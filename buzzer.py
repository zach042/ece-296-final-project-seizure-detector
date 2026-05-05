import time
import machine

class Buzzer:
    def __init__(self, pin_id=18):
        self.buzzer = machine.Pin(pin_id, machine.Pin.OUT)
        self.is_active = False
        self.buzz_start_time = 0
        self.buzz_high = False
        self.current_step = 0
        self.step_duration_ms = 300
        self.last_toggle_time = 0

    def trigger(self):
        """Start the buzz sequence immediately without blocking."""
        if self.is_active == False:
            self.is_active = True
            self.current_step = 0
            self.buzz_start_time = time.ticks_ms()
            self.last_toggle_time = self.buzz_start_time
            self.buzz_high = True
            self.buzzer.value(1)

    def update(self):
        """Call this frequently (e.g., every 10-50ms) to handle timing."""
        if not self.is_active:
            return
        
        last_time = time.ticks_ms()
        
        if time.ticks_diff(last_time, self.last_toggle_time) >= self.step_duration_ms:
            self.current_step += 1
            
            if self.current_step >= 4:
                self.is_active = False
                self.buzzer.value(0)
            else:
                if self.buzz_high:  
                    self.buzzer.value(1)
                else:
                    self.buzzer.value(0)
            self.last_toggle_time = last_time

    def is_buzzing(self):
        return self.is_active
