from machine import RTC # type: ignore
from utime import gmtime, mktime # type: ignore

# RTC library use
#(year, month, day, weekday, hours, minutes, seconds, subseconds)
#
# Time library use:
# (year, month, mday, hour, minute, second, weekday, yearday)

class Rtc_Plus:
    def __init__(self)->None:
        self._ZERO_AT = (2000, 1, 1, -1, 0, 0, 0, 0) #-1 autocalculate weekday format rtc
        self._JULIAN_ZERO = mktime(self.format_rtc_to_time(self._ZERO_AT))
        self._TIME_OFFSET = 0
        self.rtc = RTC()
        self.rtc.datetime(self._ZERO_AT) #Init at 01/01/2000 00:00:00hs

    def set_time(self, time)->None:
        if type(time) == tuple:
            self.rtc.datetime(time)
        if type(time) == int:
            time = self.julian_to_time(time)
            time = self.format_time_to_rtc(time)
            self.rtc.datetime(time)
    
    def get_time(self)->tuple:
        return self.format_rtc_to_time(self.rtc.datetime())

    def get_julian_time(self)->int:
        return self.date_to_julian(self.rtc.datetime())

    def date_to_julian(self, date)->int:
        return (mktime(self.format_rtc_to_time(date)) - self._JULIAN_ZERO)

    def time_to(self,date)->int: #return in secods time to "date"
        if type(date) == int:
            date = self.julian_to_time(date)
        time_now = mktime(self.format_rtc_to_time(self.rtc.datetime()))
        start_time = mktime(date)
        return start_time - time_now
    
    def set_time_offset(self,offset)->None:
        self._TIME_OFFSET = offset
        return
    
    def get_time_offset(self)->int:
        return self._TIME_OFFSET

    @staticmethod
    def format_time_to_rtc(date_time_format)->tuple:
        #(year, month, day, -1(auto set), hours, minutes, seconds, 0(not used))
        return (date_time_format[0],date_time_format[1],date_time_format[2],-1,date_time_format[3],date_time_format[4],date_time_format[5],0)
    
    @staticmethod
    def format_rtc_to_time(date_rtc_format)->tuple:
        #(year, month, mday, hour, minute, second, weekday, -1(auto set))
        return (date_rtc_format[0],date_rtc_format[1],date_rtc_format[2],date_rtc_format[4],date_rtc_format[5],date_rtc_format[6],date_rtc_format[3],0)
    
    @staticmethod
    def julian_to_time(julian)->tuple:
        return gmtime(julian) # type: ignore