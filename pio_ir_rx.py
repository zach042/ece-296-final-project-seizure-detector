# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 10, 2026
# Filename: pio_ir_rx.py
# Description: This file implements a custom NEC IR Protocol using the Pico W's PIO State Machines.
#              Functionally what this means is that constant signal detection is offloaded from both
#              Pico W cores, meaning that at any instant, the cores can be working on their own tasks
#              while one of the onboard FSM's handles IR input. This is a superior design largely because
#              it allows for perfect, non-blocking IR interface with the project. Alternative solutions
#              often require the Pi to actively listen for an IR input on the main thread, interrupting
#              every other aspect of the project. In essence, the IR reception does not interfere with
#              the primary seizure detection loop or the secondary core Goertzel analysis and server process.
#
#              To achieve this custom FSM NEC process, assembly code was required to be written rather than
#              Micropython, as it would be impossible to program the onboard FSM to this extent using
#              Micropython.
#
#              The NEC uses what is known as 'pulse-distance' encoding, where a leader bit predates data bits, while
#              the data bits themselves are encoded by the length of the space preceeding the data / after the burst.
#              The state machine measures the length of pulses using hardware timers / x / y registers.
# ==========================================

#necessary imports
import rp2 #module for dealng with the PIO hardware
from rp2 import PIO, StateMachine #necessary for FSM logic with PIO hardware
from machine import Pin 

#writing an ASM function, not micropython
@rp2.asm_pio(
    in_shiftdir=PIO.SHIFT_LEFT, #bits shift into ISR from the right
    autopush=False, #bits are manually shifted left
    push_thresh=32, #32 bit value is being built
    fifo_join=PIO.JOIN_RX,
)
def nec_rx_pio():
    """
    This function runs on the onboard FSM, waiting for a specific pattern to be recieved from the IR sensor.
    A 32 bit value is constructed in the input shift register.
    
    This function will wait for a start burst, if it recieves that, then measure the high signal, looping 32 times to masure
    individual bits, and then push the final 32-bit value.
    """
    # --- Wait for leader burst (pin goes LOW for a long time) ---
    wrap_target()

    label("reset")
    
    # state machine is set to wait until pin goes to low
    wait(0, pin, 0)

    #logic to see if a pin was high long enough - functionally a timer to verify if it was 9ms
    set(x, 29) # x starts at 29, coutning down to 0 over 240 ticks (5ms)
    label("count_burst")
    jmp(pin, "reset") # if pin goes high before the counter runs out, reset
    jmp(x_dec, "count_burst") [6] # count down until the loop x hits 0

    # state machine is set to wait until pin goes to high, after the signal has lasted long enough
    wait(1, pin, 0)

    # Count the leader space to distinguish data (4.5ms) from repeat (2.25ms)
    # Threshold: 170 ticks (3.4ms)
    # 20 loops * 8 cycles = 160 ticks 3.2ms
    
    set(x, 19)
    label("count_space")
    jmp(pin, "space_high")
    # Pin went low before threshold = repeat code, ignore and restart
    jmp("reset")
    label("space_high")
    jmp(x_dec, "count_space") [6]

    # This is a data frame. Wait for the leader space to end (pin goes LOW)
    wait(0, pin, 0)

    
    set(y, 31)

    label("next_bit")
    # Each bit starts with a 562us burst (pin LOW)
    # Wait for the burst to end (pin goes HIGH = space starts)
    wait(1, pin, 0)

    # Now measure the space duration

    set(x, 6)
    label("measure")
    jmp(pin, "still_high")
    # Pin went LOW = space ended = short space = bit 0
    set(x, 0)
    in_(x, 1)# shift in a 0
    jmp("bit_done")
    label("still_high")
    jmp(x_dec, "measure") [5]# 8 cycles per iteration

    # Threshold exceeded = long space = bit 1
    set(x, 1)
    in_(x, 1) # shift in a 1
    # Wait for space to end (pin goes LOW = next burst)
    wait(0, pin, 0)

    label("bit_done")
    jmp(y_dec, "next_bit")

    # All 32 bits received - push to FIFO
    push(block)

    wrap()


class PIO_IR_NEC:
    """
    The PIO_IR_NEC class is basically just a Python implementation of the NEC state machine. The class
    handles the intiitalization of the onboard hardware, and provides methods to get the decoded commands.
    
    Repaet is a constant used to identify repeating signals.
    """
    
    REPEAT = -1 #identify repeating signals

    def __init__(self, pin=13, sm_id=0):
        """
        Initializes the state machine on 
        """
        self.ir_pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.sm = StateMachine(
            sm_id,
            nec_rx_pio,
            freq=50_000,        # 50kHz = 20us per tick
            in_base=self.ir_pin,
            jmp_pin=self.ir_pin,
        )
        self.sm.active(1)

    def read(self):
        if self.sm.rx_fifo() > 0:
            raw = self.sm.get()
            addr = (raw >> 24) & 0xFF
            addr_inv = (raw >> 16) & 0xFF
            cmd = (raw >> 8) & 0xFF
            cmd_inv = raw & 0xFF

            # Validate command
            if (cmd ^ cmd_inv) == 0xFF:
                # Valid command byte
                if (addr ^ addr_inv) == 0xFF:
                    # Standard 8-bit address
                    return (addr, cmd)
                else:
                    # Extended 16-bit address
                    return (addr | (addr_inv << 8), cmd)
            else:
                # Try reversed bit order
                raw_r = self._reverse_bits(raw)
                addr = (raw_r >> 24) & 0xFF
                addr_inv = (raw_r >> 16) & 0xFF
                cmd = (raw_r >> 8) & 0xFF
                cmd_inv = raw_r & 0xFF
                if (cmd ^ cmd_inv) == 0xFF:
                    if (addr ^ addr_inv) == 0xFF:
                        return (addr, cmd)
                    else:
                        return (addr | (addr_inv << 8), cmd)
                # Invalid frame
                return None
        return None

    def read_raw(self):
        """Non-blocking read. Returns raw 32-bit value or None."""
        if self.sm.rx_fifo() > 0:
            return self.sm.get()
        return None

    def flush(self):
        """Clear any pending data in the FIFO."""
        while self.sm.rx_fifo() > 0:
            self.sm.get()

    def close(self):
        """Stop the state machine."""
        self.sm.active(0)

    @staticmethod
    def _reverse_bits(val):
        """Reverse bits in a 32-bit value."""
        result = 0
        for i in range(32):
            result = (result << 1) | (val & 1)
            val >>= 1
        return result


