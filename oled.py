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

#config holds numpad  / commands dictionaries
numpad = config.numpad 
commands = config.commands
days = config.days

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
        if self.buzzer.is_active == True:
            self.display.text("buzzer on", 0,10)
        elif self.buzzer.is_active == False:
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
        Screen is locked, and the user's input is neatly displayed to them, such that they may
        delete or enter an alternate date.
        
        Locking the display should mean the user is unable to navigate away from this page.
        """
        self.page = 4 #set page
        self.select = 0 #reset select, as it is not necessary to this page
        self.lock = True #lock screen
        self.display.fill(0) #clear screen
        self.display.text("Enter MM:DD:YY: ", 0, 0) #prompt input
        self.display.text(self.code_in[0:2] + " " + self.code_in[2:4] + " " + self.code_in[4:6], 30, 30) #make input appear to fit well on screen
        self.display.text("__:__:__", 30, 33) #input signifier
        self.display.show() #draw 
        
    def draw_seizure_log_viewer(self):
        """
        Draws the menu where users can see the list of seizures for a given date, stored in a date.txt file, as outlined
        in the seizure_logger.py file.
        
        Iniitially, the display is cleared, and remains locked from the prior draw_seizure_logs function, as this function
        should be called following that function.
        
        A try / except clause runs such that if seizure data is found for an inputted date, that data is extracted from the
        SeizureLogger module as a string and parsed / displayed neatly to the user in a scrollable vertical column.
        
        If the try / except fails and no seizures are found for a specific input date, the user is met with a 2 second transition screen
        informing them no seizures were found for that date, returning them to the main menu.
        """
        self.display.fill(0) #clear
#safely attempt to determine if a given input date has seizure logs
        try:
            seizure_archive = self.logger.get_log_from_file(self.code_in).splitlines() #split input data
    #for each seizure instance, draw it on its own line, using the current select value to scroll the entire aggregate up and down
            for i in range(self.select, len(seizure_archive)): 
                self.display.text(seizure_archive[i], 0, (i-self.select)*10)
            self.show() 
    #if no data found, inform the user and return to the main menu.
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
        """
        Allow the user to enter a date in MM DD YY format to search for seizure history for that given date.
        Limits are placed on what the user is allowed to enter, notably, the days array aggregates the days of
        each month from January to December, with the index of the array + 1 mapping 1:1 with each Month.
        
        The user is similarly not allowed to enter month values greter than twelve. The user is disallowed from
        certain inputs, as invalid inputs are simply blocked and not populated to the display.
        
        Single-digit day/month values are required to be prepended by a 0 before the user enters that single-digit value.
        
        Once the user has entered a valid date input, the screen automatically changes, as the page changes to 5, the
        menu where the user is able to either scroll through a list of past seizure isntances for that date, or they are met
        with a screen informing them that there are no seizure occurences for this date.
        """
        
#if user input is a valid numpad entry and the user input is less than its maximum input, check that input
        if input in numpad and len(self.code_in) <= 6:
            next_in = self.code_in + str(numpad[input])
    #if input is in the month section, ensure it is less than 12
            if len(next_in) <= 2:
                if int(next_in) <= 12:
                    self.code_in = next_in
                else:
                    return # if input is invalid in the day range, return exits the loop, where external logic should re-call the loop starting from the top, this exit, essentially does nothing, informing the user that their input is invalid
    #if input is is in the days section, ensure it's value is less than the maximum amount of days for that month
            elif len(next_in) <= 4:
            #slice strings to determine validity
                if int(next_in[:-2]) <= days[int(next_in[0:2])-1]:
                    self.code_in = next_in
                else:
                    return #return to exit loop, demonstrates invalid input
    #if input is in the year section, parse the input
            elif len(next_in) <= 6:
                if next_in[4:6] <= self.gps.date.split("/")[2][2:4]:
                    self.code_in = next_in
                else:
                    return
#if input is the delete button and there is a value to delete, then delete the last value.
        elif input == commands["delete"] and len(self.code_in) > 0:
            self.code_in = self.code_in[:-1]
#if input is valid (max length), enter slashes such that it meets MM/DD/YY
        if len(self.code_in) == 6:
            self.code_in = self.code_in[0:2] + '/' + self.code_in[2:4] + '/' + self.code_in[4:6] #properly place input in MM/DD/YY format
    #Remove the leading 0s from any single-digit days / months (cleaning the input for file writing / reading)
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
            self.page = 5 #move to page 5, the log viewer
    
        self.redraw_menu() #redraw at page 5
        
    def accept_code_in(self, input):
        
        """
        User may enter 4-digit code/pin when this function is called repeatedly.
        
        If the code buffer (self.code_in) receives a valid input, as long as its length is < 4,
        append the input to the code input buffer.
        
        If the input is to delete, then don't append anything and simply delete the most recent entry so long as there
        is something to delete.
        
        After input is received simply redraw the menu such that valid input can be drawn to the screen.
        
        This function operates almost identically to accept_date_in, except it is much simpler as it does not
        require valid date checks.
        """
        
#if input is valid and buffer has not been filled, append input to bufer
        if input in numpad and len(self.code_in) < 4:
            self.code_in += str(numpad[input])
#otherwise, if input is to delete, delete most recent input to the buffer
        elif input == commands["delete"] and len(self.code_in) > 0:
            self.code_in = self.code_in[:-1]
#if the max length of valid inputs has been reached, then replace the current code with the new code.
        if len(self.code_in) == 4:
            self.display.fill(0)
            self.code = self.code_in #replacing old code
            self.code_in = "" #refreshing buffer to zero, so that the next cycle works with a clean buffer
            self.display.text("code changed", 0, 0) #notify user the code has been changed and return to main menu
            self.display.text("to: ", 0, 10)
            self.display.text(self.code, 0, 30)
            self.show()
            time.sleep(2)
            self.display.fill(0)
            self.lock = False
            self.page = 0


        self.redraw_menu()
        
        
        
    def unlock_seizure_screen(self, input):
        """
        Given an input, if that input is equal to the set code / PIN, unlock the seizure screen and return the user to the main menu.
        """
#if valid input, append to code buffer
        if input in numpad and len(self.code_in) < 4:
            self.code_in += str(numpad[input])
#if delete input, delete if vlaid
        elif input == commands["delete"] and len(self.code_in) > 0:
            self.code_in = self.code_in[:-1]
#if code is valid, unlock screen
        if self.code_in == self.code:
            self.lock = False
            self.page = 0
            self.display.fill(0)
            self.code_in = ""
        self.redraw_menu()
        


    def accept_code(self):
        """
        Function used in places where a 4-digit code must be accepted, simply takes the code buffer and
        places it overtop underscores denoting the input.
        """
        self.display.text("_ _ _ _", 0, 42) #placeholder values
        self.display.text(" ".join(self.code_in), 0, 40) #buffer values
        
        
    def trigger_seizure_warning(self):
        """
        To be used within the SeizureDetecor class when a seizure warning must be issued.
        Displays !! in the bottom right corner of the screen denoting a warning
        """
        self.display.text("!!", 120, 50) #display "!!"
        self.display.show()
    
    def show(self):
        """
        Simplified version of self.display.show(), allows for easier calling from outside functions,
        such that an outside function can simply can self.display.show() rather than self.display.display.show()
        
        Also makes pushing to the display clearer within the Oled class, as a user can simply type self.show()
        """
        self.display.show() #show
        
    
    def draw_select(self):
        """
        Draw select function draws the selector icon '*', moving its position in response to changes in the self.select value.
        This function is expected to respond to changes in self.select made from the IRController class, as inputs there should
        modify the self.select value, moving the selector icon up and down when that input is passed to this function.
        
        Safety checks prevent the icon from being drawn out of the screen's bounds.
        
        If the page changes, the select value is automatically reset, forcing the selector back to its default 0 position at
        the top of the screen.
        """
#if sel is being told to go out of bounds prevent that
        if self.select <= 0 or self.select >= 5:
            self.select = 0
        self.display.fill_rect(115, 0, 9, 64, 0) #wipe only the select area of the screen on redraw
        if self.page_change == True:
            self.display.fill(0)
            self.select = 0
            self.page_change = False
        self.display.text("*", 115, self.select * 11) #draw * icon according to select value
        self.show()
        
    def boot(self):
        """
        Boot function draws the main menu
        """
        self.draw_main_menu()
        self.show()
        
        

        

    


