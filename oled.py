# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 10, 2026
# Filename: oled.py
# Description: The Oled class contained in oled.py responds to IR input logic trees in ir_controller.py,
#              updating the display accordingly. Furthermore, logic in the seizure_detector.py class
#              can lock the screen when a seizure is triggered.
#
#              All of the functions within oled.py serve as general actions to be commanded to the display,
#              generally accessed by outside classes to trigger logic based on input or status changes.
#              The functions outlined within the Oled class allow for the display to draw three primary menus,
#              a seizure lock page, log viewer page, a sleep page, and intermediary screens to select / modify options.
#
#              So functionally the Oled class provides exterior functions all the necessary tools to display
#              all necessary menus, while outside modules such as ir_controller.py organize input logic to
#              cohesively string together Oled class functions into a functional user interface.
# ==========================================

#required inputs to interface with ssd1306
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time #used to pause screens
import config

#setting up display over i2c connection
i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=400000)
dsp = SSD1306_I2C(128,64,i2c)

numpad = config.numpad #config holds numpad dictionary

class Oled:
    
    """
    """
    def __init__(self, buzzer, gps, logger):
#initialize necessary variables
        self.x_left = 0.0 #set display x to full size 0 -> 127
        self.x_right = 127.0
        self.y_top = 0.0 #set display y to full size 0 -> 63
        self.y_bottom = 63.0
        self.page = 0 #set initial page to main screen (0)
        self.select = 0 #set initial sel to main sel (0)
        self.page_change = False
        self.lock = False #screen should start unlocked        
        self.code_in = "" #code buffer begins blank
        self.code = config.code #config holds initial security code
        self.timer = None
        
#initialize modules
        self.gps = gps
        self.logger = logger
        self.display = dsp
        self.buzzer = buzzer
        
        self.redraw_menu() #draw initial menu
            
    def redraw_menu(self):
        """
        redraw_menu serves as the general decision tree regarding what should be drawn based on which page has been rendered.
        
        page key:
        
        -2 -> change code menu
        -1 -> draw settings menu
        0 -> home
        1 -> gps config
        2 -> seizure alert
        4 -> draw seizure log selection menu
        5 -> draw the viewer of seizure logs
        
        only page 5 doesn't have the draw_select, as draw select is reserved for selecting multiple things with the up / down inputs,
        and page 5 uses those inputs for scrolling up and down the list of seizure logs for a given day.
        """
#refer to key or documentation for behavior
        if self.page != 5:
            self.draw_select() #draw_select on every page except 5
        if self.page == 0:
            self.draw_main_menu()
        elif self.page == 1:
            self.draw_right_menu()
        elif self.page == 2: 
            self.draw_seizure_alert()
        elif self.page == -1:
            self.draw_left_menu()
        elif self.page == -2:
            self.draw_change_code_menu()
        elif self.page == 4:
            self.draw_seizure_logs()
        elif self.page == 5:
            self.draw_seizure_log_viewer()
            

    
    def draw_main_menu(self):
        """
        Draws the main menu, setting page to 0, and only drawing the time / date if the time / date has been set by the GPS.
        Also, if date / time have been set by the GPS, view logs will be viewable and the user will be able to select that option.
        Otherwise, if the GPS has not determined a time / date, the user is simply notified that the GPS is offline.
        """
        
        self.page = 0 #set page to 0
        self.timer = time.ticks_ms()
#if gps has time/date, draw according menu
        if self.gps.time and self.gps.date:
            self.display.text(self.gps.current_time(), 0, 0)
            self.display.text(self.gps.current_date(), 0, 10)
            self.display.text("View logs", 0, 30)
            self.display.text("_", 115, 34)
            print(self.gps.current_time())
#if gps does not have time/date, notify user GPS is offline
        elif self.gps.time == None or self.gps.date == None:
            self.display.text("GPS offline", 0, 0)        
#show either option
        self.show()
        

    def draw_right_menu(self):
        """
        Draws the right menu, setting page to 1, drawing the page title, gps config.
        User is shown GPS status as well as lat / lon if the GPS has a fix.
        If the gps has no fix, tell the user the GPS is offline.
        
        Provide the user an option to refresh the GPS regardless of its state.
        """
        
        self.page = 1 #set page to 1
        self.display.text("gps config", 0,0) #draw page title
