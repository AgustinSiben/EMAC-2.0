from MCP3208 import MCP3208
from machine import Pin, ADC, SPI # type: ignore
import os

class Channels:
    def __init__(self,adc_vref=5,table_path="/sd/Sensores")-> None:
        self._ch7_last_counter = 0
        self._ch8_last_counter = 0
        self._ch7_current_counter = 0
        self._ch8_current_counter = 0
        self._Vref = adc_vref
        self._conversion_factor = self._Vref/4095
        self._tables = Tablas(table_path)
        spi_adc = SPI(0,baudrate=10000,sck=Pin(18),mosi=Pin(19),miso=Pin(20))
        self._adc = MCP3208(spi_adc,Pin(21 ,Pin.OUT))

    def digital_values(self)-> list:
        return [self._ch7_last_counter, self._ch8_last_counter]

    def ch7_add(self)->None:
        self._ch7_current_counter += 1
        return

    def ch8_add(self)->None:
        self._ch8_current_counter += 1
        return

    def digital_update(self)->None: #Save count and restart counter
        self._ch7_last_counter = self._ch7_current_counter
        self._ch7_current_counter = 0
        self._ch8_last_counter = self._ch8_current_counter
        self._ch8_current_counter = 0
        return
    
    def optimize_tables(self, used_tables)->None:
        self._tables.remove_unused_tables(used_tables)
        return

    #Pico analog inputs
    #CH0,CH1,CH2, CPU_TEMP = 26, 27, 28, 4
    @staticmethod
    def battery_lvl()-> int:
        lvl = ADC(28).read_u16()
        return lvl
    
    @staticmethod
    def battery_lvl_in_v()-> float:
        return round(ADC(28).read_u16()*0.00055389404,2)  #*(3.3/65536 )*11
    
    @staticmethod
    def cpu_temp()->int:
        return ADC(4).read_u16()

    @staticmethod
    def cpu_temp_in_c()->float:
        voltage = ADC(4).read_u16()*0.000050354  #*3.3/65536 
        return round(27 - (voltage - 0.706)/0.001721,2)


    def get_data(self,cfg=[0 for _ in range(12)])->list: #return [CHA0-...-CHA7-CHD7-CHD8-BateryLvl-CPUTemp]
        data = self.read_all_adc()
        data = self.map_analog_values(data,cfg[:8])
        digital = self.map_digital_values(self.digital_values(),cfg[8:10])
        data.append(digital[0])
        data.append(digital[1])
        battery = self.battery_lvl_in_v() if cfg[10] != b'\x00' else None
        cpu_temp = self.cpu_temp_in_c() if cfg[11] != b'\x00' else None
        data.append(battery)
        data.append(cpu_temp)
        return data

    def map_analog_values(self,values,cfg)->list:
        if len(values) != len(cfg): raise ValueError('cfg and values must have the same length')
        sensors_mapped = []
        for channel, channel_cfg in zip(values,cfg):
            if channel_cfg == b'\x00': sensors_mapped.append(None)# None Value(sensorless)
            elif channel_cfg == b'\x01': sensors_mapped.append(channel) #channel (raw value)
            else: 
                try:
                    sensors_mapped.append(self._tables.map_with_table(channel*self._conversion_factor,channel_cfg))
                except: #If there is a problem with the files, the raw value is sent
                    sensors_mapped.append(channel) #channel (raw value)
        return sensors_mapped

    def map_digital_values(self,values,cfg)->list:
        if len(values) != len(cfg): raise ValueError('cfg and values must have the same length')
        sensors_mapped = []
        for channel, channel_cfg in zip(values,cfg):
            if channel_cfg == b'\x00': sensors_mapped.append(None)# None Value(sensorless)
            elif channel_cfg == b'\x01': sensors_mapped.append(channel) #channel (raw value)
            else:
                try:
                    sensors_mapped.append(self._tables.map_with_table(channel,channel_cfg))
                except: #If there is a problem with the files, the raw value is sent
                    sensors_mapped.append(channel) #channel (raw value)
        return sensors_mapped

    def get_all_units(self,cfg)->list:
        units = []
        for channel in cfg[:-2]:
            if channel == b'\x00' or channel == b'\x01':
                units.append("")
            else:
                units.append(self._tables.get_unit(channel))
        units.append("V")
        units.append("°C")
        return units

    def read_adc(self, pin)->int:
        return self._adc.read(pin)

    def read_all_adc(self)->list:
        return self._adc.read_all()

    #Data management
    @staticmethod
    def Bits16tobytes2(bits)->list:
        By1 = bits >> 8  # Valores mayores
        By2 = bits % 256  # Valores menores
        return [By1, By2]
    
    @staticmethod
    def bytes12_to_bytes10(values):
        values10bits = []
        for i in range(0,len(values),2):
            integer = int((values[i] + values[i+1]*256)/4)
            By1 = integer >> 8  # Valores mayores
            By2 = integer % 256  # Valores menores
            values10bits.append(By2)
            values10bits.append(By1)
        return values10bits

