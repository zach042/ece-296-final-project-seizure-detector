import time
import math
import array

PI = math.pi

def precalculate_coefficients(frequencies_to_check):
    coefficients = array.array('f')
    for f in frequencies_to_check:
        N = BUFFER_SIZE
        k = round(f * N / SAMPLE_RATE)
        w_0 = 2 * PI * k / N
        coefficients.append(2 * math.cos(w_0))
    return coefficients 

SAMPLE_RATE = 50 #hz
BUFFER_SIZE = 500
FREQUENCIES_TO_CHECK = [3,4,5,6,7,8]
SAFE_FREQUENCIES = [0.5,1,2]
COEFFICIENTS = precalculate_coefficients(FREQUENCIES_TO_CHECK)
SAFE_COEFFICIENTS = precalculate_coefficients(SAFE_FREQUENCIES)
FREQUENCY_INDICIES = [0,1,2,3,4,5]



#calculates goertzel for a single frequency
def single_goertzel(buffer, frequency_index):
    
    s0 = 0.0
    s1 = 0.0
    s2 = 0.0
    coefficient = COEFFICIENTS[frequency_index]

    for i in buffer:
        s0 = i + coefficient * s1 - s2
        s2 = s1
        s1 = s0

    return s1*s1 + s2*s2 - (coefficient * s1 * s2) #returns power of frequency in signal
    
 
@micropython.native
def multi_goertzel(buffer, frequency_indices):
    s = [[0.0, 0.0, 0.0] for _ in range(len(frequency_indices))]
    powers = []
    power = 0.0
    
    for n in range(BUFFER_SIZE):
        for i in frequency_indices:
            s[i][0] = buffer[n] + COEFFICIENTS[i] * s[i][1] - s[i][2]
            s[i][2] = s[i][1]
            s[i][1] = s[i][0]
        
    for i in frequency_indices:
        #powers.append(s[i][1]*s[i][1] + s[i][2]*s[i][2] - (COEFFICIENTS[i] * s[i][1] * s[i][2]))
        power += s[i][1]*s[i][1] + s[i][2]*s[i][2] - (COEFFICIENTS[i] * s[i][1] * s[i][2])
        
    return power

@micropython.native
def safe_multi_goertzel(buffer, frequency_indices):
    s = [[0.0, 0.0, 0.0] for _ in range(len(frequency_indices))]
    powers = []
    power = 0.0

    for i in range(len(frequency_indices)):
        s[i][0] = 0.0
        s[i][1] = 0.0
        s[i][2] = 0.0
    
    for n in range(BUFFER_SIZE):
        for i in frequency_indices:
            s[i][0] = buffer[n] + SAFE_COEFFICIENTS[i] * s[i][1] - s[i][2]
            s[i][2] = s[i][1]
            s[i][1] = s[i][0]
        
    for i in frequency_indices:
        #powers.append(s[i][1]*s[i][1] + s[i][2]*s[i][2] - (COEFFICIENTS[i] * s[i][1] * s[i][2]))
        power += s[i][1]*s[i][1] + s[i][2]*s[i][2] - (SAFE_COEFFICIENTS[i] * s[i][1] * s[i][2])
        
    return power

        

@micropython.native
def three_axis_multi_frequency_goertzel(xb, yb, zb, frequency_indicies):
    max_idx = max(frequency_indicies) + 1
    sx = [[0.0, 0.0, 0.0] for _ in range(max_idx)]
    sy = [[0.0, 0.0, 0.0] for _ in range(max_idx)]
    sz = [[0.0, 0.0, 0.0] for _ in range(max_idx)]
    power = 0.0
        
    for n in range(BUFFER_SIZE):
        for i in frequency_indicies:
            sx[i][0] = xb[n] + COEFFICIENTS[i] * sx[i][1] - sx[i][2]
            sx[i][2] = sx[i][1]
            sx[i][1] = sx[i][0]
            sy[i][0] = yb[n] + COEFFICIENTS[i] * sy[i][1] - sy[i][2]
            sy[i][2] = sy[i][1]
            sy[i][1] = sy[i][0]
            sz[i][0] = zb[n] + COEFFICIENTS[i] * sz[i][1] - sz[i][2]
            sz[i][2] = sz[i][1]
            sz[i][1] = sz[i][0]
            
    for i in frequency_indicies:
        #powers.append(s[i][1]*s[i][1] + s[i][2]*s[i][2] - (COEFFICIENTS[i] * s[i][1] * s[i][2]))
        power += sx[i][1]*sx[i][1] + sx[i][2]*sx[i][2] - (COEFFICIENTS[i] * sx[i][1] * sx[i][2])
        power += sy[i][1]*sy[i][1] + sy[i][2]*sy[i][2] - (COEFFICIENTS[i] * sy[i][1] * sy[i][2])
        power += sz[i][1]*sz[i][1] + sz[i][2]*sz[i][2] - (COEFFICIENTS[i] * sz[i][1] * sz[i][2])
    


def multi_frequency_goertzel(buffer, low_frequency, high_frequency, sample_rate, number_samples, steps = 6):
    
    collection = []
    for f in range(low_frequency, high_frequency):
        collection.append([f, goertzel(buffer, f)])
    
    return collection



def multi_frequency_power(buffer, low_frequency, high_frequency, sample_rate, number_samples):
    collection = multi_frequency_goertzel(buffer, low_frequency, high_frequency, sample_rate, number_samples)
    sum = 0.0
    for item in collection:
        sum += float(item[1])
        
    return sum

def write_frequency(name, collection, power):
    
    f = open("test.txt", "w")
    

