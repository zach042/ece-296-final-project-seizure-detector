from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
dsp = SSD1306_I2C(128,64,i2c)

class Oled:
    def __init__(self):
        self.x_left = 0.0
        self.x_right = 127.0
        self.y_top = 0.0
        self.y_bottom = 63.0
        self.page = 0
        self.display = dsp
    
    def draw_main_menu(self):
        self.clear()
        self.display.text("Time:", 0,0)
        
    def draw_right_menu(self):
        self.display.text("", 0,0)
        
    def draw_left_menu(self):
        self.display.text("", 0,0)
        
    def draw_seizure_alert(self):
        oled.clear
        self.display.text("SEIZURE DETECTED", 0, 0)
        self.display.text("ALERTING IN 15", 0, 0)
    def show(self):
        self.display.show()
        
    def await_input(self):
        time.sleep(1)
        
        
    def boot(self):
        self.draw_main_menu(self)
        self.await_input(self)
        
      

