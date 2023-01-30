from micropython import const, mem_info # type: ignore
from machine import Pin, Timer # type: ignore
from emac import emac20 # type: ignore
from time import ticks_ms, ticks_diff

#Constants
MAIN_PERIOD = const(100)
DIGITAL_RESTART_FREQ = const(0.1)

#Corrige un ERROR de PCB resuelto para proximas versiones
Pin(3, Pin.OUT, value = 1) # type: ignore
# Start Pins to GND
for i in [0,1,2,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,"LED"]:
    Pin(i, Pin.OUT, value = 0) # type: ignore

#Digital inputs
ch7_digital = Pin(22,Pin.IN, Pin.PULL_UP)
ch8_digital = Pin(27,Pin.IN, Pin.PULL_UP)

#Data logger
data_logger = emac20()

#Timers
state_timer = Timer()
restart_digital_timer = Timer()

def main()->None:
    #Digital interrups
    ch7_digital.irq(trigger = Pin.IRQ_FALLING, handler=ch7_counter)
    ch8_digital.irq(trigger = Pin.IRQ_FALLING, handler=ch8_counter)
    #Digital
    restart_digital_timer.init(freq=DIGITAL_RESTART_FREQ, mode=Timer.PERIODIC, callback=digital_update)
    state_timer.init(mode= Timer.PERIODIC, period= MAIN_PERIOD, callback= sample)
    

def sample(self)-> None:
    #print(gc.mem_free()/1024) #RAM in Kbytes
    data_logger.sample()
    return

def ch7_counter(self)->None:
    data_logger._channels.ch7_add()
    return

def ch8_counter(self)->None:
    data_logger._channels.ch8_add()
    return

def digital_update(self)->None:
    data_logger._channels.digital_update()
    return

if __name__ == '__main__':
    main()
