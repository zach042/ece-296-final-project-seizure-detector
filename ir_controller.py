import time
from machine import Pin
from ir_rx.nec import NEC_8
from ir_rx.print_error import print_error
import oled
from pio_ir_rx import PIO_IR_NEC
numpad = {"0x00ff6897": 0, "0x00ff30cf": 1, "0x00ff18e7": 2, "0x00ff7a85": 3, "0x00ff10ef": 4, "0x00ff38c7": 5, "0x00ff5aa5": 6, "0x00ff42bd": 7, "0x00ff4ab5": 8, "0x00ff52ad": 9}

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
            elif self.display.lock == True:
                self.unlock_seizure_screen()
            
            
    
    def command_oled(self):
        print('page', self.display.page)
        if self.input == "0x00ff02fd":
            self.display.page_change = True
            
            if self.display.page == 0:
                self.display.page = -1
                
            elif self.display.page == 1:
                self.display.page = 0
                
            elif self.display.page == -1:
                self.display.page = 1
                
            self.display.redraw_menu()


        elif self.input == "0x00ffc23d":
            self.display.page_change = True

            if self.display.page == 0:
                self.display.page = 1
            
            elif self.display.page == 1:
                self.display.page = -1
                
            elif self.display.page == -1:
                self.display.page = 0 
                
            self.display.redraw_menu()
                
        elif self.input == "0x00ff906f":
            self.display.select = self.display.select + 1
            self.display.redraw_menu()
        
        elif self.input == "0x00ffa857":
            self.display.select = self.display.select - 1
            self.display.redraw_menu()
            
    def unlock_seizure_screen(self):
        print(self.input)
        if self.input in numpad and len(self.display.code_in) < 4:
            self.display.code_in += str(numpad[self.input])
        elif self.input == "0x00ff9867" and len(self.display.code_in) > 0:
            self.display.code_in = self.display.code_in[:-1]
        if self.display.code_in == self.code:
            self.display.lock = False
            self.display.page = 0
            self.display.display.fill(0)
        self.display.redraw_menu()
        


    
    def reset(self):
        self.input_received = False
    
    
        

