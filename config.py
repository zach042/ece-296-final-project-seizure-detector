from imu import MPU6050
from machine import I2C, Pin
#sampling constantsconstants
SAMPLE_RATE = 50 # Hz
BUFFER_SECS = 10 # seconds of history
BUFFER_SIZE = SAMPLE_RATE * BUFFER_SECS  # 500 samples
ANALYZE_EVERY = 25 # run analysis every 0.5 sec (25 samples at 50 Hz)


FREQUENCIES_TO_CHECK = [3,4,5,6,7,8]
SEIZURE_FREQUENCY_INDICIES = [0,1,2,3,4,5]
SAFE_FREQUENCIES = [0.5,1,2]
SAFE_FREQUENCY_INDICIES = [0,1,2]

numpad = {"0x00ff6897": 0, "0x00ff30cf": 1, "0x00ff18e7": 2, "0x00ff7a85": 3, "0x00ff10ef": 4, "0x00ff38c7": 5, "0x00ff5aa5": 6, "0x00ff42bd": 7, "0x00ff4ab5": 8, "0x00ff52ad": 9}
commands = {"page_right": "0x00ffc23d", "page_left": "0x00ff02fd", "sel_up": "0x00ffa857", "sel_down": "0x00ff906f", "enter": "0x00ff22dd", "exit": "0x00ffa25d", "delete": "0x00ff9867"}
code = "1234"
