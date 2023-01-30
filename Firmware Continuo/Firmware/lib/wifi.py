import network #type: ignore
import socket #type: ignore
from storage import system_has_sd_config
from ujson import load # type: ignore

class WiFi:
    def __init__(self):
        self._ENABLED = False
        self._SSID = ""
        self._PASSWORD = ""
        self._SERVER_IP = ""
        self._SERVER_PORT = 0
        self._SEND_PERIOD = 0

        config_file = "/sd/config.json" if system_has_sd_config() else "config.json"
        try:
            with open(config_file,"r") as f:
                json_config = load(f)
                WIFI = json_config['COMUNICATION']['WIFI']
                self._ENABLED = True if WIFI['ENABLED'].lower() == "true" else False
                self._SSID = WIFI['LAN_SSID']
                self._PASSWORD = WIFI['LAN_PASSWORD']
                self._SERVER_IP = WIFI['SERVER_IP']
                self._SERVER_PORT = WIFI['SERVER_PORT']
                self._SEND_PERIOD = WIFI['SEND_PERIOD_S']
        except:
            print(f"ERROR {config_file} [WIFI]")

        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # type: ignore
        self._sta_if = network.WLAN(network.STA_IF)
        if self._ENABLED: self.connect()

    def connect(self)->None:
        if not self._sta_if.active(): self._sta_if.active(True)
        self._sta_if.connect(self._SSID,self._PASSWORD)
        if self._sta_if.isconnected():
            print(self._sta_if.ifconfig())
            self._s.connect((self._SERVER_IP, self._SERVER_PORT))
        else:
            print(f"Error al conectar a {self._SSID} con la contraseña {self._PASSWORD}")
    
    def disconnect(self)->None:
        self._sta_if.active(False)
        pass

        
    def send(self,to_send)->None:
        if not self._sta_if.isconnected(): 
            self.connect()
        else:
            print(self._sta_if.ifconfig())
        try:
            self._s.send(bytearray(to_send.encode('UTF-8')))
            print(f"Mensaje enviado a {self._SERVER_IP}:{self._SERVER_PORT}")
        except OSError:
            try:
                self._s.connect((self._SERVER_IP, self._SERVER_PORT))
                self._s.send(bytearray(to_send.encode('UTF-8')))
                print(f"Mensaje enviado a {self._SERVER_IP}:{self._SERVER_PORT}")
            except:
                print(f"No se pudo conectar a {self._SERVER_IP}:{self._SERVER_PORT}")
        except:
            print(f"Error enviando a {self._SERVER_IP}:{self._SERVER_PORT}")
        return
    
    def read(self)-> bytes:
        try:
            return self._s.recv(512)
        except:
            print("Sin Respuesta")
            return b''
    
    def is_enabled(self)->bool:
        return self._ENABLED
    
    def get_period(self)->int:
        return self._SEND_PERIOD