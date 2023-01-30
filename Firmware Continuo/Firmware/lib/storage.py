from machine import Pin, SPI # type: ignore
import uos # type: ignore
import sdcard # type: ignore

class SD:
    def __init__(self)->None:
    # SD card init mount on /sd
        self._spi = SPI(1,
                baudrate=1000000,
                polarity=0,
                phase=0,
                bits=8,
                firstbit=SPI.MSB,
                sck=Pin(10),
                mosi=Pin(11),
                miso=Pin(12))
        self._status = False
        self._files_name_offset = 0
        try:
            # Initialize SD card
            sd = sdcard.SDCard(self._spi, Pin(13, Pin.OUT))     # Assign chip select (CS) pin (and start it high)
            # Mount filesystem
            vfs = uos.VfsFat(sd)
            uos.mount(vfs, "/sd") # type: ignore
        except:
            #System does not have sd
            self._status = False
            Pin("LED", Pin.OUT, value = 1) # type: ignore
        else:
            #System has sd
            self._status = True
            Pin("LED", Pin.OUT, value = 0) # type: ignore
        try: #Create directory if not exist (Hay formas mas prolijas de hacerlo, acomodar)
            uos.mkdir("/sd/datos")
            print('Directory created: "sd/data"')
        except:
            pass #sd/data already exist'
        if self._status: self._files_name_offset = len(uos.listdir("/sd/datos"))


    def set_status(self,status)->None:
        self._status = status
        return

    def get_status(self)->bool:
        try:
            uos.listdir("/sd")
            return True
        except:
            return False

    def get_file_offset(self)->int:
        return self._files_name_offset

    def get_files_name_offset(self):
        return self._files_name_offset

    @staticmethod
    def get_free_space()->float: #return free space
        try:
            free_space = statvfs('/sd') # type: ignore
            return ((free_space[0]*free_space[3])/1048576)
        except:
            print("SD ERROR in statvfs('/sd')")
            return 0  # type: ignore

def create(path = '//')->None:
    with open(path, 'X'):
        pass
    return

def read(path, length = None)-> str | bytes:
    with open(path, 'rb') as f:
        if length == None:
            return f.read()
        else:
            return f.read(length)

def write(data, path = '//')->None:
    with open(path, 'wb') as f:
        f.write(data)
    return

def append_to(data, path = '//')->None:
    with open(path, 'a') as f:
        f.write(data)
    return

def remove(path)->None:
    try:
        uos.remove(path)
    except:
        print('The file does not exist')     
    return

def rename(old_path, new_path)->None:
    try:
        uos.rename(old_path, new_path)
    except:
        print('Error renaming file')
    return

def get_free_space(style= 'absolute')->float: # type: ignore #return free space
    if style != 'used' and style != 'absolute' and style != 'percentage':
        print("get_free_space only support Style as 'used' or 'absolute' or 'percentage'")
        return 0
    status = uos.statvfs('//')
    if style == 'absolute':
        return ((status[0]*status[3])/1048576) # type: ignore #Block size/free_block / Megabytes 
    if style == 'percentage':
        return (status[3])/(status[2]) # type: ignore # Free blocks / total blocks 
    if style == 'used':
        return status[0]*(status[2]-status[3]) # type: ignore # block size (total blocks - free blocks) 

def space_of_data()->int | None: #return space of '/data.bin'
    try:
        size = uos.stat('/data.bin')[6]
        if size == None: size = 0
        return size
    except:
        return 0

def get_sd_free_space()->None: #return free space
    try:
        free_space = statvfs('/sd') # type: ignore
        return ((free_space[0]*free_space[3])/1048576)
    except:
        print("SD ERROR in statvfs('/sd')")
        return 0  # type: ignore

def system_has_sd_config()->bool:
        try:
            with open("/sd/config.json","r") as f:
                return True
        except:
            return False