#if gps online, tell the user their position
        if self.gps.fix == True and self.gps.lat and self.gps.lon:
            self.display.text("gps connected", 0, 10)
            self.display.text("lat: ", 0, 40)
            self.display.text(str(self.gps.lat), 40, 40)
            self.display.text("lon: ", 0, 50)
            self.display.text(str(self.gps.lon), 40, 50)
#if gps offline, tell the user
        elif self.gps.fix == False:
            self.display.text("gps offline", 0, 10)
#present the option to refresh the gps regardless of state
        self.display.text("refresh gps", 0, 20)
        self.display.text("_", 115, 23)
        self.show()
        

        
    def draw_left_menu(self):
        """
            Draws the right menu, setting the page to -1 as well as the title "settings".
            present the user with the options to toggle the buzzer on / off and change the security PIN.
            
            This menu differs from the right and main menu in the sense that a fill rect is used to
            redraw the screen. This is crucial, as without it, toggling the buzzer would result in
            the 'on' / 'off' text overlapping. This is a non issue for the other menus, but a crucial distinction
            here.
            
            conditionals display the buzzer state, and the user is able to see the option prompting them to change their
            security code / PIN.
        """
        
        self.display.fill_rect(30, 10, 50, 64, 0) #key display refresh. If the user toggles the state of the buzzer, display must be wiped and redrawn to prevent text overlap
        self.page = -1 #set page to -1
        self.display.text("Settings", 0,0) #show title
#show buzzer state to user depending on the Buzzer class instance's inherent state
        if self.buzzer.state == True:
            self.display.text("buzzer on", 0,10)
        elif self.buzzer.state == False:
            self.display.text("buzzer off", 0, 10)
#provide user the option to change their security PIN
        self.display.text("change code", 0,20)
#draw selectable option prompts
        self.display.text("_", 115, 13)
        self.display.text("_", 115, 23)
        self.show()
        

    
    def draw_refresh_gps(self):
        """
        If the user chooses to refresh the gps, the display wipes and quickly replaced by a loading screen.
        The GPS module's find_coords() function is called to attempt to update its values.
        
        If a GPS fix is found, then the user is met with the notification that a signal was found, and the values
        are updated in the GPS module instance's internal values.
        
        If a GPS fix is not found, then the user is notified that a signal was not found.
        
        Either notification screen is drawn for two seconds before returning to the right_menu (gps config) page,
        where, if the GPS found a fix, the lat lon values should be immediately redrawn and shown to the user.
        
        """
        
        self.display.fill(0) #wipe display
#loading screen
        self.display.text("refreshing gps", 0, 0)
        self.display.text("loading", 60, 32)
        self.show()
#recalibrate GPS module values
        self.gps.find_coords()
#display notification depending on whether or not GPS found a fix
        self.display.fill(0)
        if self.gps.fix == True:
            self.display.text("gps signal found", 0, 30)
            time.sleep(2)
        elif self.gps.fix == False:
            self.display.text("gps signal not found", 0, 30)
            time.sleep(2)
