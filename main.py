# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 11, 2026
# Filename: main.py
# Description: This file collects every module which runs on core 1 / thread 0 into a single place,
#              deploying a general stream of work on core 1, where xyz accelerometer data is aggregated
#              into buffers and fed into a seizure detection module.
#
# ==========================================
from imu import MPU6050
from machine import I2C, Pin
import time
import array
import math
import goertzel
import oled
import seizure_detector
import ir_controller
import buzzer
import gps
import seizure_logger
import config

#sampling constants
SAMPLE_RATE = config.SAMPLE_RATE #50HZ - the amount of samples of accelerometer data collected per second (50)
BUFFER_SECS = config.BUFFER_SECS #10s - the total amount of time the buffer accumulates
BUFFER_SIZE = config.BUFFER_SIZE #500 samples - buffer size for xyz accelerometer data
ANALYZE_EVERY = config.ANALYZE_EVERY #25 - 25/50 = 1/2, so xyz accelerometer data is analyzed once every half second


# hardware config
MPU_ADDR = 0x68
i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000) #i2c connection to the MPU6050 accelerometer
i2c.writeto_mem(MPU_ADDR, 0x1A, bytes([0x03]))  #setting DLPF 44 Hz bandwidth
i2c.writeto_mem(MPU_ADDR, 0x19, bytes([19])) #setting 50 Hz sample rate
mpu = MPU6050(i2c) #initialized mpu6050 device


#buffers - data points storing physical motion behavior along x y z axes
x_buffer = array.array('f', [0.0] * BUFFER_SIZE)
y_buffer = array.array('f', [0.0] * BUFFER_SIZE)
z_buffer = array.array('f', [0.0] * BUFFER_SIZE)

#buffer config
buffer_index = 0 #starting index with which buffers are filled = 0, the first index
buffer_full = False #buffers are initially unfilled

#measure function passes MPU accelerometer data into the xyz buffers    
def measure(buffer_index):
    x_buffer[buffer_index] = mpu.accel.x
    y_buffer[buffer_index] = mpu.accel.y
    z_buffer[buffer_index] = mpu.accel.z


#module initializiation
gps_module = gps.GPS() #gps module 
logger = seizure_logger.SeizureLogger(gps_module) #seizure_logger module
buzzer = buzzer.Buzzer() #buzzer module
oled = oled.Oled(buzzer, gps_module, logger) #oled module
oled.boot() #startup oled module
detector = seizure_detector.SeizureDetector(oled, buzzer, logger) #seizure detector module
ir_control = ir_controller.IRController(oled, detector) #infrared recieiver and control module

while True:
    """
    This is the main loop where all of the code is tied together.
    The main loop runs on thread 0 with a maximum timeout of 20ms per cycle,
    such that buffer values are resampled every 20ms, meeting the 50Hz rating.

    Every cycle, the buffer index is reset if the xyz buffers are full. Otherwise,
    new data is inserted into the xyz buffers at the current value of the buffer index.

    This loop spawns an onboard SFM to await IR input as well, such that input is non-blocking, but
    such that input received is also passed to functions. This input data is what allows the user
    to control the rest of the device, and as every module has been pre-initialized,
    when the user enters input into the system, it is automatically handled by the
    ir_controller mdoule, which extends changes in behavior to the display, GPS, and buzzer.
    This logic is all obscured away into the other modules for brevity within the main loop, but
    it is important to make the distinction that the main loop is fundamentally what facilitates the input
    into the ir_controller, allowing for this behavior, and that any behavior which the ir_controller
    influences runs on thread 0 apart from the web server and Goertzel analyses, which are almost entirely
    facilitated by seperate processes on thread 1. This is managed safely though, as thread 0 passes data
    to shared memory with thread 1 in the SeizureDetector class.

    Every half second, a goertzel analysis is demanded, forcing the detector to command
    thread 1 to perform a Goertzel analysis every half second.

    In order to maintain a steady 20ms cycle time, a timed sleep pauses the cycle if it finishes
    before 20ms.

    Once the loop is finished, the buffer index is incremented, such that every 20ms singular new data
    points are aggregated into the xyz buffers, maintaining a 50Hz sample rate.

    """

    start = time.ticks_ms()
        
#if buffer becomes full, reset its index to zero such that the buffer refills from zero
    if buffer_index == BUFFER_SIZE:
        buffer_index = 0
        
#measure xyz data into buffer indices at the given buffer index
    measure(buffer_index)
    
#allows non-blocking input
    ir_control.await_input()

#once ever half second run a Goertzel analysis on the second thread
    if buffer_index % 25 == 0:
        detector.analyze(x_buffer, y_buffer, z_buffer)
        

#at the end of the loop, 
    buffer_index += 1
    end = time.ticks_ms()
    elapsed = end - start
    remaining = 20 - elapsed
    
    if remaining > 0:
        time.sleep_ms(remaining)
    
    #optional debug line ensures that cycle finishes within 20ms becauause each loop must be 20ms in order to hit 50Hz target
    #print('time to cycle',time.ticks_ms() - start)
    
    



















