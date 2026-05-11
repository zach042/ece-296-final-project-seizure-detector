# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 10, 2026
# Filename: ir_controller.py
# Description: This file contains the IRController class, used to manage and command actions
#              to the system and display given infrared controller input.
#              multiple functions work together with the OLED display and other classes to
#              efficiently and elegantly allow the user to disable / enable the buzzer,
#              place the display in sleep mode, customize their device PIN, view previous seizures,
#              and recalibrate the GPS.
#              The functions within the IRController class largely serve as methods for the IR input to
#              interface with the OLED display, but also work together with state variables from the OLED
#              display such as 'page' to determine what to show the user given an IR input.
# ==========================================

import time #time is a necessary library, allowing for complex timers and sleep logic
from machine import Pin #pin is required to initialize the device connection with the Pico W.
from ir_rx.nec import NEC_8 #
from ir_rx.print_error import print_error #
import oled #
from pio_ir_rx import PIO_IR_NEC
import config #config contains the numpad and commands IR dictionaries

numpad = config.numpad
commands = config.commands

"""
IR
"""
class IRController:
    
    def __init__(self, display, detector):
        self.display = display
        self.input = None
        self.input_received = False
        self.device = PIO_IR_NEC(pin=19)
        self.code = '1234'
        self.detector = detector
        

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
                self.exit_and_sleep_menus()
                self.display.accept_code_in(self.input)
            elif self.display.lock == True and self.display.page == 4:
                self.exit_and_sleep_menus()
                self.display.accept_date_in(self.input)
            elif self.display.lock == True and self.display.page == 5:
                self.command_oled()
        elif self.display.page == 0 and (time.ticks_ms() - self.display.timer) > 1000:
            self.display.timer = time.ticks_ms()
            self.display.display.fill_rect(0, 0, 110, 64, 0)
            self.display.draw_main_menu()
            self.display.show()
            self.detector.seizing = False
            
            
    def exit_and_sleep_menus(self):
        if self.input == commands["exit"] and self.display.page in [-2, 4, 5]:
            print('EXITING')
            self.display.lock = False
            self.display.display.fill(0)
            self.display.draw_main_menu()
        elif self.input == commands["exit"] and self.display.page in [-1,0,1]:
            self.display.display.fill(0)
            self.display.display.text('entering sleep', 0, 0)
            self.display.display.text('mode', 0, 10)
            self.display.show()
            time.sleep(2)
            self.display.page = 6
            self.display.display.fill(0)
            self.display.show()
        elif self.input == commands["exit"] and self.display.page == 6:
            print('waking up')
            self.display.page = 0
            self.display.redraw_menu()
    
    def command_oled(self):
        self.exit_and_sleep_menus()
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
                if self.display.select == 3 and self.display.gps.date and self.display.gps.time:
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

    
    def reset(self):
        self.input_received = False
    
    
        

