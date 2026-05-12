# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 11, 2026
# Filename: seizure_detector.py
# Description: Using the continuous stream of xyz buffer accelerometer data and the goertzel algorithms,
#              seizure_detector.py merges all of this logic into a single class for determining
#              whether or not a seizure has occured.
#
#              The general metholology for determining whether or not a seizure has occured is
#              based upon prior work of the open source community as well as general academic research
#              into the study of wearables for seizure detection. References are available in the README.md
#
#              This procedure follows three primary steps:
#              1) feed xyz buffer data into two seperate goertzel algorithms - one measuring the seizure
#              frequency band, and the other measuring the non-seizure frequency band. Record these values
#              as power values for seizure and non-seizure motion.
#              2) compare the strength of these two frequencies to determine which frequency band dominates.
#              if the seizure frequency band dominates the non-seizure frequency band by a very large margin (70-90%),
#              then flag that a seizure has been potentially detected.
#              3) repeat this process ten times over five seconds. if a seizure is flagged every single check over the five
#              seconds, then lock the screen, notify the server, force the system to beep, await a user code entry
#              to unlock the device, and write to the device's storage this seizure event.
#
#              This file serves as a crucial step in this process, as it analyzes the given frequency data, determining whether or not a seizure
#              has occurred over those ten cycles, prompting other devices to respond accordingly.
#
#              It is worth understanding that this seizure analysis with the Goertzel algorithm is initiated by the main loop in main.py,
#              but exectued on thread 1, as the Goertzel analysis of this many frequencies takes nearly half a second.
#
#              Furthermore, the server logic is also initiated by this file on the second core, so as not to disrupt the data collection or other
#              processes in the main loop when a user requests information from the server. 
# ==========================================

import goertzel #allows goertzel analysis of MPU sensor data from main.py
import _thread #for performing Goertzel and running the server on the second core
import time #maintaining steady time on the thread worker
import server #for starting a server instance
class SeizureDetector:
    
    """
    seizure_detector.py is partially untrue to its name, as it simultaneously serves as the manager of the server
    as well as the arbiter of seizure detection logic. The filename remains seizure_detector though, largely because
    the seizure detector itself serves as the dispatcher and manager of the server, and because the majority of the code
    is related to seizure detection.
    
    This design philosophy was decided on because the seizure_detector itself primairly exectues code on thread 1,
    while the main loop and general display logic runs on thread 0. Considering that thread 0 requires its while loop
    to execute consistently within small 20ms iterations, running a server which can interact with a client is simply
    not realistic within the main thread 0 loop. To remedy this, the server itself is written as a state machine which
    runs within the core2_worker, where core2_worker itself is functionally a state machine which either serves server requests
    or runs the multi-axis goertzel algorithms depending on whether the main loop (core 1 / thread 0) has decided 1/2 second has passed
    and it is time to run through the goertzel algorithm.
    
    So functionally, seizure_detector.py and the SeizureDetector class serve as the primary manager of logic on thread 2,
    although the bulk of code within the class itself is dedicated to seizure detection logic.
    """
    
    def __init__(self, display, buzzer, logger):
#variable declarations
        self.seize_count = 0 #the amount of seizures the device has detected this lifecycle
        self.seizing = False #a flag to determine whether the device has flagged a seizure
        self.warning = False #a flag to determine whether a seizure is about to be flagged
        #input_x,y,z variables which allow the input xyz buffer variables to be shared between core 1 and 2
        self.input_x = None 
        self.input_y = None
        self.input_z = None
        self.seizure_power = 0.0 #power recorded in the seizure band of frequencies
        self.total_power = 0.0 #power recorded in all frequency
        self.safe_power = 0.0 #power recorded in the safe band of frequencies
        self.run_goertzel = False #a flag used to command core 2 to crunch goertzel numbers
#class declarations
        self.display = display #oled display
        self.buzzer = buzzer #buzzer
        self.logger = logger #seizure_logger
        self.web_server = server.WebServer(self.display.gps, self) #web server instantiation
        self.web_server.start() #start web server
#safely attempt to begin a new thread
        try:
            _thread.start_new_thread(self.core2_worker, ())
            print("Worker thread started")
        except Exception as e:
            print(f"Failed to start worker: {e}")
            
    """
    Initializes the general variables required for seizure detection.
    
    Starts and turns on the web server.
    """
        
    @micropython.native
    def analyze(self, x_b, y_b, z_b):
