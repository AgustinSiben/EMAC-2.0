from machine import Pin, UART  # type: ignore
import uasyncio as asyncio  # type: ignore
import network  # type: ignore
import socket  # type: ignore
from time import ticks_ms, ticks_diff  # type: ignore
from lib.emac import data_logger
import storage
from lib.configuration import get_from_file, set_in_file

modem_connecting = False
communication_using = 'MODEM'  # "WIFI" Or "MODEM"

# ------------------------------ Serial ------------------------------


async def check_communications(period_ms: int = 1000):
    global serial_cable_last, uart_0, modem_connecting
    uart_0 = create_serial_uart()
    while True:
        await asyncio.sleep_ms(period_ms)
        if modem_connecting:
            continue
        serial_cable_connected = check_serial_cable()
        data_logger._serial_connected = serial_cable_connected
        data_logger.power_sensors(serial_cable_connected)

        bytes_in = uart_0.read()
        if bytes_in != b'' and bytes_in is not None:
            serial_cable_last = ticks_ms()
            # Si llega la config por el mercury siempre borro los datos
            # Lo fuerzo con data_logger._config._configured = False
            if b'CE' in bytes_in:
                data_logger._config._configured = False
            response = commands(bytes_in)
            if response != b'' and response is not None:
                uart_0.write(response)
                if response == b'DG':
                    send_all_data(uart_0)


def create_serial_uart(time_out=25, baud=19200, tx_pin=0, rx_pin=1) -> UART:
    return UART(0,
                baudrate=baud,
                timeout=time_out,  # type:ignore
                tx=Pin(tx_pin),
                rx=Pin(rx_pin))


def check_serial_cable() -> bool:
    global serial_cable_last, uart_0
    if data_logger._serial_connected:
        # Check if two seconds have passed without receiving any messages, indicating disconnection
        if ticks_diff(ticks_ms(), serial_cable_last) < 2000:
            return True
    # ¿Cable is still connected?
    value = bool(Pin(1, Pin.IN).value())
    if value:
        # Update the timestamp of the last received message
        uart_0 = create_serial_uart()
        serial_cable_last = ticks_ms()
    return value


# Serial
# Tiene que ser negativo por la comparación en la funcion check_serial_cable
serial_cable_last = -10000
led_connectivity = Pin(3, Pin.OUT, value=0)  # type: ignore
uart_0 = create_serial_uart()

# ------------------------------ Modem ------------------------------
'''
modem_commands = [b'ate0\r\n',
                  b'AT+CREG=1\r\n',
                  b'AT+MIPCALL=1,"igprs.claro.com.ar","",""\r\n',
                  b'AT+MIPOPEN=1,40000,"190.124.196.178",40000,0\r\n',
                  b'AT+MIPSEND=1,"4345002900280038002C0036002E0024002200000000003D43FB0B8843FB0B78004B00027A020200000000005045485504000012"\r\n',
                  b'AT+MIPPUSH=1\r\n']
'''
modem_commands = []


async def modem_check() -> None:
    while True:
        await asyncio.sleep(2)
        # If not configured to use MODEM not connect
        if communication_using != 'MODEM':
            continue
        if data_logger._modem_ready:
            # data_logger.low_freq(False)
            await connect_and_send()
            if data_logger._to_send_data == 0:
                # Restart flag
                data_logger._to_send_data = data_logger._config._send_data
            # data_logger.low_freq(True)


def create_modem_uart(time_out=5, baud=19200, tx_pin=16, rx_pin=17) -> UART:
    return UART(0,
                baudrate=19200,
                timeout=5,  # type:ignore
                tx=Pin(16),
                rx=Pin(17),
                parity=None,
                stop=1)


def modem_disconnect():
    global uart_0, modem_connecting
    Pin(16, Pin.IN)
    Pin(17, Pin.IN)
    uart_0 = create_serial_uart()
    data_logger.power_connectivity(False)
    data_logger._modem_ready = False
    modem_connecting = False
    led_connectivity.off()
    print("Conectivity disconected")


def modem_start():
    global uart_0, modem_connecting
    modem_connecting = True
    uart_0 = create_modem_uart()
    data_logger.power_connectivity(True)


