from imu import MPU6050
from machine import I2C, Pin
import time
import array
import math
import goertzel
#import oled

#math constants
PI = math.pi

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

def measure(buffer_index):
    start_t = time.ticks_us()
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
        
    end_t = time.ticks_us()
    while time.ticks_diff(end_t, start_t) < 20000:
        end_t = time.ticks_us()


def fill_initial_buffers():
    s = time.ticks_us()
    print("Filling bufers, wait 10 seconds")
    for i in range(500):
        measure(i)
        
    print("buffers filled")
    print(time.ticks_us() - s)
    
    
    
def get_buffer_snap(circular_buf, write_index, size):
    snap = array.array('f', [0.0] * size)
    for i in range(size):
        snap[i] = circular_buf[(write_index + i) % size]
    return snap


    
def analyze(buffer):
    power = goertzel.multi_frequency_power(buffer, 3, 6, SAMPLE_RATE, 500)
    
    # Check if buffer is actually filling with different values
    unique_values = len(set(buffer))  # Should be close to 500 when full
    
    # Check if buffer_index is actually changing
    print(f"Power: {power:.1f} | Unique samples: {unique_values} | Index: {buffer_index}")

    


initialized = False
while True:
    if initialized == False:
        fill_initial_buffers()
        initialized = True
        
    if buffer_index == 500:
        buffer_index = 0
        
    measure(buffer_index)
    
    if buffer_index % 25 == 0:
        analyze(get_buffer_snap(x_buffer, buffer_index, 500))
        analyze(get_buffer_snap(y_buffer, buffer_index, 500))
        analyze(get_buffer_snap(z_buffer, buffer_index, 500))
        
    buffer_index += 1
        
    
    



















