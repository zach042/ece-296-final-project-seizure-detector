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
import config

gps = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17)) #initialize gps module
UTC_OFFSET = config.UTC_OFFSET
days = config.days

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
        self.searching = False
        self.rtc = RTC() #instance of RTC needed to take a given time / date value and properly update it
        
    """
    During initialization, all time, date, and location values must be set to zero, as they have
    not been determined yet.
    
    self.rtc sets up an initial clock with initially inaccurate values, on my Pico W, this is a 2021 date.
    
    """
        
    def find_coords(self):
        
        """
        Find_coords is the only function outside modules should call which change any interior values of an instance
        of the GPS class. This function should be called when the overall device is able to pause other processes and
        focus entirely on pulling time and coordinate values from the GPS module.
        
        This function parses the text constantly outputted from the physical GPS module, determining if the GPS has a fix,
        what the coordinates are, what the UTC time is, and what the local time is given the config.py time offset.
        
        This function takes no inputs apart from self and returns nothing, only updating the internal variables of the instance of the GPS class,
        which should be accessed by external classes directly or via the current_time and current_date functions.
        
        The function runs for approximately 15-18 seconds, as the loop iterates 150 time, sleeping .1 second per iteration, while the GPS logic itself
        is near instantaneous. The reason for running 150 iterations is because the program will attempt to read 150 individual lines of GPS text output,
        eliminating the chance of the program 'missing' lines.
        """
        
#for loop runs for 15 seconds
        for i in range(150):
    #try / except elegantly returns to loop if the program fails to read a line
            try:
        #if there is a line, parse it with readline()
                if gps.any():
                    line = gps.readline()
            #if there is a newline character, seperate it and analyze that line
                    if line and b'\n' in line:
                        newl = line.decode('utf-8').strip()
                        newl = newl.split(',')
                        print(newl)
                #RMC provides a fix flag 'A' in both RMC[2] and RMC[12]
                        if newl[0] == "$GPRMC" and not "A" in newl[12]:
                            self.fix = False
                #GGA is for coordinates, if there is a fix and data in the reading, lat lon values can be parsed from GGA
                        if newl[0] == "$GPGGA" and newl[2] != '' and self.fix == True:
                            self.lat = (int(newl[2][0:2]) + (float(newl[2][2:4]))/60) #parse out lat values, and convert the degrees
                    #if lat is southern hemisphere, ensure reading is negative
                            if newl[3] == 'S': 
                                self.lat = -self.lat
                            self.lon = (int(newl[4][0:3]) + (float(newl[4][3:-1]))/60) #parse out lon values and convert the degrees
                    #if lon is western hemisphere, ensure reading is negative
                            if newl[5] == 'W':
                                self.lon = -self.lon
                            print(self.lat, self.lon)
                #RMC line is for checking time values, and 'A' in RMC[2] indicates a fix.
                        if newl[0] == "$GPRMC" and newl[2] == 'A':
                            self.fix = True
                            
                            if len(newl[1]) >= 6: #RMC[1] contains time values, and would typically be empty without a fix, that's why we check length
                                hour = int(newl[1][0:2])
                                minute = int(newl[1][2:4])
                                second = int(newl[1][4:6])

                            if len(newl[9]) >= 6: #RMC[9] contains date values, and would typically be empty without a fix, that's why we check length
                                day = int(newl[9][0:2])
                                month = int(newl[9][2:4])
                                year = 2000 + int(newl[9][4:6])
                                
                            #+/- flags are critical to determining how the UTC -> local time conversion works. if +, add values, if - subtract values.
                                if UTC_OFFSET[0] == "+":
                                    corrected_hour = hour + int(UTC_OFFSET[1:3])
                                    corrected_minute = minute + int(UTC_OFFSET[4:6])
                                elif UTC_OFFSET[0] == "-":
                                    corrected_hour = hour - int(UTC_OFFSET[1:3])
                                    corrected_minute = minute - int(UTC_OFFSET[4:6])
                                corrected_day = day
                                corrected_month = month
                                corrected_year = year
                            #if once the minutes have been added / subtracted, the time is > 60 | < 60, correct that accordingly
                                if corrected_minute > 59:
                                    corrected_minute = corrected_minute - 60
                                    corrected_hour = corrected_hour + 1
                                elif corrected_minute < 0:
                                    corrected_minute = corrected_minute + 60
                                    corrected_hour = corrected_hour - 1
                            #if once the hours have been added / subtracted, the hour is > 24 | < 24, correct that accordingly
                                if corrected_hour >= 24:
                                    corrected_hour = corrected_hour - 24 #resets back to a 24-hour time, time exceeding an hour should be reset to a new day
                                    corrected_day = day + 1 #if the hour spans into a new day, the day itself must be corrected
                                elif corrected_hour < 0: 
                                    corrected_hour = 24 + corrected_hour #resets back to 24 hour time if UTC is ahead of local time
                                    corrected_day = day - 1 #if the UTC leads local time by a day, the day itself requires correction
                                    
                            #if the day has been corrected by a leading / lagging UTC, month and year may also need correction. This code checks that.
                                if corrected_day <= 0: 
                                    if month > 1: #if the corrected day goes back a day and the month is not January, simply shift back a month and reset the day accordingly
                                        corrected_month = month - 1
                                        corrected_day = days[corrected_month - 1] #-1 is necessary because the days indices are 0-11 while months are 1-12.
                                    elif month == 1: #if the corrected day goes back a day and the month is January, reset to December
                                        corrected_month = 12
                                        corrected_day = days[11]
                                elif corrected_day > days[corrected_month - 1]: #logic branch for if the corrected day needs to go forward in time
                                    if month < 12: #if month is not December and and the corrected day exceeds the limit of days for that month, shift the month forward and reset the day to the first day of that month
                                        corrected_month = month + 1
                                        corrected_day = 1 #reset day
                                    elif month == 12: #if month is december, reset month to January, reset the the day to 1, and increment the year ahead.
                                        corrected_month = 1
                                        corrected_day = 1
                                        corrected_year = year + 1
                                        
                                #set real time clock datetime
                                self.rtc.datetime((corrected_year, corrected_month, corrected_day, 1, corrected_hour, corrected_minute, second, 0))
            except:
                #if there is an error parsing a line, loop back o start of for loop
                print("failed")
                        
            time.sleep(0.1)
            
        
            
    def current_time(self):
        """
        Passses the rtc time as a string to external modules.
        """
        t = self.rtc.datetime()
#piece out the hour, minute, and year second from datetime if they exist
        if t:
            hour = t[4]
            minute = t[5]
            return f"{hour:02d}:{minute:02d}" #place time in the standard HH:SS format used throughout this project
#if there is no rtc.datetime object return nothing
        else:
            return None
        
    def current_date(self):
        """
        Passses the rtc date as a string to external modules.
        """
        d = self.rtc.datetime() #current date time array
#piece out the month, day, and year values from datetime if they exist
        if d:
            year = d[0]
            month = d[1]
            day = d[2]
            return f"{month}/{day}/{year}" #format year month and day into the standardized MM:DD:Y format used throughout the rest of the program. Requires parsing into YY in external classes though
#if there is no rtc.datetime object return nothing
        else:
            return None

        