async def connect_and_send():
    # Puerto serie no conectado
    if check_serial_cable():
        modem_disconnect()
        print("To connect using the modem the serial cable must be disconnected")
        return

    # Prendo el modem y creo el uart para la comunicación
    modem_start()
    await asyncio.sleep(50)

    # Puerto serie no conectado
    if check_serial_cable():
        modem_disconnect()
        print("To connect using the modem the serial cable must be disconnected")
        return

    # Obtengo el IP
    if not await get_ip():
        modem_disconnect()
        return
    print("IP ASIGNADO")

    await asyncio.sleep(10)
    # Conecto al servidor
    if not await server_connect():
        modem_disconnect()
        return
    led_connectivity.on()
    print("MODEM CONECTADO")
    # Envio configuración al servidor y espero los comandos
    await modem_send_and_read()
    modem_disconnect()
    return


async def get_ip():
    global uart_0, modem_commands
    print(modem_commands)
    i = 0
    start_time = ticks_ms()
    print("Modem IP request")
    # Envio los comandos hasta pedir el IP
    while not b'AT+MIPOPEN' in modem_commands[i]:
        uart_0.write(modem_commands[i])
        print(modem_commands[i])
        i += 1
        await asyncio.sleep_ms(100)

    # Espero hasta que me asignen un IP
    bytes_in = uart_0.read()
    while True:
        if ticks_diff(ticks_ms(), start_time) > 10000:
            return False  # Tiempo de espera agotado
        if bytes_in != None and bytes_in != b'':
            if b'MIPCALL:' in bytes_in:
                print("IP: ", bytes_in)
                return True
            else:
                print(bytes_in)
        await asyncio.sleep_ms(200)
        bytes_in = uart_0.read()


async def server_connect():
    global uart_0, modem_commands
    start_time = ticks_ms()
    connect_command = b'AT+MIPOPEN=1,0,"",0,0'
    for command in modem_commands:
        if b'AT+MIPOPEN=1' in command:
            connect_command = command
            break
    print("Conectando al servidor")
    uart_0.write(connect_command)
    print(connect_command)
    # Espero la conexión con el servidor
    bytes_in = uart_0.read()
    while True:
        if ticks_diff(ticks_ms(), start_time) > 10000:
            return False  # Tiempo de espera agotado
        if bytes_in != None and bytes_in != b'':
            print(bytes_in)
            if b'4F4B' in bytes_in:
                return True
        bytes_in = uart_0.read()


async def modem_send_and_read():
    global uart_0
    start_time = ticks_ms()
    data = command_X()
    await modem_send_bytes(uart_0, data)
    while ticks_diff(ticks_ms(), start_time) < 30000:
        await asyncio.sleep_ms(100)
        bytes_in = uart_0.read()
        if bytes_in != b'' and bytes_in is not None:
            if b'MIPRTCP' in bytes_in:
                bytes_in = get_modem_message(bytes_in)
                print('Llega al modem: ', bytes_in)
                response = commands(bytes_in)
                if response != b'' and response is not None:
                    await modem_send_bytes(uart_0, response)
                    if response == b'DG':
                        await asyncio.sleep_ms(500)
                        await send_all_data_modem(uart_0, True)


async def send_all_data_modem(called_by, clear_memory=False):
    print("Sending data")
    try:
        # Envio 4 bytes que contienen la cantidad de bytes almacenados
        space = storage.space_of_data()
        space = int.to_bytes(space, 4, 'little')
        await modem_send_bytes(called_by, space)
        with open('/data.bin', 'rb') as f:
            bytes_1024 = f.read(1024)
            while bytes_1024:
                await asyncio.sleep_ms(100)
                await modem_send_bytes(called_by, bytes_1024)
                bytes_1024 = f.read(1024)

        if clear_memory:
            storage.delete_file_contents('/data.bin')

    except:
        print("Error enviando datos")


async def modem_send_bytes(called_by: UART, bytes_to_send: bytes) -> None:
    str_to_send = bytes_to_hex_string(bytes_to_send)
    called_by.write(f'AT+MIPSEND=1,"{str_to_send}"\r\n'.encode())
    print(f'AT+MIPSEND=1,"{str_to_send}"\r\n')
    await asyncio.sleep_ms(500)
    called_by.write(b'AT+MIPPUSH=1\r\n')