#xyz buffer values are placed into the shared memory values of self.input_x,y,z such that core 1 and 2 processes can both access the data
        self.input_x = x_b
        self.input_y = y_b
        self.input_z = z_b
        self.run_goertzel = True #shared memory flag tells core2_worker to run a goertzel analysis
        
#if seizure_power is very large and overrepresented, flag it
        if self.seizure_power != None:
            if self.seizure_power >= 1000 and self.seizure_power / self.total_power >= 0.5:
                self.seize_count += 1
                print(self.seize_count)
                
    #if seize count has breanched seizure threshold, lock device and notify via buzzer and network
                if self.seize_count == 10:
                    self.display.code_in = "" #code_in is used by multiple variables, and is key to unlocking the seizure screen. must ensure it is blank.
                    self.display.display.fill(0) #wipe the display before the seizure lock screen is set on OLED
                    self.display.draw_seizure_alert() #draw seizure lock screen on OLED
                    self.buzzer.trigger() #activate buzzer, alarming nearby people
                    self.logger.log_seizure_event() #write to the local storage that this seizure event occured
                    self.web_server.send_seizure_alert() #notify mobile devices of seizure event via ntfy
                    self.seizing = True #set seizing flag to true, important for core2_worker
                    
    #if seize count is in the warning zone, trigger warning
                if self.seize_count > 5 and self.seize_count < 10: #if seize count for > 10 seconds
                    self.display.trigger_seizure_warning() #draws alert on display
                    self.warning = True 
                    self.buzzer.trigger()
#if seizure power is not large or not over represented, do nothing and redraw display / disable any warning
            else:
                self.seize_count = 0
                self.warning = False
                
    """
    The micropython native macro is used to slightly speed up the execution of the analyze function.
    
    The xyz buffer values are set to self.input_xyz values to create shared variables between cores 1 and 2
    
    The run goertzel flag is initially set to True such that the core 2 worker will begin running goertzel algorithms.
    In the meantime, goertzel will run for half a second, setting power values, such that the next iteration of analyze
    will have up-to-date power values. So, functionally, each analysis is roughly 1/2 second behind the true time, althugh this
    is generally a negligeble delay for the purpose of a seizure detector.
    
    Logic within analyze functionally analyzes the power values from the previous goertzel analysis, determinng if the ratio
    of power within the seizure band of frequenceis is large and significantly over represented in the total frequency of powers.
    
    If a seizure has been repeatedly flagged over ten successive iterations of the analyze function, the oled display is locked and forced into
    a seizure notification screen. Furthermore, the is_seizing flag is raised, pushing new logic to the web server (on core 2 in core2_worker) and sending a push notification
    via the web server module thrugh ntfy to mobile applicaitions on core 1.
    """
        
    def core2_worker(self):
#while True constantly runs on thread 1 / core 2
        while True:
            st = time.ticks_us()
            if self.run_goertzel != True:
                self.web_server.update()
            elif self.input_x != None and self.run_goertzel == True:
                self.seizure_power = goertzel.three_axis_goertzel(self.input_x, self.input_y, self.input_z, [0,1,2,3,4,5])        
                self.safe_power = goertzel.safe_three_axis_goertzel(self.input_x, self.input_y, self.input_z, [0,1,2])
                self.total_power = self.seizure_power + self.safe_power
                self.run_goertzel = False
                print('time for goertzel: ', time.ticks_us() - st)
            else:
                time.sleep_ms(100)
            self.buzzer.update()

                
                
    """
    core2_worker responds to server requests or alternatively runs goertzel analyses over safe and unsafe frequencies, but never does both.
    self.seizure_power/safe_power/total_power are updated for core 1 to scrutenize, as the variables occupy shared memory within the
    SeizureDetector class between cores 1 and 2 when a goertzel analysis is run.
    
    This architecture is necessary, as responding to a single web request takes 100ms to complete while a multi-band goertzel analysis takes 450-470ms.
    Offloading both of these functions to core 2 such that neither process runs together ensures that the 500ms (1/2 second) Goertzel analysis
    dispatches on core 1 maintain a steady rate.
    """











