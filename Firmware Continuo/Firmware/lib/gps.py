from machine import Pin, UART
from ujson import load # type: ignore
from storage import system_has_sd_config
import nmea

class Gps:
    def __init__(self)->None:
        self._time_out = 50
        self._baudrate = 9600
        self._uart = UART(1, baudrate=self._baudrate, timeout=self._time_out, tx=Pin(8), rx=Pin(9))  # type: ignore
        self._last = {}
        config_file = "/sd/config.json" if system_has_sd_config() else "config.json"
        try:
            with open(config_file,"r") as f:
                json_config = load(f)
                GPS = json_config['COMUNICATION']['GPS']
                if GPS['CONNECTION'].lower() == "external":
                    self._uart = UART(1, baudrate=self._baudrate, timeout=self._time_out, tx=Pin(4), rx=Pin(5)) # type: ignore
        except:
            print(f"ERROR {config_file} [GPS]")
    
    def set_last(self, last)->None:
        self._last = last
        return
    
    def get_last(self,clear=False)->dict:
        if not clear: return self._last
        last = self._last
        self._last = {}
        return last

    def read(self)->dict | None:
        arrival = self._uart.read()
        if arrival != None:
            try:
                return nmea.to_dict(arrival.decode('ascii'))
            except:
                return {}