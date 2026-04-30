import time
from machine import Pin
from ir_rx.nec import NEC_8
from ir_rx.print_error import print_error
irPin = 13
import oled

class IRController:
    def callback(self, IRbit, addr, ctrl):
        print(IRbit)
    
    def __init__(self, display):
        self.display = display
        self.irPin = 13
        self.device = NEC_8(Pin(irPin, Pin.IN), self.callback)
        

    def await_input(self):
        try:
            pass
        except KeyboardInterrupt:
            IR.close()
        
    
        


