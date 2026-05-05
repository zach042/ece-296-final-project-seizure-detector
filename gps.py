from machine import UART, Pin
import time

gps = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

class GPS:
    def __init__(self):
        self.lat = None
        self.lon = None
        self.fix = False
        self.find_coords()
        
    def find_coords(self):
        for i in range(20):
            if gps.any():
                line = gps.readline()
                
                if line and b'\n' in line:
                    newl = line.decode('utf-8').strip()
                    print(newl)
                    #if newl[3:5] == 'GGA':
                        #lat = (int(newl[17:19]) * (float(newl[19:27]))/60)
                        #print(lat)
            time.sleep_ms(25)
        


g = GPS()
g.find_coords()