def get_modem_message(message: bytes) -> bytes:
    message = message.split(b',')[-1]
    message = message.replace(b'\r\n', b'')
    message_str = message.decode()
    return hex_string_to_bytes(message_str)


def bytes_to_hex_string(bytes_in) -> str:
    bytes_in = "".join("\\x%02x" % i for i in bytes_in)
    bytes_in = bytes_in.upper()
    bytes_in = bytes_in.replace('\X', '')  # type: ignore
    return bytes_in


def hex_string_to_bytes(hex_string: str) -> bytes:
    # Remove backslashes and "x" from the format
    hex_string = hex_string.replace("\\x", "")
    hex_string = hex_string.lower()  # Convert to lowercase to ensure correct format
    try:
        # Convert the hexadecimal string to bytes
        byte_array = bytes.fromhex(hex_string)
        return byte_array
    except ValueError:
        raise ValueError("Invalid hexadecimal string")


# ------------------------------ Wifi ------------------------------


async def connect_socket() -> None:
    while True:
        await asyncio.sleep(2)
        # If not configured to use WIFI not connect
        if communication_using != 'WIFI':
            continue
        if data_logger._to_send_data == 0:
            # data_logger.low_freq(False)
            await asyncio.gather(asyncio.create_task(wifi_listen_socket()),
                                 asyncio.create_task(disconnect(timeout=30)))
            # data_logger.low_freq(True)


# WIFI
ssid = "BVNET-4CB24CB2"
password = "H7KFYX77TYMRNV44"
ip_port = ("192.168.0.2", 8000)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # type: ignore
sta_if = network.WLAN(network.STA_IF)


async def wifi_connect() -> None:
    print("CONECTANDO")
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.active():
        sta_if.active(True)
    sta_if.connect(ssid, password)
    i = 0
    while not sta_if.isconnected() and i < 60:
        i += 1
        led_connectivity.toggle()
        await asyncio.sleep_ms(100)
    if sta_if.isconnected():
        print(sta_if.ifconfig())
        led_connectivity.on()
    else:
        print(f"Error al conectar a {ssid} con la contraseña {password}")
        led_connectivity.off()
    return


async def disconnect(timeout: int = 0) -> None:
    await asyncio.sleep(timeout)
    s.close()
    sta_if.disconnect()
    sta_if.active(False)
    sta_if.deinit()
    led_connectivity.off()
    pass


async def write(to_send: bytes) -> bool:
    if not sta_if.isconnected():
        await wifi_connect()
    else:
        print(sta_if.ifconfig())
    try:
        print("SEND: ", to_send)
        for i in to_send:
            s.send(i)  # type: ignore
        print(f"Mensaje enviado a {ip_port[0]}:{ip_port[1]}")
    except:
        print(f"Error enviando a {ip_port[0]}:{ip_port[1]}")
        return False
    return True


async def wifi_listen_socket():
    if not sta_if.isconnected():
        await wifi_connect()
    print("Conectando socket")
    ip = ip_port[0]
    port = ip_port[1]
    try:
        reader, writer = await asyncio.open_connection(ip, port)

        # Send data to server
        data = command_X()
        writer.write(data)
        print(data)

        # Listen socket until wifi is disconected
        while True:
            led_connectivity.on()
            bytes_in = await reader.read(1024)
            if bytes_in != b'' and bytes_in is not None:
                response = commands(bytes_in)
                if response != b'' and response is not None:
                    writer.write(response)
                    # El equipo pide los datos
                    if response == b'DG':
                        await asyncio.sleep_ms(500)
                        send_all_data(writer, clear_memory=True)

    except:
        print(f"Esperando conexión por WiFi para abrir el socket nuevamente")
        led_connectivity.off()

    # Esta acá porque si falla la conexión tiene que volver al valor máximo, si lo pongo arriba
    # y falla no lo cambia
    if data_logger._to_send_data == 0:
        # Restart flag
        data_logger._to_send_data = data_logger._config._send_data


async def request_configuration(delay: int = 0):
    while True:
        await asyncio.sleep(delay)
        if not data_logger._config._configured:
            print("Configuration request")
            data_logger._to_send_data = 0
            data_logger._modem_ready = True
        else:
            return


# ------------------------------ Commands ------------------------------


