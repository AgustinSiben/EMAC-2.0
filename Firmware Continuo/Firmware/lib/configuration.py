from ujson import load # type: ignore
from storage import system_has_sd_config

class Cfg:
    def __init__(self)->None:
        self._name = "XXXX"
        self._channels_cfg = [b'\x01',b'\x01',b'\x01',b'\x01',b'\x01',b'\x01',b'\x01',b'\x01',b'\x01',b'\x01',b'\x01',b'\x01'] #start at 1 (RAW value)
        self._status = {'NMEA': '$STS','SD':'NA','GPS': 'NA', 'NA_0':'NA','NA_1': 'NA', 'record': 'NA', 'counter': 0,'SONAR': 'NA','file_name':''}
        self._file_number = 0
        self._recording = False

        config_file = "/sd/config.json" if system_has_sd_config() else "config.json"
        try:
            with open(config_file,"r") as f:
                json_config = load(f)
                CONFIGURATION = json_config['CONFIGURATION']
                self._name = CONFIGURATION["name"]
                self._channels_cfg = [i.to_bytes(1,'little') for i in CONFIGURATION["channels_cfg"]]
        except:
            print(f"ERROR {config_file} [CONFIGURATION]")
    
    def get_cfg_dict(self)->dict:
        return {'NAME': self._name, "CHANNELS_CFG": self._channels_cfg, "STATUS": self._status, "RECORDING": self._recording}

    def set_name(self,name)->None:
        self._name = name
        return
    
    def get_name(self)->str:
        return self._name
    
    def set_channels_cfg(self,cfg)->None:
        self._channels_cfg = cfg
        return
    
    def get_channels_cfg(self)->list:
        return self._channels_cfg
    
    def set_status(self,status)->None:
        self._status = status
        return
    
    def set_status_key(self,key,value)->None:
        if key in self._status: self._status[key] = value
        return
    
    def get_status(self)->dict:
        return self._status

    def set_recording(self, recording)->None:
        self._recording = recording
        status = "OK" if recording else "NA"
        self.set_status_key("record",status)
        return
    
    def get_recording(self)->bool:
        return self._recording
    
    def update_status(self, sd_status, sample_counter, gps_warning,file_name)->None:
        self._status["GPS"] = "OK" if gps_warning == "A" else "NA"
        self._status["record"] = "OK" if self._recording else "NA"
        self._status["SD"] = "OK" if sd_status else "NA"
        self._status["counter"] = str(sample_counter)
        self._status["file_name"] = file_name
        return

    #b'CONFIG,1000,/sd/Sensores,4.9,SHNU,12,65,2,2,2,2,2,2,2,2,2,2,true,120,,,,40001,EXTERNAL'
    @staticmethod
    def from_bytes_to_dict(cfg)->dict:
        cfg = cfg.decode('UTF-8')
        cfg = cfg.split(',')
        if len(cfg) != 24: raise ValueError('$CONFIG length is not correct')
        cfg_dict, emac, configuration, comunication, wifi, gps = {}, {}, {}, {}, {}, {}
        #EMAC cfg
        emac['SAMPLE_RATE_ms'] = int(cfg[1])
        emac['TABLES_PATH'] = cfg[2]
        emac['ADC_Vref'] = float(cfg[3])
        #Chanels and name cfg
        configuration['name'] = cfg[4]
        channels_cfg = []
        for i in range(12):
            channels_cfg.append(int(cfg[i+5]))
        configuration['channels_cfg'] = channels_cfg
        #wifi cfg
        wifi['ENABLED'] = cfg[17]
        wifi['SEND_PERIOD_S'] = int(cfg[18])
        wifi['LAN_SSID'] = cfg[19]
        wifi['LAN_PASSWORD'] = cfg[20]
        wifi['SERVER_IP'] = cfg[21]
        wifi['SERVER_PORT'] = int(cfg[22])
        #gps conection
        gps['CONNECTION'] = cfg[23]
        #make directory
        cfg_dict['EMAC'] = emac
        cfg_dict['CONFIGURATION'] = configuration
        comunication['WIFI'] = wifi
        comunication['GPS'] = gps
        cfg_dict['COMUNICATION'] = comunication
        return cfg_dict
