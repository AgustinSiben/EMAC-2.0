from machine import Pin, freq  # type: ignore
from time import ticks_ms, ticks_diff  # type: ignore
from lib.sensors import Channels
from lib.configuration import Cfg, get_from_file
import storage
import os


class emac20:
    def __init__(self) -> None:
        # Constants
        self._INIT_POWE_ON = 550
        self._MODEM_POWER_ON = 450

        # Variables
        self._state = 0
        self._end_of_cycle = 1200
        self._to_send_data = -1  # Actual step
        self._modem_ready = False
        self._serial_connected = False
        self._channels = Channels()
        self._gps_values = {}
        self._sonar_values = {}
        self._config = Cfg()

        # Pins
        # self.pwm = PWM(Pin(14))
        # self.pwm.freq(frequency)
        # self.pwm.duty_u16(duty)
        try:
            T = get_from_file('periodes_to_send')
            self.set_send_period(int(T))  # type: ignore
        except:
            print("Error reading periodes_to_send en config file")

        # self.low_freq(True)

    def next_state(self) -> None:
        self.state_machine()
        self._state += 1
        Pin(15, Pin.OUT).off()
        if self._state % 10 == 0:  # Cada 1 segundo
            Pin(15, Pin.OUT).on()  # Activity led to know if it is working
            sequence = ["\r|", "\r/", "\r-", "\r\\"]
            print(sequence[int((self._state % 40)/10)], end="")

    def state_machine(self) -> None:
        if (self._state < self._end_of_cycle - self._INIT_POWE_ON) and not self._serial_connected:
            self.power_sensors(False)
            # return

        if self._state >= self._end_of_cycle - self._INIT_POWE_ON or self._serial_connected:
            if self._config._configured:
                self.power_sensors(True)

        if self._state == self._end_of_cycle - self._MODEM_POWER_ON:
            if self._to_send_data <= 1:
                self._modem_ready = True

        if self._state >= self._end_of_cycle:
            if self._config._configured:
                self.take_sample()
                if self._to_send_data > 0:
                    self._to_send_data -= 1
            self.next_cycle_times()
            print("END OF CYCLE ")
            print(f"faltan {self._to_send_data} muestas hasta enviar")
            print('Ejecutado: ', self._config._rtc.get_time())

    def next_cycle_times(self):
        self._end_of_cycle += int.from_bytes(
            b''.join(self._config._t_sample), 'little') * 10

    # --------------- DATA ---------------

    def make_data(self) -> list:  # type: ignore
        data = []
        for i in self._channels.get_data():
            data.append(i)
        data = [i.to_bytes(1, 'little') for i in data]
        for i in self._config.get():
            data.append(i)
        return data

    def take_sample(self):
        data = self.make_data()
        config = self._config.get_channels_cfg()
        to_save = []
        for idx, channel in enumerate(config):
            if channel != 0:
                i = idx*2
                to_save.append(data[i])
                to_save.append(data[i+1])
        to_save = bytes(
            bytearray([int.from_bytes(i, 'little') for i in to_save]))
        with open('/data.bin', 'ab') as f:
            f.write(to_save)

    def update_parameters(self) -> None:
        self._state = (self._config._rtc.get_julian_time()*10)
        self._end_of_cycle = int.from_bytes(
            b''.join(self._config._ini_sample), 'little')*10
        # self.update_json_config()

    def set_send_period(self, period_in_cycles: int):
        t_sample_in_seconds = int.from_bytes(
            b''.join(self._config._t_sample), 'little')
        if t_sample_in_seconds == 0:
            t_sample_in_seconds = 0.5
        period_to_send = t_sample_in_seconds*period_in_cycles
        # Envio de datos no menor a 10 minutos
        if period_to_send < 600:
            period_in_cycles = int(600/t_sample_in_seconds)
        self._config._send_data = period_in_cycles
        # En 1 para que en el primer ciclo ya envie datos
        self._to_send_data = 1

    @staticmethod
    def power_sensors(value: bool):
        Pin(6, Pin.OUT).value(value)

    @staticmethod
    def power_connectivity(value: bool):
        Pin(7, Pin.OUT).value(value)

    @staticmethod
    def low_freq(value: bool):
        if value:   # 20MHz
            freq(20000000)  # type: ignore
        else:       # 120MHz
            freq(120000000)  # type: ignore


# Data logger
data_logger = emac20()