def commands(bytes_in=b'') -> bytes:
    if len(bytes_in) == 26:
        return config_in(bytes_in)
    if b'CE' in bytes_in:
        if len(bytes_in) == 28:
            return config_in(bytes_in[2:])
        return b'OK'
    if b'LD' in bytes_in:
        return b'DG'  # Send data
    if b'GA' in bytes_in:
        return command_GA(bytes_in)
    if b'TX' in bytes_in:
        bytes_in = bytes_in.split(b'TX')[1]
        command_TX(bytes_in[:2])
    if b'X' in bytes_in:
        return command_X()
    return b''


def command_X() -> bytes:
    data = data_logger.make_data()
    data.insert(0, b'E')
    data.insert(0, b'C')
    data = b''.join(data)
    return data


def config_in(bytes_in) -> bytes:
    if bytes_in != None:
        data_logger._config.set(bytes_in)
        data_logger.update_parameters()
        if not data_logger._config._configured:
            storage.delete_file_contents('/data.bin')
            data_logger._config._configured = True
    return b''


def command_TX(send_period) -> None:
    if len(send_period) != 2:
        print("Error updating connection period", send_period)
        return
    send_period = int.from_bytes(send_period, 'big') + 1
    data_logger.set_send_period(send_period)
    set_in_file('periodes_to_send', str(send_period))


def command_GA(config) -> bytes:
    global ssid, password, ip_port, modem_commands, communication_using
    print("Nueva configuración de internet")
    set_in_file('wireless_config', config.decode())
    # Remove GA command
    config = config.split(b'GA')[-1]
    modem_commands, send_period = config.split(b';')

    # Period is the first 2 bytes after the b';'
    send_period = send_period[0:2]
    command_TX(send_period)

    # Internet parameters
    modem_commands = modem_commands.replace(b'/', b'')
    modem_commands = modem_commands.split(b'\r')[0:-1]  # Remove last '\'
    modem_commands = [command + b'\r\n' for command in modem_commands]

    # Check whether the connection is established using wifi or via modem
    mode = ''
    for command in modem_commands:
        if b'MIPCALL' in command:
            command = command.replace(b'\r\n', b'')
            splitted = bytes.decode(command, 'utf-8').split(',')
            ssid = splitted[1].replace('"', '')
            mode = splitted[2].replace('"', '')
            password = splitted[3].replace('"', '')
            set_in_file('ssid', ssid)
            set_in_file('password', password)
        if b'MIPOPEN' in command:
            splitted = bytes.decode(command, 'utf-8').split(',')
            port = int(splitted[1])
            ip = splitted[2].replace('"', '')
            set_in_file('ip_port', f'{ip} {port}')
            ip_port = (ip, port)

    # Save connection commands
    save_modem_commands = b"".join(modem_commands)
    save_modem_commands = save_modem_commands.replace(b'\r\n', b" ")
    set_in_file('wireless_config', save_modem_commands.decode())

    # WIFI system or MODEM system
    if mode.upper() == 'WIFI':
        communication_using = 'WIFI'
        print("Configured to use WIFI")
    else:
        communication_using = 'MODEM'
        print("Configured to use MODEM")
    set_in_file('communication_using', communication_using)
    return b''


def send_all_data(called_by, clear_memory=False):
    try:
        # Envio 4 bytes que contienen la cantidad de bytes almacenados
        space = storage.space_of_data()
        space = int.to_bytes(space, 4, 'little')
        called_by.write(space)
        with open('/data.bin', 'rb') as f:
            bytes_1024 = f.read(1024)
            while bytes_1024:
                called_by.write(bytes_1024)
                bytes_1024 = f.read(1024)

        if clear_memory:
            storage.delete_file_contents('/data.bin')
    except:
        print("Error enviando datos")


def get_wireless_config():
    global modem_commands, ip_port, ssid, password, communication_using
    wireless = get_from_file('wireless_config')
    modem_commands = []
    for command in wireless:
        modem_commands.append(command.encode() + b'\r\n')
    socket_conn = get_from_file('ip_port')
    ip_port = (socket_conn[0], int(socket_conn[1]))
    ssid_password = get_from_file('ssid_password')
    ssid = ssid_password[0]
    password = ssid_password[1]
    communication_using = get_from_file('communication_using')


get_wireless_config()
