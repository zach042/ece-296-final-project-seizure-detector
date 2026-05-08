from machine import UART, Pin, RTC
import time

gps = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))


class GPS:
    def __init__(self):
        self.lat = None
        self.lon = None
        self.fix = False
        self.time = None
        self.date = None
        self.rtc = RTC()
        
    def find_coords(self):
        
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

        

