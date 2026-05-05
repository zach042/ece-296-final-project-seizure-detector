from machine import UART, Pin
import time

gps = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))

class GPS:
    def __init__(self):
        self.lat = None
        self.lon = None
        self.fix = False
        self.find_coords()
        
    def find_coords(self):
        for i in range(100):
            if gps.any():
                line = gps.readline()

                if line and b'\n' in line:
                    newl = line.decode('utf-8').strip()
                    newl = newl.split(',')
                    print(newl)
                    if newl[0] == "$GPGGA" and newl[2] != '' and self.fix == True:
                        self.lat = (int(newl[2][0:2]) + (float(newl[2][2:4]))/60)
                        self.lon = (int(newl[4][0:3]) + (float(newl[4][3:-1]))/60)
                        print(self.lat, self.lon)
                    elif newl[0] == "$GPRMC" and newl[2] != '' and self.fix == False:
                        if "A" in newl[12]:
                            print('\nfixxxx')
                            self.fix = True
            time.sleep(0.1)
        
test = GPS()