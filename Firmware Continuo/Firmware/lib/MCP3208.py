import machine # type: ignore

class MCP3208:

    def __init__(self, spi, cs):#spi: configured SPI bus, cs:  pin to use for chip select, ref_voltage: r
        self.cs = cs
        self._spi = spi
        self._out_buf = bytearray(3)
        self._out_buf[0] = 0x01
        self._in_buf = bytearray(3)

    def read(self, pin):
        self.cs.value(0) # turn on
        self._in_buf = bytearray(3) #clean old value
        self._out_buf[0] = 0b00000111 if pin > 3 else 0b00000110
        self._out_buf[1] = pin << 6
        self._out_buf[2] = 0
        self._spi.write_readinto(self._out_buf, self._in_buf)
        self.cs.value(1) # turn off
        return  (((self._in_buf[1] << 8) & 0xFFF) | self._in_buf[2])
        #result = self.Bits16tobytes2(result, format='little')
        #return result #Return 2 bytes
        #return (((self._in_buf[1] << 8) & 0xFFF) | self._in_buf[2])
    
    def read_all(self):
        all_channels = []
        for i in range(8):
            all_channels.append(self.read(i))
            #values = self.read(i,False)
            #all_channels.append(((values[0] << 8) & 0xFFF) | values[1])
        return all_channels
        
    @staticmethod
    def Bits16tobytes2(bits, format = 'little')->list:
        By1 = bits >> 8  # Valores mayores
        By2 = bits % 256  # Valores menores
        return [By2, By1] if format == 'little' else [By1, By2] 
