import time
import math

PI = math.pi
def goertzel(buffer, sample_rate, frequency):

    N = len(buffer) #The length of our buffer (500) to be iterated over from 0 to 499
    k = round(frequency * N / sample_rate) #pulled from N = k * (sample_rate/freq))
    w_0 = 2 * PI * k / N
    coefficient = 2 * math.cos(w_0)
    
    s0 = 0.0
    s1 = 0.0
    s2 = 0.0
    
    for n in range(N):
        s0 = buffer[n] + coefficient * s1 - s2
        s2 = s1
        s1 = s0

    return s1*s1 + s2*s2 - (coefficient * s1 * s2) #returns power of frequency in signal
    
    



def multi_frequency_goertzel(buffer, low_frequency, high_frequency, sample_rate, number_samples, steps = 6):
    
    collection = []
    for f in range(low_frequency, high_frequency):
        collection.append([f, goertzel(buffer, sample_rate, f)])
    
    return collection
    
    
    
def multi_frequency_power(buffer, low_frequency, high_frequency, sample_rate, number_samples):
    collection = multi_frequency_goertzel(buffer, low_frequency, high_frequency, sample_rate, number_samples)
    sum = 0.0
    for item in collection:
        sum += int(item[1])
        
    return sum

def write_frequency(name, collection, power):
    
    f = open("test.txt", "w")
    