class Tablas:
    def __init__(self,file_path)->None:
        self._file_path = file_path
        self._tables = {}
        self.update_tables_from_files()

    def update_tables_from_files(self)->None:
        try:
            files = os.listdir(self._file_path.encode('UTF-8'))
        except:
            print("NO SD")
            return
        for file in files:
            Pin(15).toggle()
            file_path = self._file_path.encode('UTF-8') + b"/" + file
            print(f"Getting ID from: {file.decode('UTF-8')}") # type: ignore
            with open(file_path,"r") as f:
                contents = f.read().split("\n")
                contents = self.file_contents_to_dictionary(contents[1:])
                id = int(contents['ID'])
                del contents['ID']
                #I check that the keys are correct
                keys_in_contents = "Salida" in contents and "X" in contents and "Y" in contents and "Modo" in contents
                keys_in_contents = keys_in_contents and "Decimales" in contents and "Unidad" in contents and "Entrada" in contents
                if not keys_in_contents: raise ValueError(f'ERROR IN {file_path} MUST HAVE "Salida","X","Y","Decimales","Unidad","Modo","Entrada"')
                #Save contents
                self._tables[id] = contents

    def map_with_table(self,value,id)->int | float | str | None:
        id = int.from_bytes(id,'little')
        if id not in self._tables: raise ValueError(f"{id} not in IDs") #if table doesn't exist raise error
        contents = self._tables[id]
        if contents["Salida"] == "NUMERO":
            return round(self.map_interpolating(contents["X"],contents["Y"],value),int(contents["Decimales"]))
        elif contents["Salida"] == "TEXTO":
            return self.map_by_proximity(contents["X"],contents["Y"],value)
        else: raise ValueError("BAD 'SALIDA' PARAMETER")
    
    def get_unit(self,id):
        id = int.from_bytes(id,'little')
        contents = self._tables[id]
        return contents["Unidad"]

    def number_of_ids(self)->int:
        return len(self._tables)

    def remove_unused_tables(self,used_tables)->None:
        used_tables = list(map(lambda x : int.from_bytes(x,'little'),used_tables))
        keys = list(self._tables.keys()) # needed because dictionary resizes during iteration
        for key in keys:
            if not key in used_tables: del self._tables[key]
        return


    @staticmethod
    def file_contents_to_dictionary(file_contents)->dict:
        contents_dict = {}
        for line in file_contents:
            if line == "" or line[0] == ";": continue # remove lines that start with ";" and remove "" in array
            line = line.replace('\r','')
            line = line.split("=")
            contents_dict[line[0]] = line[1]
        return contents_dict

    @staticmethod
    def map_interpolating(x,y,point)->float:
        x = [float(i) for i in x.split(";")[:-1]]
        y = [float(i) for i in y.split(";")[:-1]]
        if len(x) != len(y): raise ValueError("X and Y must have the same length")
        #Saturation
        if point < x[0]: return y[0]
        if point > x[-1]: return y[-1]
        i = 0
        while x[i] < point: i += 1
        return y[i-1] + (y[i]-y[i-1])*(point-x[i-1])/(x[i]-x[i-1])

    @staticmethod
    def map_by_proximity(x,y,point)->str:
        x = [float(i) for i in x.split(";")[:-1]]
        y = [i for i in y.split(";")[:-1]]
        if len(x) != len(y): raise ValueError("X and Y must have the same length")
        #Saturation
        if point < x[0]: return y[0]
        if point > x[-1]: return y[-1]
        i = 0
        while x[i] < point: i += 1
        return y[i] if abs(x[i]-point)<abs(x[i-1]-point) else y[i-1]