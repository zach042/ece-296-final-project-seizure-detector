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


@micropython.native
def three_axis_goertzel(xb, yb, zb, frequency_indices):

    power=0.0

    for frequency_index in frequency_indices:
        sx1 = 0.0
        sx2 = 0.0
        sy1 = 0.0
        sy2 = 0.0
        sz1 = 0.0
        sz2 = 0.0
        c = COEFFICIENTS[frequency_index]
        
        for i in range(BUFFER_SIZE):
            sx0= xb[i] + c * sx1 - sx2
            sx2 = sx1
            sx1 = sx0
            
            sy0= yb[i] + c * sy1 - sy2
            sy2 = sy1
            sy1 = sy0
            
            sz0= zb[i] + c * sz1 - sz2
            sz2 = sz1
            sz1 = sz0
    
        power += sx1 * sx1 + sx2 * sx2 - c * sx1 * sx2
        power += sy1 * sy1 + sy2 * sy2 - c * sy1 * sy2
        power += sz1 * sz1 + sz2 * sz2 - c * sz1 * sz2
    return power

@micropython.native
def safe_three_axis_goertzel(xb, yb, zb, frequency_indices):
    
    power=0.0

    for frequency_index in frequency_indices:
        sx1 = 0.0
        sx2 = 0.0
        sy1 = 0.0
        sy2 = 0.0
        sz1 = 0.0
        sz2 = 0.0
        c = SAFE_COEFFICIENTS[frequency_index]
        
        for i in range(BUFFER_SIZE):
            sx0= xb[i] + c * sx1 - sx2
            sx2 = sx1
            sx1 = sx0
            
            sy0= yb[i] + c * sy1 - sy2
            sy2 = sy1
            sy1 = sy0
            
            sz0= zb[i] + c * sz1 - sz2
            sz2 = sz1
            sz1 = sz0
    
        power += sx1 * sx1 + sx2 * sx2 - c * sx1 * sx2
        power += sy1 * sy1 + sy2 * sy2 - c * sy1 * sy2
        power += sz1 * sz1 + sz2 * sz2 - c * sz1 * sz2
        
    return power




