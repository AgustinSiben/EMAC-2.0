from storage import space_of_data
from rtc_plus import Rtc_Plus
import ubinascii


class Cfg:
    def __init__(self) -> None:
        self._configured = False
        self._name = [b'X', b'X', b'X', b'X']
        self._ini_sample = [b'\x00', b'\x00', b'\x00', b'\x00']
        # Por defecto 2 minutos [b'x',b'\x02'] para 10 minutos
        self._t_sample = [b'x', b'\x00']
        self._t_regre = [b'\x00', b'\x00']
        self._channels_cfg = [b'\x01', b'\x01', b'\x01', b'\x01', b'\x01',
                              b'\x01', b'\x01', b'\x01', b'\x01', b'\x00']  # start at 1 (RAW value)
        self._send_data = -1  # Cycles to send data
        self._rtc = Rtc_Plus()
        self.read_config_in_file()

    def get(self) -> list:
        hour = self._rtc.get_julian_time().to_bytes(4, 'little')
        all_cfg = []
        for i in hour:
            all_cfg.append(i.to_bytes(1, 'little'))
        for i in self._ini_sample:
            all_cfg.append(i)
        for i in self._t_sample:
            all_cfg.append(i)
        for i in self._t_regre:
            all_cfg.append(i)
        for i in self._channels_cfg:
            all_cfg.append(i)
        for i in self._name:
            all_cfg.append(i)  # .to_bytes(1,'little'))
        busy_memory = bytearray(
            space_of_data().to_bytes(3, 'little'))  # type: ignore
        for i in busy_memory:
            all_cfg.append(i.to_bytes(1, 'little'))
        all_cfg.append(b'\x12')  # --- 12 = 18hexa #¿Que es?
        return all_cfg

    def set(self, cfg) -> None:
        if len(cfg) != 26:
            print('Error reading configuration')
            return
        self._rtc.set_time(int.from_bytes(
            cfg[0:4], 'little') + self._rtc._JULIAN_ZERO)
        self._ini_sample = [i.to_bytes(1, 'little') for i in cfg[4:8]]
        self._t_sample = [i.to_bytes(1, 'little') for i in cfg[8:10]]
        self._t_regre = [i.to_bytes(1, 'little') for i in cfg[10:12]]
        self._channels_cfg = [i.to_bytes(1, 'little') for i in cfg[12:22]]
        self._name = [i.to_bytes(1, 'little') for i in cfg[22:]]
        cfg = ubinascii.hexlify(cfg).decode('utf-8')
        set_in_file('config', cfg)
        print("Equipo configurado correctamente")

    def get_channels_cfg(self) -> list:
        cfg = self._channels_cfg
        cfg = [int.from_bytes(x, 'little') for x in self._channels_cfg]
        return cfg

    def read_config_in_file(self):
        try:
            cfg = get_from_file('config')
            cfg = ubinascii.unhexlify(bytearray(cfg, 'utf-8'))
            self.set(cfg)
        except:
            print("Error in config.txt file")
        # Returns false because the set() function sets it to true but it has to ask for the time
        self._configured = False
        # Restart the rtc to lose the past time of the file
        self._rtc = Rtc_Plus()


def get_from_file(parameter: str) -> str:
    with open('/config.txt', 'r') as f:
        for line in f.readlines():
            values = line.strip('\r\n ').split(' ')
            if values[0] == parameter:
                if len(values) == 2:
                    return values[1]
                return values[1:]
        raise ValueError(f'{parameter} not found in configuration file')


def set_in_file(parameter: str, value: str):
    modified_lines = []
    with open('/config.txt', 'r') as f:
        for line in f:
            values = line.strip('\r\n ').split(' ')
            if values[0] == parameter:
                new_line = f"{parameter} {value}\n"
                modified_lines.append(new_line)
            else:
                modified_lines.append(line)
    with open('/config.txt', 'w') as f:
        for line in modified_lines:
            f.write(line)


def print_config():
    with open('/config.txt', 'r') as f:
        print(f.read())
