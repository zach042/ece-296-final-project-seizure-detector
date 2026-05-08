import time
from machine import Pin
from ir_rx.nec import NEC_8
from ir_rx.print_error import print_error
import oled
from pio_ir_rx import PIO_IR_NEC
numpad = {"0x00ff6897": 0, "0x00ff30cf": 1, "0x00ff18e7": 2, "0x00ff7a85": 3, "0x00ff10ef": 4, "0x00ff38c7": 5, "0x00ff5aa5": 6, "0x00ff42bd": 7, "0x00ff4ab5": 8, "0x00ff52ad": 9}
commands = {"page_right": "0x00ffc23d", "page_left": "0x00ff02fd", "sel_up": "0x00ffa857", "sel_down": "0x00ff906f", "enter": "0x00ff22dd", "exit": "0x00ffa25d", "delete": "0x00ff9867"}

class IRController:
    
    def __init__(self, display):
        self.display = display
        self.input = None
        self.input_received = False
        self.device = PIO_IR_NEC(pin=19)
        self.code = '1234'
        

    def await_input(self):
        self.input = raw = self.device.read_raw()
        if raw is not None:
            self.input = f"{raw:#010x}"
            print(self.input)
            print(self.display.page)
            if self.display.lock == False:
                self.command_oled()
            elif self.display.lock == True and self.display.page == 2:
                self.display.unlock_seizure_screen(self.input)
            elif self.display.lock == True and self.display.page == -2:
                self.exit_menu()
                self.display.accept_code_in(self.input)
            elif self.display.lock == True and self.display.page == 4:
                self.exit_menu()
                self.display.accept_date_in(self.input)
            elif self.display.lock == True and self.display.page == 5:
                self.exit_menu()
                self.command_oled()
            
            
    def exit_menu(self):
        if self.input == commands["exit"] and self.display.page in [-2, 4, 5]:
            print('EXITING')
            self.display.lock = False
            self.display.display.fill(0)
            self.code_in = ""
            self.display.draw_main_menu()
    
    def command_oled(self):
        self.exit_menu()
        print('page', self.display.page)
        if self.input == commands["page_left"]:
            self.display.page_change = True
            
            if self.display.page == 0:
                self.display.page = -1
                
            elif self.display.page == 1:
                self.display.page = 0
                
            elif self.display.page == -1:
                self.display.page = 1
                
            self.display.redraw_menu()


        elif self.input == commands["page_right"]:
            self.display.page_change = True

            if self.display.page == 0:
                self.display.page = 1
            
            elif self.display.page == 1:
                self.display.page = -1
                
            elif self.display.page == -1:
                self.display.page = 0 
                
            self.display.redraw_menu()
                
        elif self.input == commands["sel_down"]:
            self.display.select = self.display.select + 1
            self.display.redraw_menu()
        
        elif self.input == commands["sel_up"]:
            self.display.select = self.display.select - 1
            self.display.redraw_menu()
            
        elif self.input == commands["enter"]:
            if self.display.page == 0:
                if self.display.select == 3:
                    self.display.code_in = ""
                    self.display.page = 4
                    self.display.display.fill(0)
                    self.display.accept_date_in(self.input)
                    
            elif self.display.page == -1:
                if self.display.select == 1:
                    self.display.buzzer.state = not self.display.buzzer.state
                    
                elif self.display.select == 2:
                    self.display.code_in = ""
                    self.display.page = -2
                    self.display.display.fill(0)
                    self.display.accept_code_in(self.input)
                    self.display.draw_change_code_menu()
                    
            elif self.display.page == 1:
                if self.display.select == 2:
                    self.display.draw_refresh_gps()
                    
            self.display.redraw_menu()
            
    def unlock_seizure_screen(self):
        print(self.input)
        if self.input in numpad and len(self.display.code_in) < 4:
            self.display.code_in += str(numpad[self.input])
        elif self.input == commands["delete"] and len(self.display.code_in) > 0:
            self.display.code_in = self.display.code_in[:-1]
        if self.display.code_in == self.code:
            self.display.lock = False
            self.display.page = 0
            self.display.display.fill(0)
            self.display.code_in = ""
        self.display.redraw_menu()
        


    
    def reset(self):
        self.input_received = False
    
    
        

