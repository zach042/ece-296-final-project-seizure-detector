from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=400000)
dsp = SSD1306_I2C(128,64,i2c)

numpad = {"0x00ff6897": 0, "0x00ff30cf": 1, "0x00ff18e7": 2, "0x00ff7a85": 3, "0x00ff10ef": 4, "0x00ff38c7": 5, "0x00ff5aa5": 6, "0x00ff42bd": 7, "0x00ff4ab5": 8, "0x00ff52ad": 9}

class Oled:
    def __init__(self, buzzer, gps):
        self.x_left = 0.0
        self.x_right = 127.0
        self.y_top = 0.0
        self.y_bottom = 63.0
        self.page = 0
        self.select = 0
        self.gps = gps
        
        self.display = dsp
        self.buzzer = buzzer

        self.page_change = False
        self.lock = False
        
        self.code_in = ""
        self.code = "1234"
        
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
        elif self.page == -2:
            self.draw_change_code_menu()
    
    def draw_main_menu(self):
        self.page = 0
        self.display.text("Time:", 0,0)
        self.show()
        
    def draw_right_menu(self):
        self.page = 1
        self.display.text("gps config", 0,0)
        if self.gps.fix == True and self.gps.lat and self.gps.lon:
            self.display.text("gps connected", 0, 10)
            self.display.text("lat: ", 0, 40)
            self.display.text(str(self.gps.lat), 40, 40)
            self.display.text("lon: ", 0, 50)
            self.display.text(str(self.gps.lon), 40, 50)
        elif self.gps.fix == False:
            self.display.text("gps offline", 0, 10)
        self.display.text("refresh gps", 0, 20)
        self.display.text("_", 115, 23)
        self.show()
    
    def draw_refresh_gps(self):
        self.display.fill(0)
        self.display.text("refreshing gps", 0, 0)
        self.display.text("loading", 60, 32)
        self.show()
        self.gps.find_coords()
        self.display.fill(0)
        if self.gps.fix == True:
            self.display.text("gps signal found", 0, 30)
            time.sleep(2)
        elif self.gps.fix == False:
            self.display.text("gps signal not found", 0, 30)
            time.sleep(2)
        self.display.fill(0)
        self.redraw_menu()
        
        
    def draw_left_menu(self):
        self.display.fill_rect(30, 10, 50, 64, 0)
        self.page = -1
        self.display.text("Settings", 0,0)
        self.display.text("buzzer", 0,10)
        self.display.text(str(self.buzzer.state), 55, 10)
        self.display.text("change code", 0,20)
        self.show()
        
    def draw_same_menu(self):
        self.page = self.page
        
    def draw_seizure_alert(self):
        self.page = 2
        self.lock = True
        self.display.fill_rect(0, 40, 115, 64, 0)
        self.display.text("SEIZURE DETECTED", 0, 0)
        self.display.text("enter code to", 0, 10)
        self.display.text("disarm", 0, 20)
        self.accept_code()
        self.display.show()
        
    def draw_change_code_menu(self):
        self.page = -2
        self.lock = True
        self.display.fill_rect(0, 40, 115, 64, 0)
        self.display.text("new code: ", 0, 0)
        self.accept_code()
        self.display.show()
        
    def accept_code_in(self, input):
        
        if input in numpad and len(self.code_in) < 4:
            self.code_in += str(numpad[input])
        elif input == "0x00ff9867" and len(self.code_in) > 0:
            self.code_in = self.code_in[:-1]
        if len(self.code_in) == 4:
            self.display.fill(0)
            self.code = self.code_in
            self.code_in = ""
            self.display.text("code changed", 0, 0)
            self.display.text("to: ", 0, 10)
            self.display.text(self.code, 0, 30)
            self.show()
            time.sleep(2)
            self.display.fill(0)
            self.lock = False
            self.page = 0


        self.redraw_menu()
        
    def unlock_seizure_screen(self, input):
        print(input)
        
        if input in numpad and len(self.code_in) < 4:
            self.code_in += str(numpad[input])
        elif input == "0x00ff9867" and len(self.code_in) > 0:
            self.code_in = self.code_in[:-1]
        if self.code_in == self.code:
            self.lock = False
            self.page = 0
            self.display.fill(0)
            self.code_in = ""
        self.redraw_menu()
        

        
    def accept_code(self):
        self.display.text("_ _ _ _", 0, 42)
        self.display.text(" ".join(self.code_in), 0, 40)
        
        
    def trigger_seizure_warning(self):
        self.display.fill(0)
        self.display.text("!!", 120, 50)
        self.display.show()
    
    def show(self):
        self.display.show()
        
    def unlock(self):
        self.lock = False
        self.code_in = ""
    
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
        
        

        

    
