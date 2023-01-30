from machine import Pin  # type: ignore
from time import ticks_ms, ticks_diff # type: ignore
from ujson import load, dump # type: ignore
from configuration import Cfg
from gps import Gps
from bluetooth import Bluetooth
from wifi import WiFi
from channels import Channels
import storage
import from_raw_to_str

class emac20:
    def __init__(self)->None:
        self._SAMPLE_RATE_ms = 1000
        self._WIFI_DT = 120
        self._ADC_Vref = 5
        self._TABLES_PATH = "/tables"
        self._line = 0
        self._last_sample = ticks_ms()
        self._sd = storage.SD()
        self._cfg = Cfg()
        self._cfg.set_status_key("SD","OK" if self._sd.get_status() else "NA")
        print('SD Init ',self._sd.get_status())
        
        config_file = "/sd/config.json" if storage.system_has_sd_config() else "config.json"
        try:
            with open(config_file,"r") as f:
                json_config = load(f)
                EMAC = json_config['EMAC']
                self._TABLES_PATH = EMAC['TABLES_PATH']
                self._SAMPLE_RATE_ms = EMAC['SAMPLE_RATE_ms']
                self._ADC_Vref = EMAC['ADC_Vref']
            print(f"Config for EMAC read from: {config_file}")
        except:
            print(f"ERROR {config_file} [EMAC]")

        #Pins
        self._power_sensors = Pin(6,Pin.OUT, value = 1) # type: ignore
        self._power_connectivity = Pin(7,Pin.OUT, value = 1) # type: ignore
        self._led_activity = Pin(15, Pin.OUT, value = 0) # type: ignore
        #self._led_gps_activity = Pin(3, Pin.OUT, value = 0) #No usar en PCB V1

        #self._pwm = PWM(Pin(14))
        #self._pwm.freq(frequency)
        #self._pwm.duty_u16(duty)
        #

        self._channels = Channels(table_path=self._TABLES_PATH,adc_vref=self._ADC_Vref)
        self._channels.optimize_tables(self._cfg.get_channels_cfg()) #Remove unused tables

        #Comunication
        self._gps = Gps()
        self._bluetooth = Bluetooth(name=self._cfg.get_name())
        self._wifi = WiFi()
        from_raw_to_str.rtc.set_time_offset(from_raw_to_str.rtc.get_julian_time()) #Set start time
    
    def add_line(self)->None:
        self._line += 1
        return
    
    def get_line(self)->int:
        return self._line

    def sample(self)->None:
        self.check_gps() #Check if uart buffes has something
        self.check_bluetooth()
        if ticks_diff(ticks_ms(),self._last_sample) < self._SAMPLE_RATE_ms: return
        self._last_sample=ticks_ms()
        if not self._sd.get_status(): self._sd = storage.SD()
        self._led_activity.toggle()
        data = from_raw_to_str.data_to_string(self.get_line(),self._cfg.get_name(),self._channels.get_data(cfg=self._cfg.get_channels_cfg()),self._gps.get_last(clear=True))
        self.send_samples(data)
        self.add_line()
        print(data)
        return
    
    def check_gps(self)->None:
        gps_arrival = self._gps.read()
        if not gps_arrival: return
        self._gps.set_last(gps_arrival) # If something has arrive save it
        self._cfg.set_status_key("GPS","NA" if gps_arrival['warning'] != "A" else "OK")
        self._led_activity.toggle()
        return
    
    def check_bluetooth(self)->None:
        all_bt_arrival = self._bluetooth.read()
        if all_bt_arrival == None: return
        all_bt_arrival = set(all_bt_arrival.split(b'$')) #Split arrivals and remove duplicates # type: ignore
        all_bt_arrival = list(filter(lambda i: i != b'',all_bt_arrival)) #remove b'' values
        print(all_bt_arrival)
        for bt_arrival in all_bt_arrival:
            if bt_arrival == b'REC':
                self._bluetooth.write('$REC')
                self._cfg.set_recording(True)
                self._line = 0
                return
            if bt_arrival == b'STOP':
                self._bluetooth.write('$STOP')
                self._cfg.set_recording(False)
                return
            if bt_arrival == b'UNITS':
                print("Sending Units to the application")
                self._bluetooth.write(from_raw_to_str.make_units(self._channels.get_all_units(self._cfg.get_channels_cfg()))) #send units
                return
            if bt_arrival == b'CONFIG':
                print("Sending configuration to the application")
                config_file = "/sd/config.json" if storage.system_has_sd_config() else "config.json"
                try:
                    with open(config_file,"r") as f:
                        self._bluetooth.write(from_raw_to_str.make_config(load(f)))
                except:
                    print('Error reading config file. Bluetooth $CONFIG')
                return
            if b'CONFIG' in bt_arrival:
                try:
                    config_dict = self._cfg.from_bytes_to_dict(bt_arrival)
                    with open('config.json','w') as f:
                        dump(config_dict,f)#,indent=4) # type: ignore
                    try: #SD remove
                        with open('/sd/config.json','w') as f:
                            dump(config_dict,f) # type: ignore
                    except:
                        print("Could not save config.json to sd")
                    self._bluetooth.write('$ALERT,El equipo se configuró correctamente. Reinicie EMAC continuo para aplicar los cambios')
                    print('El equipo se configuró correctamente. Reinicie EMAC continuo para aplicar los cambios')
                except:
                    self._bluetooth.write('$ALERT,ERROR: El equipo NO se configuró')
                    print('ERROR: El equipo NO se configuró')
        

    def send_samples(self,data)->None:
        if self._cfg.get_recording():
            self.save_data(data + "\n")
            print("Guardando:")
            if self.get_line() % self._wifi.get_period() == 0 and self._wifi.is_enabled(): #send to server only recording data
                self._wifi.send(data)
        bt_data = data.replace(",,",",-9999,")
        bt_data = bt_data.replace(",,",",-9999,") #needs to be done twice
        self._bluetooth.write(from_raw_to_str.make_status(self._cfg.get_status())) #Send status
        self._bluetooth.write(f"$DATA,{bt_data}") #Send data
        return

    def save_data(self,data)->None:
        file_number = str(int(self.get_line()/86400) + self._sd.get_file_offset())  #one file per day
        while(len(file_number)<3): file_number = '0' + file_number  # type: ignore
        file_name = f"EMAC-DATA-{file_number}.txt"
        self._cfg.set_status_key("file_name",file_name)
        try:
            storage.append_to(data,f"sd/datos/{file_name}")
            self._cfg.set_status_key("counter",self.get_line())
            Pin("LED", Pin.OUT, value = 0) # type: ignore
        except Exception as error:
            print(f"SD ERROR: Can't write SD {error}")
            self._bluetooth.send_error(error)
            Pin("LED", Pin.OUT, value = 1) # type: ignore
            self._sd.__init__() #Try to reinit SD card
        return