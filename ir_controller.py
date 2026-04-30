import time
from machine import Pin
from ir_rx.nec import NEC_8
from ir_rx.print_error import print_error
irPin = 13
myIR = Pin(irPin, Pin.IN)

def callback(IRBit, addr, ctrl):
    print(IRBit)
    
IR = NEC_8(myIR, callback)

try:
    while True:
        pass
except KeyboardInterrupt:
    IR.close()
    print('program terminated')