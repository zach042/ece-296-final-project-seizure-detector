from imu import MPU6050
from machine import I2C, Pin
import time
import array
import math
import goertzel
import oled
import seizure_detector
import ir_controller

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
mag_buffer = array.array('f', [0.0] * BUFFER_SIZE)
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

def measure_old(buffer_index):
    global gx, gy, gz
    ax = mpu.accel.x
    ay = mpu.accel.y
    az = mpu.accel.z
    
    rx = mpu.gyro.x * 0.01745  # deg/s to rad/s
    ry = mpu.gyro.y * 0.01745
    rz = mpu.gyro.z * 0.01745
    
    new_gx = gx + (gy * rz - gz * ry) * (1.0 / SAMPLE_RATE)
    new_gy = gy + (gz * rx - gx * rz) * (1.0 / SAMPLE_RATE)
    new_gz = gz + (gx * ry - gy * rx) * (1.0 / SAMPLE_RATE)
    
    gx = ALPHA * new_gx + (1 - ALPHA) * ax
    gy = ALPHA * new_gy + (1 - ALPHA) * ay
    gz = ALPHA * new_gz + (1 - ALPHA) * az
    
    x_buffer[buffer_index] = ax - gx
    y_buffer[buffer_index] = ay - gy
    z_buffer[buffer_index] = az - gz
    
def measure(buffer_index):
    x_buffer[buffer_index] = mpu.accel.x
    y_buffer[buffer_index] = mpu.accel.y
    z_buffer[buffer_index] = mpu.accel.z
    
@micropython.native
def measure_mag(buffer_index):
    x_val = mpu.accel.x
    y_val = mpu.accel.y
    z_val = mpu.accel.z
    mag_buffer[buffer_index] = math.sqrt((x_val * x_val) + (y_val * y_val) + (z_val * z_val))

@micropython.native
def fill_initial_buffers():
    print("Filling bufers, wait 10 seconds")
    for i in range(500):
        s = time.ticks_us()
        measure(i)
        elapsed = time.ticks_us() - s
        remaining = 20_000 - elapsed

        if remaining > 0:
            time.sleep_ms(remaining // 1000)
        
        
    print("buffers filled")
    print(time.ticks_us() - s)
    


initialized = False
oled = oled.Oled()
oled.boot()
detector = seizure_detector.SeizureDetector(oled)
controller = ir_controller.IRController(oled)
while True:
    start = time.ticks_us()
    if initialized == False:
        fill_initial_buffers()
        initialized = True
    if buffer_index == 500:
        buffer_index = 0
        
    measure(buffer_index)
    
    if buffer_index % 25 == 0:
        detector.analyze(x_buffer, y_buffer, z_buffer, mag_buffer)
        
    buffer_index += 1
    end = time.ticks_us()
    elapsed = end - start
    remaining = 20_000 - elapsed

    if remaining > 0:
        time.sleep_ms(remaining // 1000)
    
    
    print('time', time.ticks_us() - start)
    
    



















