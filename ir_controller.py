import time
from machine import Pin
from ir_rx.nec import NEC_8
from ir_rx.print_error import print_error
irPin = 13
import oled
from pio_ir_rx import PIO_IR_NEC
    

class IRController:
    
    def __init__(self, display):
        self.display = display
        self.input = None
        self.input_received = False
        self.device = PIO_IR_NEC(pin=13)
        

    def await_input(self):
        self.input = raw = self.device.read_raw()
        if raw is not None:
            self.input = f"{raw:#010x}"
            print(self.input)
            print(self.display.page)
            self.command_oled()
    
    def command_oled(self):
        print('page', self.display.page)
        if self.input == "0x00ff02fd":
            if self.display.page == 0:
                self.display.draw_left_menu()
                
            elif self.display.page == 1:
                self.display.draw_main_menu()
                
            elif self.display.page == -1:
                self.display.draw_right_menu()

        elif self.input == "0x00ffc23d":
            if self.display.page == 0:
                self.display.draw_right_menu()
            
            elif self.display.page == 1:
                self.display.draw_left_menu()
                
            elif self.display.page == -1:
                self.display.draw_main_menu()
    
    def reset(self):
        self.input_received = False
    
    
        


