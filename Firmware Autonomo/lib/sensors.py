from MCP3208 import MCP3208
from machine import Pin, ADC, SPI  # type: ignore
from lib.configuration import get_from_file


class Channels:
    def __init__(self) -> None:
        self._ch7_last_counter = 0
        self._ch7_current_counter = 0

        self._ch8_last_counter = 0
        self._ch8_current_counter = 0

        self._voltage_reference = 1
        try:
            mvr = float(get_from_file('mercurry_v_ref'))
            evr = float(get_from_file('emac_vref'))
            self._voltage_reference = evr/mvr
        except:
            self._voltage_reference = 1

    def digital_values(self) -> list:
        # Le cambié el sentido por el mercury
        return [self._ch8_last_counter, self._ch7_last_counter]

    def ch7_add(self) -> None:
        self._ch7_current_counter += 1

    def ch8_add(self) -> None:
        self._ch8_current_counter += 1

    def digital_update(self) -> None:  # Save count and restart counter
        self._ch7_last_counter = self._ch7_current_counter
        self._ch7_current_counter = 0
        self._ch8_last_counter = self._ch8_current_counter
        self._ch8_current_counter = 0

    # Pico analog inputs
    # CH0,CH1,CH2, CPU_TEMP = 26, 27, 28, 4
    @staticmethod
    def battery_lvl() -> int:
        lvl = ADC(28).read_u16()
        Pin(27, Pin.IN, Pin.PULL_UP)  # reinit Pin 28 used by ADC
        return lvl

    @staticmethod
    def battery_lvl_in_v() -> float:
        lvl = ADC(28).read_u16()*0.00055389404  # *(3.3/65536 )*11
        Pin(27, Pin.IN, Pin.PULL_UP)  # reinit Pin 27 used by ADC
        return lvl

    @staticmethod
    def cpu_temp() -> int:
        return ADC(4).read_u16()

    @staticmethod
    def cpu_temp_in_c() -> float:
        voltage = ADC(4).read_u16()*0.000050354  # *3.3/65536
        return 27 - (voltage - 0.706)/0.001721

    # MCP3208 analog inputs
    # return [CHA0-...-CHA7-CHD7-CHD8]
    def get_data(self) -> list:
        data = self.read_all_adc()
        data = self.bits12_to_bits10(data)
        for dv in self.digital_values():  # [CH7,CH8]
            two_bytes = self.Bits16tobytes2(dv)
            data.append(two_bytes[1])  # LOW
            data.append(two_bytes[0])  # HIGH
        # data.append(battery_lvl()) Todavía no lo integramos
        # data.append(cpu_temp()) Todavía no lo integramos
        # gps_data = gps.read() Todavía no lo integramos
        return data

    @staticmethod
    def read_adc(pin, is_differential=False) -> int:
        spi_adc = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(20))
        adc = MCP3208(spi_adc, Pin(21, Pin.OUT), ref_voltage=4.894)
        return adc.read(pin, is_differential)  # type: ignore

    @staticmethod
    def read_all_adc() -> list:
        spi_adc = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(20))
        adc = MCP3208(spi_adc, Pin(21, Pin.OUT), ref_voltage=4.894)
        return adc.read_all()

    # Data management
    @staticmethod
    def Bits16tobytes2(bits) -> list:
        By1 = bits >> 8  # Valores mas significativos
        By2 = bits % 256  # Valores menos significativos
        return [By1, By2]

    def bits12_to_bits10(self, values):
        values10bits = []
        for i in range(0, len(values), 2):
            integer = int((values[i+1] + values[i]*256)/4)
            integer = int(integer*self._voltage_reference)
            Bits1 = integer >> 8  # Valores mayores
            Bits2 = integer % 256  # Valores menores
            values10bits.append(Bits2)
            values10bits.append(Bits1)
        return values10bits
