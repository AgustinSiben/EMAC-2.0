# import gc # type: ignore
from ujson import load  # type: ignore
from micropython import mem_info  # type: ignore
from machine import Pin, Timer  # type: ignore
import uasyncio as asynci
from lib.comunication import *
from lib.emac import data_logger

Pin(3, Pin.OUT, value=1)  # type: ignore
# Start Pins to GND
for i in [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 26, 27, 28]:
    Pin(i, Pin.IN)  # type: ignore

# Timers
state_timer = Timer()
restart_digital_timer = Timer()
MAIN_PERIOD = 100
DIGITAL_RESTART_FREQ = 0.1


def next_state(self) -> None:
    data_logger.next_state()


def ch7_counter(self) -> None:
    data_logger._channels.ch7_add()


def ch8_counter(self) -> None:
    data_logger._channels.ch8_add()


def digital_update(self) -> None:
    data_logger._channels.digital_update()


async def main() -> None:
    # Digital interrups
    # Ch7 Interrupt - Not implemented on Mercury
    # Pin(22, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_RISING,
    #                                 handler=ch7_counter)
    # Ch8 Interrupt
    Pin(27, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_RISING,
                                     handler=ch8_counter)
    # Digital
    state_timer.init(mode=Timer.PERIODIC,
                     period=MAIN_PERIOD,
                     callback=next_state)

    restart_digital_timer.init(freq=DIGITAL_RESTART_FREQ,
                               mode=Timer.PERIODIC,
                               callback=digital_update)

    # Asyncio tasks
    await asyncio.gather(asyncio.create_task(request_configuration(60)),
                         asyncio.create_task(check_communications(100)),
                         asyncio.create_task(connect_socket()),
                         asyncio.create_task(modem_check()))


if __name__ == '__main__':
    asyncio.run(main())
