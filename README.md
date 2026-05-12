#ECE 296 Seizure Detector

##Elevator Pitch
This project is a wearable seizure detection device which uses a complex frequency analysis given multi-axis accelerometer data over ten seconds. The device has a complex user interface on the OLED display, controllable by an IR remote, as well as mobile notifications, a local web server, and onboard buzzer to notify others when a seizure occurs. Seizure logs are stored and an onboard GPS module tracks time and position, while users are also able to view previous seizure archives.

##Project Overview
Using the Raspberry Pi Pico W, the SunFounder Kit for the Raspberry Pi Pico W, an OLED display, and GPS module, this project serves as a wearable seizure detection and logging system. Using the MPU6050 tri-axis accelerometer included in the SunFounder Kit, xyz motion data is captured at a rate of 50hz over a period of ten seconds. This data is analyzed using a Goertzel Discrete Fourier Transform to isolate and compare the strength of seizure band frequencies and non-seizure band frequencies. Fourier Transforms are the medical gold standard for non-ECG wearable devices within academia as well as open-source settings. The typical band of physical motion frequencies during a seizure tends to be roughly 3 - 8Hz. OpenSeizureDetector uses this frequency band, while other grand mal seizure frequency analyses have settled on 5-6 Hz. A Goertzel DFT is applied to the seizure frequency band as well as non-seizure frequencies (0.5-2Hz), and the strength between bands is compared. If the seizure band is exceedingly overrepresented in the data by a margin of 94%, a seizure is flagged, and a notification is sent to mobile devices connected via NTFY, while the device physically alerts nearby people with a Buzzer and a local web server update.

While this device is primarily a seizure detection device based on the modern principles set forth by OpenSeizureDetector and modern research, the device also largely serves as a cohesive and interactive wearable, with a complex user interface and a wealth of configurable options. Notably, there are three main menus for the user to navigate once the device boots, a home page displaying time, date, and allowing the viewing of seizure logs, a settings page where users may configure options with the device, and a GPS configuration page where users may refresh the GPS’ location. Each of these menus and their options integrates complex logic trees and the focused integration of multiple classes. Multiple sub menus and dedicated functions exist serving the sole purpose of presenting a clean user interface while providing meaningful utility. 

In order for the user to view the current time and date, as well as for seizure logs to be written properly, the GPS module must be initialized, as time and date are parsed only by the GPS. UTC is converted to local time based on a customizable UTC_CONFIG constant within the config.py file. Time and date are necessary for seizure logs to be written, as the way in which seizure logs are organized is directly via time and date, where a file is stored on the device names “MM/DD/YY.txt” with time entries indicating prior seizure events. The user may repeatedly refresh the GPS module within the GPS config page / right menu by selecting the “refresh GPS” option. Should the GPS ascertain proper time, date, and location values, the time / date will appear on the home menu. 

Once a seizure has been triggered, a locked seizure screen will appear alongside a loud beeping noise. The user must enter a predetermined code in order to disable this screen. The user is also provided an option to customize and change this code within the settings page. A web server is consistently run on the second core of the Pico W alongside the Goertzel analyses. This web server will update its status to reflect that the wearer is currently having a seizure. Also, though the WebServer class, a notification is sent through the NTFY application to mobile phones opted into this project whenever a user has a seizure. This allows for meaningful application of this project, as caregivers or relatives can quickly be made aware of a grand mal seizure as well as where this seizure has occurred. 

The way in which the display is controlled is a particularly standout aspect of this project, as, custom IR Sensor logic was implemented to use the onboard Pico W state machines to continuously wait for and detect user input. This was decided on as the standard IR library was unsuitable for this project as inputs were often not registered, and code blocking appeared necessary to properly capture inputs. By offloading this logic from both cores to the onboard state machine, the Pico W itself can continuously loop through its work uninterrupted on the primary and secondary cores. 

##Hardware Components
 - Raspberry Pi Pico W
 - MPU6050 (Included in SunFounder Kit) - xyz motion data collector
 - SSD1306 OLED Display - User Interface
 - Infrared Receiver (SunFounder Kit or ___) - 
 - NEO-6M GPS Module - location and time
 - Buzzer (SunFounder Kit)
 - Breadboard (SunFounder Kit)
 - 4x long SunFounder Kit green wires
 - 4x long SunFounder Kit white wires
 - 6x short SunFounder Kit green wires
 - 6x short SunFounder Kit yellow wires
 - 1x short SunFounder Kit blue wire
 - some way to secure the Breadboard and components to the forearm, I used generic sticky velcro available at most craft stores.

##Breadboard layout / wiring

##System Architecture Overview

General System Overview:

The most high level overview of this device’s logic-flow is captured []. Once the device is powered on, each individual component is initialized in main.py beginning with the MPU6050, followed by the GPS, SeizureLogger, Buzzer, OLED, SeizureDetector, and the IRController. Also, the xyz motion buffers are initialized in this first pass, filled with 0 values. Once each physical component on the board has been activated and each necessary class has been instantiated, the initial iteration of the main loop begins, a timer is started and data sampling begins. The timer itself ensures that the loop runs steadily at 20ms per iteration, as the sample rate for data collection is 50Hz, or 50 samples / second. The first iteration of the main loop also begins the FSM PIO IR detector, allowing input. With each pass within the main loop, the output of this PIO is analyzed by the IRController, which sends corresponding commands to the OLED display. Furthermore, every 25 cycles of the main loop (0.5 seconds), a Goertzel analysis of the current xyz frequency buffers is called. This data is passed into the SeizureDetector class, which runs the Goertzel analyses on the second core and determines whether a seizure is occurring or not. So, while the fundamental loops running within cores 1 and 2 are strictly isolated, the data is often shared between the cores and the overall system requires the cohesive mix of processes running on both cores in order to achieve this outcome.

Core 1:

The core 1 loop is better illustrated in []. Breaking down that logic into words, the core 1 loop functionally repeats the same exact tasks each iteration of its cycle. The iteration begins by starting an internal timer counted in milliseconds. Then, it determines if the buffer_index (the value incremented each cycle to fill one new value per 20ms into each xyz buffer at the appropriate index) is full or not. If the value is full, the buffer index is reset to zero such that the next values are placed at the starting points of their respective buffers. The internal measure function is then called, filling one data point each into the xyz motion buffers. After this, the IRController is passed the most recent input from the PIO FSM and is allowed to make any necessary changes to the OLED display given the internal logic structure of the IRController class. Then, the OLED is updated in some way by the IRController’s internal logic. At this point if the current iteration is divisible by 25, that means 25 cycles have passed since the past cycle was divisible by 25. In other words, 25 20ms cycles have passed = 500ms = 0.5 seconds. So, core 1 calls the SeizureDetector class instance’s analyze() function, which spawns a Goertzel analysis on the second core. Then, finally the buffer index is incremented by one, and the loop checks if 20ms have elapsed since the start time. If 20ms have not passed, then the loop sleeps until exactly 20ms have passed. This loop is repeated infinitely throughout the device’s lifecycle, with the only changes in logic occurring based upon the user’s input to the IRController. Refer to the IRController system architecture for more information.


Core 2:



##Challenges Solved

##What I Learned





























