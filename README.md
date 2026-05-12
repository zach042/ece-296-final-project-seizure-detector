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
 - SunFounder Kit Batter and Battery Holder

 ##Video demo
 ![Link text](https://www.youtube.com/watch?v=sAgPejwyLyU)

##Breadboard layout / wiring / circuit diagrams
Attached are three unique images of the project's wiring layout such that any person wishing to understand or recreate the project may do so easily given the way in which multiple photos reveal each connection between pins.
![Alt text](/images/circuit-diagrams/everything-connected.png)
![Alt text](/images/circuit-diagrams/modules-removed.png)
![Alt text](/images/circuit-diagrams/nothing-connected.png)



##System Architecture Overview

General System Overview:
![Alt text](/images/flowcharts/general-system-flow-chart.png)
The most high level overview of this device’s logic-flow is captured in the flow chart above. Once the device is powered on, each individual component is initialized in main.py beginning with the MPU6050, followed by the GPS, SeizureLogger, Buzzer, OLED, SeizureDetector, and the IRController. Also, the xyz motion buffers are initialized in this first pass, filled with 0 values. Once each physical component on the board has been activated and each necessary class has been instantiated, the initial iteration of the main loop begins, a timer is started and data sampling begins. The timer itself ensures that the loop runs steadily at 20ms per iteration, as the sample rate for data collection is 50Hz, or 50 samples / second. The first iteration of the main loop also begins the FSM PIO IR detector, allowing input. With each pass within the main loop, the output of this PIO is analyzed by the IRController, which sends corresponding commands to the OLED display. Furthermore, every 25 cycles of the main loop (0.5 seconds), a Goertzel analysis of the current xyz frequency buffers is called. This data is passed into the SeizureDetector class, which runs the Goertzel analyses on the second core and determines whether a seizure is occurring or not. So, while the fundamental loops running within cores 1 and 2 are strictly isolated, the data is often shared between the cores and the overall system requires the cohesive mix of processes running on both cores in order to achieve this outcome.

Core 1:
![Alt text](/images/flowcharts/core-1-flow-chart.png)
The core 1 loop is better illustrated in the flowchart listed above. Breaking down that logic into words, the core 1 loop functionally repeats the same exact tasks each iteration of its cycle. The iteration begins by starting an internal timer counted in milliseconds. Then, it determines if the buffer_index (the value incremented each cycle to fill one new value per 20ms into each xyz buffer at the appropriate index) is full or not. If the value is full, the buffer index is reset to zero such that the next values are placed at the starting points of their respective buffers. The internal measure function is then called, filling one data point each into the xyz motion buffers. After this, the IRController is passed the most recent input from the PIO FSM and is allowed to make any necessary changes to the OLED display given the internal logic structure of the IRController class. Then, the OLED is updated in some way by the IRController’s internal logic. At this point if the current iteration is divisible by 25, that means 25 cycles have passed since the past cycle was divisible by 25. In other words, 25 20ms cycles have passed = 500ms = 0.5 seconds. So, core 1 calls the SeizureDetector class instance’s analyze() function, which spawns a Goertzel analysis on the second core. Then, finally the buffer index is incremented by one, and the loop checks if 20ms have elapsed since the start time. If 20ms have not passed, then the loop sleeps until exactly 20ms have passed. This loop is repeated infinitely throughout the device’s lifecycle, with the only changes in logic occurring based upon the user’s input to the IRController. Refer to the IRController system architecture for more information.


Core 2:
![Alt text](/images/flowcharts/core-2-flow-chart.png)

The loop which is executed on the second core is generally far simpler than than core 1's loop, as it is generally only concerned with Goertzel analysis and running the server. This simplicity is necessary, as a Goertzel analysis often takes nearly half a second, while a server response a tenth of a second. Should either of theese have been implemented on the first core, the entire sampling logic and reliable data collection loop would fail to work entirely. 

The primary operation from this loop is as outlined in the flowchart and as follows: set an internal timer, although this is solely for debugging, then if the Goertzel flag is false, update the web server. If the flag is true, then run a Goertzel analysis, passing the values to the shared memory space class values within SeizureDetector, such that the aspects of the analyze() function which run on core 1 can properly determine whether a seizure has occured or not, and toggle devices initialized on core 1 accordingly. Then the buffer is updated at the end of the loop, and the loop cyccles back to the start. The timer may optionally be used to debug how long a Goertzel loop takes to ensure it fits within the 0.5 second required window. 


##Challenges Solved
Throughout this project, there are dozens of problems I solved, as fundamentally, the breadth of this project spans multiple domains with complex systems orchestration. The first challenge I solved was mentally organizing how interfacing with the OLED display would work. This was initially a very complicated challenge to me, as I am primarily experienced in writing functional Elixir code rather than object oriented code. However, I turned to my previous work in lab four on the pong game and drew inspiration from the way in which objects were continuously redrawn. I made things distinctly my own though, as I opted to stray from the hierarchial class nature of that lab and chose to keep the OLED class seperate from other classes while still allowing other classes to interface with the display. The most difficult aspect of initially deciding how I would orchestrate complex UI states was overwhelming, but I wrote out a rudamentary plan where there would be three main menus with system configuration and quick cycling between the menus with the IR controller. 

The first real challenge I actually solved with code was the seizure detection logic. Initially, I had an extremely complex system for handling xyz accelerometer values, as I accounted for gravity, eliminating it from the accelerometer readings using complex math. This was before I had even implemented a frequency analysis, published a GitHub Repo, or really gotten to serious work on the project. I quickly realized that gravity would always be a sort of constant within my calculations regardless of the orientation of the device, and quickly removed this implementation, replacing it with a simple measurement system that analyzes the pure xyz values. Furthermore, I realized that gravity really is a meaningless force in my Seizure Detection logic, as I had planned to isolate frequencies, meaning that the overall magnitude of one axis being greater or lesser than another axis was irrelevant because accelerometer magnitude values were not used anywhere in standard DFT analyses. This was solved later though, after I had figured out that the Goertzel Algorithm was ideal for my system. I've detailed this below.

Before I could even think about isolating frequencies, I had to consider how I would collect XYZ data. I decided that I would keep track of a list of values, and set my sights on a 50Hz sample rate, as I knew that in order to analyze a frequency, you must have sampled at double that frequency from ECE 260. I decided to store 10 seconds of 50Hz data, but really wasn't sure what the best way to do this on a microcontroller was considering its limited power and memory. Initially I used a list, but learned that the array module was much more efficient for this purpose, and decided to use that instead. I then drafted a simple xyz buffer solution where a while True loop continuosuly recoreded the XYZ accelerometer data in their own respective buffers.

The next real challenge I had to work through was figuring out what method I should use to isolate the strength of Seizure band frequencies. This first requried me to research what frequencies are generally considerede to be within the seizure band and which frequencies are not. I had to look through multiple reseaerch papers, and often got confused if the researchers were discussing ECG frequency or accelerometer frequency. Anyone attempting to recreate this project and reseaerch on their own time should ensure they too make this distinction while researching. I learned largely through YouTube videos that a primary way computer isolate frequencies is with a Full Fourier Transform, where all frequencies within a noisy signal are isolated and assigned strength values. I did more research and learned about Discrete Fourier Transforms, particularly, the Goertzel DFT, a commonly used Fourier Transform which allows one to isolate only a select batch of desired frequency strengths. I decided this was the perfect method because it would allow the Pico to analyze frequency strengths efficiently without having to spend time analyzing frequencies I was unconcerned with. 

Implementing the Goertzel algorithm in code was actually quite difficult, as the online resources were slimmer than I had expected. I based my initial iteration on the example listed on Wikipedia, and it appeared to work well enough, but was very slow, as I had started out running three seperate Goertzel equations, as I originally thought I needed to use one per axis. As I had tested an implementation of a multi frequency Goertzel, I learned that my implementation was simply too slow to analyze 3 seperate axes at once by Goertzel over multiple frequencies. In the process of reaching this point I had also solved many other minor issues such as whether or not I needed to use a circular buffer for frequency analysis and how I can better optimize the Goertzel algorithm generally.

Optimizing the Goertzel algorithm effectively proved to be one of the most beneficial choices I made during my project. The original multi frequency version was slow and ran on the same thread as all my other logic. The algorithnm itself was grossly inefficient, as coefficients were calculated during each Goertzel loop, I had unnecessary extra for loops, and had not properly settled on the best way to analyze all three axes at once. I even played with the idea of simply combining all three axes into one single magnitude and analyzing Goertzel on that before I realized that made frequency analysis impossible because I no longer had any negative values. Ultimately, I optimized Goertzel through hours of thought and research, finally realizing that if my frequecny values were preconfigured, it is easiest to precompute the coefficients as well, and use the same coefficients in a tri-axis Goertzel analysis while tracking seperate incrementing s_1 and s_2 variables per axis. I basically went from running nine or twelve for loops to running two main ones per Goertzel analysis, while also offloading the work to a second core. This miraculously kept the timing just under my .5 second limit. 

Getting the thread module to work well was also a significant challenge. I turned to Paul McWhorter's YouTube series, but found that what he was doing and my goals were not entirely aligned, so I had to fiddle with the architecture a lot. I went back and forth from having the thread startup each time a Goertzel analysis was requested and having it be a constantly running thread that shared memory space with the SeizureDetector class. Ultimately, this just took a lot of trial and error and common sense, but I refined the implementation into a thread that was always active rather than something that starts and dies every half second.

While I had been working out the issues with the Goertzel analysis, I also had to figure out how to actually do something meaningful when the Goertzel returned large power values in the seizure bands. This is where I had finally settled on implementing a rudamentary OLED UI. I started by going back to my original plan for a three menu UI, and wired the display in properly and programmed it to function properly.

Using Paul McWhorter's videos as a reference, I got started on an implementation of the IR controller to actually allow the user to interact with the OLED display, as in its current state, the OLED display did nothing meaningful. I think at this point I had a working seizure alarm on the screen, but I needed the user to interface with the display. 

Setting up IR control was potentially the most difficult task of this entire project, as I started using Paul McWhorter's tutorials as a reference, but found the library he was using confusing and error prone. Repeatedly, errors woul throw uring extremely simple operations, and it became abundantly clear that the default module was fundamentally incompatible with my timed 20 second loops. I could have offloaded the logic to core 2, but I was already pushing that core to its limits with Goertzel and would miss many inputs moving both instances there. I got permission from Mr. Sasaki to use AI to help me solve this problem an dhad AI assist me in writing assembly code, wrapping it in a class to constantly chceck input using one of the Pico's on board state machines. This became my pio_ir_rx.py file and PIO_IR_NEC class. I struggled to initially understand how to implement this, but quickly got up to speed after learning some basic assembly principles and testing the AI generated code. This was still a significant challenge though, as I had to really spend time wrapping my head around the entirely foreign concept of assembly and how it was able to process inputs while both cores were in use.

Following that truly challenging implementation, I had rudamentary OLED display control working.

The Buzzer implementation was quite straightforward, as was setting up more basic OLED interfacing.

The next major challenge I encountered was setting up the GPS. I had to get help soldering pins and used Paul McWhorter's online tutorials to interface with the GPS. This required learning about the whole paradigm of how GPS even works, largely through Paul's videos, as well as understanding what the outputs of GPS to the Pico W mean. I spent significant time iterating upon and improving my logic for capturing GPS data, largely through trial and error, printing GPS values to the console.

At this point, my project was very close to being complete, but I still had significant progress to make with the IR control of the display and what the display could show. While implementing the general logic for a security PIN, sleep mode, GPS activation, and log viewer / recorder was all actually very straightforward, I encoutnered significant error stemming from the complexity and scale to which my program had grown to. At this point many modules interacted with one anohter, and changing one aspect of a single module often broke features in another, often requiring me to read through files over and over until I had their functions memorized. Working about the complexity I had incurred while still delivering new features and solutions was the real final challenge. 

##What I Learned

I learned many things throughout my work on this project. One of the most important things I learned is that it is always best to be extremely careful when redesigning circuit layouts and wiring on breadboards. I spent hours attempting to make my components fit toegether as neatly as possible, frying two IR sensors in the process and almost destroying other components as there were multiple instances where I had forgot to properly wire things like the GPS module and buzzer following a redesign. Luckily, the devices weren't placed in an orientation that would have caused harm to the components, but the fact that there were multiple wiring mistakes on my part really opened my eyes to my own forgetfulness when working with complex systems. I also learned that being as focuesd as possible helps, as I would occasionally work while around my girlfriend, and would repeatedly make mistakes when chatting with her while working. 

I also learned how important it is to plan systems before you implement them. This is something I learned in high school programming classes, and through work on my own personal projects, but, working in an object-oriented language has made me understand just how important this is. I learned that many design decisions I made early on I became stuck with unless I decided to heavily refactor, as my class instances frequently overlapped and relied on eachother for their own behavior to properly function. I learned that sketching out a basic flow chart or even something as small as going in with a clear mental plan can make an extraordinary difference when working across multiple embedded and complex files. The amount of design mistakes I made which required correcting and small logical errors often grew and would frequently require me to rethink my overall system layout before ammending my mistake and continuing working. 

Through this project, my understanding of the importance of performance driven design principles grew significantly. Through my days of work figuring out how to optimize and set up the Goertzel algorithm, I not only learned some of the best practices for performance in Micropython, but why these practices are so important. I learned that it is always important to group performance intensive activities when possible, and that reducing for loops is almost always a plus. Precomputation can save large algorithms, and make them run very quickly on small devices like the Pico. Furthermore, I was able to learn that simplicity is often a sacrifice made for performance, but it can be a necessary sacrifice that greatly improves your ability to optimize other problems. I think it is often that on modern computers, optimization is considered, but not to the extent it needs to be on limited hardware like the Pico. I really feel much more confident in my ability to optimize my code better on microcontrollers in the future as well as on large projects on powerful computers. 

Beyoond this, I feel I have really gained a better understanding as to how tiny embedded systems work. Having to think through my own use cases, consider the limitations of my hardware, and fulfill my ambitions given the constraints, I found myself often questioning just how the Pico itself was desgined or the GPS module. I feel that I have learned just how complex these systems really are.

In terms of what I laerned technically, I will list those below, as there are too many to possibly discuss in paragraph form:
 - Micropython array vs list, how to use array and why to use it
 - How frequency analysis is done mathematically and computationally
 - How to interface with a microcontroller's state machine using Assembly
 - Basic Assembly programming and how to wrap functionality in a Micropython class
 - How to design and improve large OOP-based projects where classes often interface with eachother
 - How to design a class to represent an onboard device
 - How to use _thread to allocate complex work to the second core
 - The _ naming convention for private functions
 - What sockets are and how they work in Micropython for networking
 - How to set up a server and ensure steady operation using FSM architecture
 - Using the os library to interface with files on the Pico
 - Proper docstring and commenting conventions
 - Navigating complex input / display logic and decision trees given repeatedly refreshing inputs
 - GPS math, conventions, and interfacing over Micropython
 - NEC
 - quality code > quantity code
 - methods for creating decision trees when case / switch statements are unavailable
 - The importance of using local class variables in other classes to effectively reduce the amount of variables


























