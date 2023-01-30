def to_dict(string):
    dict = {}
    all_nmea = string.split('\n')
    for nmea in all_nmea:
        if nmea[:6] == '$GPRMC':
            dict.update(GPRMC_to_dict(nmea))
        if nmea[:6] == '$GPVTG':
            dict.update(GPVTG_to_dict(nmea))
        if nmea[:6] == '$GPGGA':
            dict.update(GPGGA_to_dict(nmea))
        #if nmea[:6] == '$GPGSA':
        #if nmea[:6] == '$GPGSV': # Unused or redundant
        #if nmea[:6] == '$GPGLL':
 
    return dict

def GPRMC_to_dict(string):
    splited = string.split(',')
    dict = {}
    if splited[1] != '': dict['time'] = splited[1]
    if splited[2] != '': dict['warning'] = splited[2]
    if splited[3] != '': dict['latitude'] = splited[3]
    if splited[4] != '': dict['latitude cardinal'] = splited[4]
    if splited[5] != '': dict['longitude'] = splited[5]
    if splited[6] != '': dict['longitude cardinal'] = splited[6]
    #if splited[7] != '': dict['speed'] = splited[7]
    if splited[9] != '': dict['date'] = splited[9]
    #if splited[10] != '': dict['magnetic variation'] = splited[10]
    #if splited[11] != '': dict['magnetic variation cardinal'] = splited[11]
    return dict

def GPVTG_to_dict(string):
    splited = string.split(',')
    dict = {}
    if splited[1] != '': dict['course'] = splited[1]#dict['track made good'] = splited[1]
    #if splited[2] != '': dict['fixed text T'] = splited[2]
    #if splited[5] != '': dict['speed'] = splited[5] 
    #if splited[6] != '': dict['fixed text N'] = splited[6]
    if splited[7] != '': dict['speed km/h'] = splited[7]
    #if splited[8] != '': dict['fixed text K'] = splited[8]
    return dict
 
def GPGGA_to_dict(string):
    splited = string.split(',')
    dict = {}
    #if splited[6] != '': dict['GPS  quality'] = splited[6]
    if splited[7] != '': dict['number of satellites'] = splited[7]
    #if splited[8] != '': dict['horizontal dilution of position'] = splited[8]
    if splited[9] != '': dict['altitude'] = splited[9]
    return dict