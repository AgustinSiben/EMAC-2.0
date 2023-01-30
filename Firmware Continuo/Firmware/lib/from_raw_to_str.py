from rtc_plus import Rtc_Plus

rtc = Rtc_Plus()

def data_to_string(line,name,sensors,gps)->str:
    string = f"{name},"
    #string += str(rtc.get_julian_time() - rtc.get_time_offset())
    string += str(line)
    string += ','
    if 'date' in gps:
        string += str(gps['date'])[4:6]
        string += '/'
        string += str(gps['date'])[2:4]
        string += '/'
        string += str(gps['date'])[0:2]
    string += ','
    if 'time' in gps:
        string += str(gps['time'])[0:2]
        string += ':'
        string += str(gps['time'])[2:4]
        string += ':'
        string += str(gps['time'])[4:6]
    string += ','
    if 'latitude' in gps:
        if str(gps['latitude cardinal']) == 'S': string += '-'
        grados = float(gps['latitude'][:2])
        d_minutos = float(gps['latitude'][2:])/60
        string += str(grados + d_minutos)
    string += ','
    if 'longitude' in gps:
        if str(gps['longitude cardinal']) == 'W': string +='-'
        if str(gps['longitude'])[0] == '0':
            grados = float(gps['longitude'][:3])
            d_minutos = float(gps['longitude'][3:])/60
            string += str(grados + d_minutos)
    string += ','
    if 'course' in gps: string += str(gps['course'])
    string += ','
    if 'speed' in gps: string += str(gps['speed'])
    string += ','
    if 'altitude' in gps: string += str(gps['altitude'])
    string += ','
    #if 'GPS  quality' in gps: string += str(gps['GPS  quality'])
    #string += ','
    if 'number of satellites' in gps: string += str(gps['number of satellites'])
    string += ','
    for channel in sensors:
        if channel != None: string += str(channel)
        string += ','
    return string

def make_status(dictionary)->str:
    return f"{dictionary['NMEA']},{dictionary['SD']},{dictionary['GPS']},{dictionary['SONAR']},{dictionary['NA_0']},{dictionary['NA_1']},{dictionary['record']},{str(dictionary['counter'])},{str(dictionary['file_name'])}"

#NOMBRE,FECHA,HORA,LAT,N/S,LONG,E/W,CURSO,VELOCIDAD,ALTITUD,CALIDAD DE GPS,NUMERO DE SATELITES,CANALES
def make_units(channels_units)->str:
    units = ["$UNITS","°","km/h","m","",""]
    for channel in channels_units:
        units.append(channel)
    units = ",".join(units)
    #len(units.split(',')) == 19 para la app
    return units

def make_config(json)->str:
    config_array = ['$CONFIG']
    EMAC = json['EMAC']
    CONFIGURATION = json['CONFIGURATION']
    COMUNICATION = json['COMUNICATION']
    WIFI = COMUNICATION['WIFI']
    GPS = COMUNICATION['GPS']
    config_array.append(EMAC['SAMPLE_RATE_ms'])
    config_array.append(EMAC['TABLES_PATH'])
    config_array.append(EMAC['ADC_Vref'])
    config_array.append(CONFIGURATION['name'])
    for i in CONFIGURATION['channels_cfg']:
        config_array.append(i)
    config_array.append(WIFI['ENABLED'])
    config_array.append(WIFI['SEND_PERIOD_S'])
    config_array.append(WIFI['LAN_SSID'])
    config_array.append(WIFI['LAN_PASSWORD'])
    config_array.append(WIFI['SERVER_IP'])
    config_array.append(WIFI['SERVER_PORT'])
    config_array.append(GPS['CONNECTION'])
    config_array = list(map(str,config_array))
    return ",".join(config_array)