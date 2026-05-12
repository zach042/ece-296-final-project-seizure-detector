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

#imports
import time #time is a necessary library, allowing for complex timers and sleep logic
from machine import Pin #pin is required to initialize the device connection with the Pico W.
from ir_rx.nec import NEC_8 #
from ir_rx.print_error import print_error #
import oled #
from pio_ir_rx import PIO_IR_NEC
import config #config contains the numpad and commands IR dictionaries

#config values for inpts
numpad = config.numpad
commands = config.commands

class IRController:
    """
    IRController class recieves inputs from the onboard IR Module, determining what shall be done with them
    depending on the Oled display instance's current page and lock value.
    
    Logic expressed within the class organizes the Oled class instance's display functions into a cohesive
    User Experience, chaining multiple display functions together such that the user can navigate between pages,
    change device settings, deactivate the seizure alarm, view past seizure logs, and place the device in rest mode.
    """
    
    def __init__(self, display, detector):
#device / onbooard pin initialization
        self.device = PIO_IR_NEC(pin=19)
#local variable initialization
        self.input = None
#external class initialization
        self.display = display
        self.detector = detector
    
        """
        Initializes the onboard ir receiver module, local input variable, and external class instances
        for use within the module. Critically the display is defined within the scope of the class,
        allowing for complex display navigation given IR input.
        """
        

    def await_input(self):
        self.input = raw = self.device.read_raw() #read input from SFM device
#if the input is not none, translate it, and enter a decision tree regarding what shall be done if the device is locked.
        if raw is not None:
            self.input = f"{raw:#010x}"
            print(self.input)
            print(self.display.page)
#this is the general decision tree regarding what to do if the display is locked, the documenation outlines this tree.
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
#if the current screen is the home screen, redraw it every second to display current date / time.
        elif self.display.page == 0 and (time.ticks_ms() - self.display.timer) > 1000: #timer logic
            self.display.timer = time.ticks_ms() #increment timer
            self.display.display.fill_rect(0, 0, 110, 64, 0) #redraw everything except selection icons
            self.display.draw_main_menu() #redraw main menu after 1s
            self.display.show()
            self.detector.seizing = False #ensure seizing value is set to false, this is largely here because there isn't a great place to reset this elsewhere.
            
        """
        await_input block is designed to run each iteration, 20ms within the main block, and takes
        the non-blocking, always active listening input from the onboard SFM, and determines what should
        be done with that input.
        
        if the display is unlocked, the general command_oled() function is called, where a decision tree exists
        determining what to do with generic input.
        If the display is locked, then multiple potential behaviors should occur as follows
        
        display locked + seizure lock/unlock screen -> redraw seizure lock/unlock screen
        display locked + change code menu -> allow the user to input an exit menu command and then go to the generic command_oled() tree
        display locked + input date to view seizure logs screen -> allow the user to input an exit menu command and then allow date input
        display locked + currently viewing seizure logs -> command_oled()
        
        crucially, this page also has a one second timer, which redraws the home screen if the current screen being displayed is the home screen,
        every second, such that the time and date can be redrawn if changed automatically.
        
        """
            
    def exit_and_sleep_menus(self):
        """
        This function serves to handle the input of the power button on the IR remote control.
        In the commands dictionary, this button has been labeled 'exit', but it really serves as the
        sleep / exit button, exiting any menu apart from the seizure lock, and sleeping when on one
        of the three main menus.
        
        In practice, this function determines which page the display is currently on, if an exit or sleep
        (only one option) can occur, and then handles that command accordingly.
        
        Crucially, the button also serves as a power / wake button
        """
#if input is exit / sleep while on an exitable locked menu page, unlock that menu and return to the home screen
        if self.input == commands["exit"] and self.display.page in [-2, 4, 5]: #-2, 4, and 5 are the exitable locking menus
            print('EXITING')
            self.display.lock = False #disable the lock, so that the user can navigate when returning to home page.
            self.display.display.fill(0) #clear display
            self.display.draw_main_menu() #draw main menu
