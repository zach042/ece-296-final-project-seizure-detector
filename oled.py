from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=400000)
dsp = SSD1306_I2C(128,64,i2c)

class Oled:
    def __init__(self):
        self.x_left = 0.0
        self.x_right = 127.0
        self.y_top = 0.0
        self.y_bottom = 63.0
        self.page = 0
        self.select = 0
        self.display = dsp
        self.page_change = False
        self.redraw_menu()
            
    def redraw_menu(self):
        self.draw_select()
        if self.page == 0:
            self.draw_main_menu()
        elif self.page == 1:
            self.draw_right_menu()
        elif self.page == 2:
            self.draw_seizure_alert()
        elif self.page == -1:
            self.draw_left_menu()
    
    def draw_main_menu(self):
        self.page = 0
        self.display.text("Time:", 0,0)
        self.show()
        
    def draw_right_menu(self):
        self.page = 1
        self.display.text("right menu", 0,0)
        self.show()
        
    def draw_left_menu(self):
        self.page = -1
        self.display.text("left menu", 0,0)
        self.show()
        
    def draw_same_menu(self):
        self.page = self.page
        
    def draw_seizure_alert(self):
        self.page = 2
        self.display.text("SEIZURE DETECTED", 0, 0)
        self.display.show()
        
    def trigger_seizure_warning(self):
        self.display.fill(0)
        self.display.text("!!", 120, 50)
        self.display.show()
    
    def show(self):
        self.display.show()
    
    def draw_select(self):
        if self.select <= 0 or self.select >= 5:
            self.select = 0
        self.display.fill_rect(115, 0, 9, 64, 0)
        if self.page_change == True:
            self.display.fill(0)
            self.select = 0
            self.page_change = False
        self.display.text("*", 115, self.select * 11)
        self.show()
        
    def boot(self):
        self.draw_main_menu()
        self.show()
        
        
      
ol = Oled()


