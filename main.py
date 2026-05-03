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

#sampling constantsconstants
SAMPLE_RATE    = 50       # Hz
BUFFER_SECS    = 10       # seconds of history
BUFFER_SIZE    = SAMPLE_RATE * BUFFER_SECS  # 500 samples
ANALYZE_EVERY  = 25       # run analysis every 0.5 sec (25 samples at 50 Hz)


# hardware config
MPU_ADDR = 0x68
i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=400000)
i2c.writeto_mem(MPU_ADDR, 0x1A, bytes([0x03]))  #DLPF 44 Hz bandwidth
i2c.writeto_mem(MPU_ADDR, 0x19, bytes([19]))     #50 Hz sample rate
mpu = MPU6050(i2c)


#buffers - data points storing wave behavior
x_buffer = array.array('f', [0.0] * BUFFER_SIZE)
y_buffer = array.array('f', [0.0] * BUFFER_SIZE)
z_buffer = array.array('f', [0.0] * BUFFER_SIZE)
buffer_index = 0
buffer_full = False
sample_count = 0

# gravity filter
gx = mpu.accel.x
gy = mpu.accel.y
gz = mpu.accel.z
ALPHA = 0.98  # complementary filter constant

sieze_count = 0
is_seizure = False
    
def measure(buffer_index):
    x_buffer[buffer_index] = mpu.accel.x
    y_buffer[buffer_index] = mpu.accel.y
    z_buffer[buffer_index] = mpu.accel.z



initialized = True
oled = oled.Oled()
oled.boot()
buzzer = buzzer.Buzzer()
detector = seizure_detector.SeizureDetector(oled, buzzer)
ir_control = ir_controller.IRController(oled)

while True:
    start = time.ticks_us()
        
    if buffer_index == 500:
        buffer_index = 0
        
    measure(buffer_index)
    ir_control.await_input()
    


        
    if buffer_index % 25 == 0:
        detector.analyze(x_buffer, y_buffer, z_buffer)
        
    buffer_index += 1
    end = time.ticks_us()
    elapsed = end - start
    remaining = 20_000 - elapsed
    
    if remaining > 0:
        time.sleep_ms(remaining // 1000)
    
    
    #print('time to cycle',time.ticks_us() - start)
    
    



