#wipe display and redraw the right (gps config) menu
        self.display.fill(0)
        self.redraw_menu()
        

        
        
    def draw_seizure_alert(self):
        """
        Lock the display and alert the user to the fact that a seizure has been detected.
        User may enter the code / PIN to unlock the device
        
        Locking the display should mean the user is unable to navigate away from this page.
        """
        self.page = 2 #set page to 2
        self.lock = True #lock screen
        self.display.fill_rect(0, 40, 115, 64, 0) #wipe the code on refresh such that new code values can be drawn from accept_code()
        self.display.text("SEIZURE DETECTED", 0, 0) #notify user of seizure
        self.display.text("enter code to", 0, 10)
        self.display.text("disarm", 0, 20)
        self.accept_code() #accept code input
        self.show()
        
    def draw_change_code_menu(self):
        """
        Lock the display and allow the user to change the code. Accept code input and wipe
        the display every cycle such that if the code input changes, it is redrawn without
        drawing atop the previous code.
        
        Locking the display should mean the user is unable to navigate away from this page.
        """
        self.page = -2 #set page
        self.lock = True #lock screen
        self.display.fill_rect(0, 40, 115, 64, 0) #wipe code region of display
        self.display.text("new code: ", 0, 0)
        self.accept_code() #accept code input
        self.display.show()
        
    def draw_seizure_logs(self):
        """
        Draws input screen where user can select a date to see seizure records from that date.
        Screen is locked, and the user's input is neatly displayed to them.
        Locking the display should mean the user is unable to navigate away from this page.
        """
        self.page = 4
        self.select = 0
        self.lock = True
        self.display.fill(0)
        self.display.text("Enter MM:DD:YY: ", 0, 0)
        self.display.text(self.code_in[0:2] + " " + self.code_in[2:4] + " " + self.code_in[4:6], 30, 30)
        self.display.text("__:__:__", 30, 33)
        self.display.show()
        
    def draw_seizure_log_viewer(self):
        self.display.fill(0)
        try:
            seizure_archive = self.logger.get_log_from_file(self.code_in).splitlines()
            print(len(self.code_in))
            print('sz', seizure_archive)
            for i in range(self.select, len(seizure_archive)):
                self.display.text(seizure_archive[i], 0, (i-self.select)*10)
            self.show()
        except:
            self.display.text("no seizures", 0, 0)
            self.display.text(f"on {self.code_in}", 0, 10)
            self.display.text("returning to", 0, 30)
            self.display.text("main menu...", 0, 40)
            self.show()
            time.sleep(2)
            self.display.fill(0)
            self.code_in = ""
            self.lock = False
            self.draw_main_menu()
            self.redraw_menu()
            
        

    
    def accept_date_in(self, input):
        days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if input in numpad and len(self.code_in) <= 6:
            next_in = self.code_in + str(numpad[input])
            if len(next_in) <= 2:
                if int(next_in) <= 12:
                    self.code_in = next_in
                else:
                    return
            elif len(next_in) <= 4:
                if int(next_in[:-2]) <= days[int(next_in[0:2])-1]:
                    self.code_in = next_in
                else:
                    return
            elif len(next_in) <= 6:
                if next_in[4:6] <= self.gps.date.split("/")[2][2:4]:
                    self.code_in = next_in
                else:
                    return
        elif input == "0x00ff9867" and len(self.code_in) > 0:
            self.code_in = self.code_in[:-1]
        
        if len(self.code_in) == 6:
            self.code_in = self.code_in[0:2] + '/' + self.code_in[2:4] + '/' + self.code_in[4:6]
            print('it0', self.code_in)
            if '/0' in self.code_in:
                self.code_in = self.code_in.replace('/0', '/')
                print('it1', self.code_in)
            if self.code_in[0] == '0':
                print('it2', self.code_in)
                self.code_in = self.code_in[1:]
                print('it3', self.code_in)
            self.display.fill(0)
            self.show()
            self.display.fill(0)
            self.page = 5
    
        print(self.code_in)
        self.redraw_menu()
        
    def accept_code_in(self, input):
        
        if input in numpad and len(self.code_in) < 4:
            self.code_in += str(numpad[input])
        elif input == "0x00ff9867" and len(self.code_in) > 0:
            self.code_in = self.code_in[:-1]
        if len(self.code_in) == 4:
            self.display.fill(0)
            self.code = self.code_in
            self.code_in = ""
            self.display.text("code changed", 0, 0)
            self.display.text("to: ", 0, 10)
            self.display.text(self.code, 0, 30)
            self.show()
            time.sleep(2)
            self.display.fill(0)
            self.lock = False
            self.page = 0


        self.redraw_menu()
        
        
        
    def unlock_seizure_screen(self, input):
        if input in numpad and len(self.code_in) < 4:
            self.code_in += str(numpad[input])
        elif input == "0x00ff9867" and len(self.code_in) > 0:
            self.code_in = self.code_in[:-1]
        if self.code_in == self.code:
            self.lock = False
            self.page = 0
            self.display.fill(0)
            self.code_in = ""
        self.redraw_menu()
        

        
    def accept_code(self):
        self.display.text("_ _ _ _", 0, 42)
        self.display.text(" ".join(self.code_in), 0, 40)
        
        
    def trigger_seizure_warning(self):
        self.display.text("!!", 120, 50)
        self.display.show()
    
    def show(self):
        self.display.show()
        
    def unlock(self):
        self.lock = False
        self.code_in = ""
    
    def draw_select(self):
        if self.select <= 0 or self.select >= 5:
            self.select = 0
        self.display.fill_rect(115, 0, 9, 64, 0)
        if self.page_change == True:
            self.display.fill(0)
            self.select = 0
            self.page_change = False
        self.display.text("*", 115, self.select * 11)
        self.show()
        
    def boot(self):
        self.draw_main_menu()
        self.show()
        
        

        

    

