# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 11, 2026
# Filename: gps.py
# Description: gps.py serves as the file containing the GPS class. This class allows the GPS module's 
#              calculated lat, lon, and UTC time to be extracted, parsed, and acessed by instances of other classes
#              which accept the instance of a GPS class as an input.
#
#              The GPS class determines time, lat, and lon once it has a lock within the find_coords function,
#              updating these values within the local GPS class.
#
#              Once time and date have been ascerned by the GPS, these values are converted to local time / date
#              given the lat lon values. These values are passed to a local class instance of the RTC (real-time-clock)
#              module. Then, the current_time and current_date functions parse the rtc datetime array into strings where
#              where other class instances may access these values.
#
#              The self.time and self.date values are simply reference points, used to calculate the local time in conjunction with
#              the self.lat and self.lon values. These modified date / time values are then passed to rtc.datetime, where
#              the current_time and current_date functions neatly parse this data for external libraries. The self.date and self.time
#              values are never passed to outside modules, as they are inaccurate UTC values.
# ==========================================
#imports
from machine import UART, Pin, RTC #for interfacing with GPS module
import time #for time.sleep()

gps = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17)) #initialize gps module 


class GPS:
    """
    GPS class collects current time, date, lat, and lon, so that other modules
    can access these values and display them to the user or notify others when
    and where a seizure has occurred.
    
    RTC is used to keep track of the current datetime once these values have been
    ascerned by the GPS.
    """
    
    def __init__(self):
        self.lat = None
        self.lon = None
        self.fix = False
        self.time = None
        self.date = None
        self.rtc = RTC() #instance of RTC needed to take a given time / date value and properly update it
        
    """
    During initialization, all time, date, and location values must be set to zero, as they have
    not been determined yet.
    
    self.rtc sets up an initial clock with inaccurate values.
    
    """
        
    def find_coords(self):
        
        """
        Find_coords is the primary function used to 
        """
        
        for i in range(150):
            try:
                if gps.any():
                    line = gps.readline()

                    if line and b'\n' in line:
                        newl = line.decode('utf-8').strip()
                        newl = newl.split(',')
                        print(newl)
                            
                        if newl[0] == "$GPRMC" and not "A" in newl[12]:
                            self.fix = False
                        if newl[0] == "$GPGGA" and newl[2] != '' and self.fix == True:
                            self.lat = (int(newl[2][0:2]) + (float(newl[2][2:4]))/60)
                            if newl[3] == 'S':
                                self.lat = -self.lat
                            self.lon = (int(newl[4][0:3]) + (float(newl[4][3:-1]))/60)
                            if newl[5] == 'W':
                                self.lon = -self.lon
                            print(self.lat, self.lon)
                        if newl[0] == "$GPRMC" and newl[2] == 'A':
                            print('\nfixxxx')
                            self.fix = True

                            if len(newl[1]) >= 6:
                                hour = int(newl[1][0:2])
                                minute = int(newl[1][2:4])
                                second = int(newl[1][4:6])

                            if len(newl[9]) >= 6:
                                day = int(newl[9][0:2])
                                month = int(newl[9][2:4])
                                year = 2000 + int(newl[9][4:6])
                                
                                self.time = (f"{hour}:{minute}")
                                self.date = (f"{month}/{day}/{year}")

                                self.rtc.datetime((year, month, day, 1, hour, minute, second, 0))
                                print(f"RTC Set: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
            except:
                print("failed")
                        
            time.sleep(0.1)
            
        
            
    def current_time(self):
        """
        Passses the rtc time as a string to external modules.
        """
        t = self.rtc.datetime()
        
        if t:
            hour = t[4]
            minute = t[5]
            return f"{hour:02d}:{minute:02d}"
        else:
            return None
        
    def current_date(self):
        """
        Passses the rtc date as a string to external modules.
        """
        t = self.rtc
        d = self.rtc.datetime()
        
        if d:
            year = d[0]
            month = d[1]
            day = d[2]
            return f"{month}/{day}/{year}"
        else:
            return None

        

