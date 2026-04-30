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
def multi_goertzel(buffer, frequency_indicies):
    s = [[0.0, 0.0, 0.0] for _ in range(len(frequency_indicies))]
    powers = []
    power = 0.0
    
    for n in range(BUFFER_SIZE):
        for i in frequency_indicies:
            s[i][0] = buffer[n] + COEFFICIENTS[i] * s[i][1] - s[i][2]
            s[i][2] = s[i][1]
            s[i][1] = s[i][0]
        
    for i in frequency_indicies:
        #powers.append(s[i][1]*s[i][1] + s[i][2]*s[i][2] - (COEFFICIENTS[i] * s[i][1] * s[i][2]))
        power += s[i][1]*s[i][1] + s[i][2]*s[i][2] - (COEFFICIENTS[i] * s[i][1] * s[i][2])
        
    return power

@micropython.native
def three_axis_goertzel(xb, yb, zb, frequency_indices):
    n = len(frequency_indices)
    sx1=array.array('f',[0.0]*n); sx2=array.array('f',[0.0]*n)
    sy1=array.array('f',[0.0]*n); sy2=array.array('f',[0.0]*n)
    sz1=array.array('f',[0.0]*n); sz2=array.array('f',[0.0]*n)
    power=0.0

    for i in range(BUFFER_SIZE):
        x=xb[i]
        y=yb[i]
        z=zb[i]
        for j in range(n):
            c=COEFFICIENTS[frequency_indices[j]]
            sx0= x + c * sx1[j] - sx2[j]
            sx2[j] = sx1[j]
            sx1[j] = sx0
            sy0= y + c * sy1[j] - sy2[j]
            sy2[j] = sy1[j]
            sy1[j] = sy0
            sz0= z + c * sz1[j] - sz2[j]
            sz2[j] = sz1[j]
            sz1[j] = sz0
    
    for j in range(n):
        c=COEFFICIENTS[frequency_indices[j]]
        power += sx1[j] * sx1[j] + sx2[j] * sx2[j] - c * sx1[j] * sx2[j]
        power += sy1[j] * sy1[j] + sy2[j] * sy2[j] - c * sy1[j] * sy2[j]
        power += sz1[j] * sz1[j] + sz2[j] * sz2[j] - c * sz1[j] * sz2[j]
    return power

@micropython.native
def safe_three_axis_goertzel(xb, yb, zb, frequency_indices):
    n = len(frequency_indices)
    sx1=array.array('f',[0.0]*n); sx2=array.array('f',[0.0]*n)
    sy1=array.array('f',[0.0]*n); sy2=array.array('f',[0.0]*n)
    sz1=array.array('f',[0.0]*n); sz2=array.array('f',[0.0]*n)
    power=0.0

    for i in range(BUFFER_SIZE):
        x=xb[i]
        y=yb[i]
        z=zb[i]
        for j in range(n):
            c=SAFE_COEFFICIENTS[frequency_indices[j]]
            sx0= x + c * sx1[j] - sx2[j]
            sx2[j] = sx1[j]
            sx1[j] = sx0
            sy0= y + c * sy1[j] - sy2[j]
            sy2[j] = sy1[j]
            sy1[j] = sy0
            sz0= z + c * sz1[j] - sz2[j]
            sz2[j] = sz1[j]
            sz1[j] = sz0
    
    for j in range(n):
        c=SAFE_COEFFICIENTS[frequency_indices[j]]
        power += sx1[j] * sx1[j] + sx2[j] * sx2[j] - c * sx1[j] * sx2[j]
        power += sy1[j] * sy1[j] + sy2[j] * sy2[j] - c * sy1[j] * sy2[j]
        power += sz1[j] * sz1[j] + sz2[j] * sz2[j] - c * sz1[j] * sz2[j]
    return power


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
    



