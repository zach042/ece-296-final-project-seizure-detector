# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 10, 2026
# Filename: main.py
# Description: buzzer.py contains the Buzzer class, a simple class which interfaces with the onboard buzzer
#              from the SunFounder kit via GPIO Pin 18. The buzzer itself creates a loud, high pitched noise
#              when triggered.
#              The buzzer class itself has multiple status variables determining whether the buzzer is active,
#              how long a buzzer step occurs for, and timer functionality.
# ==========================================

#necessary imports
import time
import machine

class Buzzer:
    def __init__(self, pin_id=18):
        self.buzzer = machine.Pin(pin_id, machine.Pin.OUT) #initializes connection between Pi and buzzer over pin 8
        self.is_active = True
        self.buzz_start_time = 0
        self.buzzing = False
        self.last_toggle_time = 0

    def trigger(self):
        """
        Immediately triggers the buzzer sequence, setting the buzzer value to 1, sending power to the alarm.
        The time is the reset each trigger such that the total duration of the buzzing can be controlled by outside functions.
        buzzing is set to true, informing outside functions that the buzzer is currently buzzing.
        """
        if self.buzzing == False and self.is_active:
            self.buzzing = True
            self.buzz_start_time = time.ticks_ms()
            self.last_toggle_time = self.buzz_start_time
            self.buzzer.value(1)

    def update(self):
        """
        This function serves as a timing control for the buzzer, to ensure that triggers last for finite times
        rather than infinitely supplying power to the buzzer.
        
        This function can be run regardless of whether or not the buzzer has previously been triggered, as it
        uses the buzzing flag to determine whether or not the buzzer is currently active. If the buzzer is active,
        then timing control is applied using the timer value. Both of these values are set during a buzzer trigger
        in the trigger function.
        
        So functionally, this update function serves as a control to the toggle function, ensuring buzzer beeps last
        for short controlled times.
        """
        if not self.is_active:
            return
        
        last_time = time.ticks_ms()
        
        if self.buzzing:
            
            if last_time - self.buzz_start_time > 10000:
                self.buzzing = False
                self.buzzer.value(0)
            else:
                self.buzzer.value(1)
            self.last_toggle_time = last_time

        else:
            self.buzzer.value(0)
                



