from machine import Pin, UART # type: ignore
from storage import system_has_sd_config
from ujson import load # type: ignore

class Bluetooth:
    def __init__(self,name=None)-> None:
        self.time_out = 50
        self.baudrate = 9600
        self.uart = UART(0, baudrate=self.baudrate, timeout=self.time_out, tx=Pin(16), rx=Pin(17))  # type: ignore
        if name != None :
            self.write(f"AT+BAUD{self.baudrate}\r\n")
            self.write(f"AT+NAME{name}\r\n")
            print(f"Bluetooth module name: {name}")
    
    def read(self)->bytes | None:
        return self.uart.read()

    def write(self,msg)->None:
        self.uart.write(msg)
        return

    def send_and_wait(self,msg)->bytes | None: #Write and return read()
        self.write(msg)
        txt = self.read()
        return txt
    
    def send_error(self,msg)->None:
        self.write(f"$ERROR,{msg}")
        return