#if input is exit / sleep and the user is on one of the three main menus, put the device to sleep (page 6)
        elif self.input == commands["exit"] and self.display.page in [-1,0,1]:
            self.display.display.fill(0) #clear
            self.display.display.text('entering sleep', 0, 0) #notify the user the device is entering sleep mode.
            self.display.display.text('mode', 0, 10)
            self.display.show()
            time.sleep(2) #pause the notification screen for two seconds so the user knows device is entering sleep mode.
            self.display.page = 6 #set page to 6, the sleep screen.
            self.display.display.fill(0) #clear display so that screen is blank
            self.display.show()
#if input is exit / seep and display is 6, then wake the display
        elif self.input == commands["exit"] and self.display.page == 6:
            self.display.page = 0
            self.display.redraw_menu() #draw main menu
    
    def command_oled(self):
        
        """
        command_oled is the primary logic tree for Oled class instance changes on non-locking screens given IR input.
        
        the general structure is:
        
        page left: cycle infinitely left through the three main menu pages, in order.
        page right: cycle infinitely right through main menu pages, in order.
        sel_down: move the selector value down. This action modifies the Oled class' draw_select,
        visibly moving the selector icon down the page.
        sel_up: move the selector value up. This action modifies the Oled class' draw_select,
        visibly moving the selector icon up the page.
        
        The enter command exists in its own general logic tree, only processing a command if the select value aligns
        with an actionable select input.
        """
        
        self.exit_and_sleep_menus() #first, allow users to exit or sleep menus
        
#if the input is page left, cycle through pages depending on current page status
        if self.input == commands["page_left"]:
            self.display.page_change = True #trigger page change reset, forcing the Oled display reset logic
    #case based logic, properly setting next page based on the current page
            if self.display.page == 0:
                self.display.page = -1
                
            elif self.display.page == 1:
                self.display.page = 0
                
            elif self.display.page == -1:
                self.display.page = 1
                
            self.display.redraw_menu()

#if the input is page left, cycle through pages depending on current page status
        elif self.input == commands["page_right"]:
            self.display.page_change = True
    #case based logic, properly setting next page based on the current page
            if self.display.page == 0:
                self.display.page = 1
            
            elif self.display.page == 1:
                self.display.page = -1
                
            elif self.display.page == -1:
                self.display.page = 0 
                
            self.display.redraw_menu()
            
#if input is sel_down or sel_up, change the select value, triggering the Oled display to redraw the selector *
        elif self.input == commands["sel_down"]:
            self.display.select = self.display.select + 1
            self.display.redraw_menu()
        
        elif self.input == commands["sel_up"]:
            self.display.select = self.display.select - 1
            self.display.redraw_menu()
            
#if input is enter, a unique decision tree exists depending on which page is active as well as what the current select value is
        elif self.input == commands["enter"]:
    #if on home page and select is 3 and gps initialized, then allow user to view log files, pushing them to page 4 and redrawing the screen
            if self.display.page == 0:
                if self.display.select == 3 and self.display.gps.date and self.display.gps.time:
                    self.display.code_in = ""
                    self.display.page = 4 #4 is the page where users can input a date to see past seizures
                    self.display.display.fill(0)
                    self.display.accept_date_in(self.input)
    #if on settings / left page and selector is 1, allow user to toggle buzzer
            elif self.display.page == -1:
                if self.display.select == 1:
                    self.display.buzzer.is_active = not self.display.buzzer.is_active
        #if on settings and selector is 2, toggle change code menu
                elif self.display.select == 2:
                    self.display.code_in = ""
                    self.display.page = -2 #page 2 is change code menu
                    self.display.display.fill(0)
                    self.display.accept_code_in(self.input)
                    self.display.draw_change_code_menu()
    #if on gps config menu and selelct is 2, allow gps refresh
            elif self.display.page == 1:
                if self.display.select == 2:
                    self.display.draw_refresh_gps()

            self.display.redraw_menu() #regardless of input, redraw the menu
    
    
        

