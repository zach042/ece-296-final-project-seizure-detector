# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 10, 2026
# Filename: goertzel.py
# Description: this file aggregates the necessary functions to perform complex frequency analysis of
#              motion data, using the modified Discrete Fourier Transform known as the Goertzel Algorithm.
#              This file has thre primary functions:
#              1) precalculate_coefficients - a function which allows for the constants specific to each
#              frequency analyzed in the DFT to be calculated prior to the foor loop's work, allowing
#              for nearly double the performance of computing the coefficients during the DFT loop.
#              Because the frequency values are predetermined, this is a necessary and critical optimization.
#              2) three_axis_goertzel - a function which performs the goertzel alogrithm over three seperate
#              axes at once (xyz), allowing for extremely performant signal strenght analysis within the given bands
#              This function uses the coefficients calculated for frequencies within the seizure band
#              3) safe_three_axis_goertzel - an identical function to three_axis_goertzel apart fromt the use of
#              SAFE_COEFFICIENTS, the non-seizure frequency band coefficients rather than seizure band coefficients.
#
#              Both functions are critical, as the modern standard for analyzing seizures with wearable technology
#              generally considers some comparison of signal strength in seizure frequency bands to non seizure frequency bands.
# ==========================================

import math #math is necessary to deal with the cos calculations
import array #array allows for better optimization than lists [] while providing the same functionality for this use case
import config #config imports configured values

SAMPLE_RATE = config.SAMPLE_RATE #hz
BUFFER_SIZE = config.BUFFER_SIZE
FREQUENCIES_TO_CHECK = config.FREQUENCIES_TO_CHECK
SAFE_FREQUENCIES = config.SAFE_FREQUENCIES

def precalculate_coefficients(frequencies_to_check):
    """
    precalculate_coefficients serves as one of the greatest optimizations this proejct has made.
    The function is given a list of known frequencies it would typically have to calculate unique
    constants for each frequency within the goertzel algorithm itself, significantly reducing the speed
    of the goertzel algorithm to a near unusable point for 10 seconds of data at a 50Hz sample rate.

    This function simply extends the general widely available methods for computing Goertzel coefficients
    to a function which aggregattes these coefficients into an array.

    An array is used to collect these values, as it provides a more efficient way for the Pico W to
    append values to a list structure.
    """
    coefficients = array.array('f')
    for f in frequencies_to_check:
        N = BUFFER_SIZE
        k = round(f * N / SAMPLE_RATE)
        w_0 = 2 * math.pi * k / N
        coefficients.append(2 * math.cos(w_0))
    return coefficients 

COEFFICIENTS = precalculate_coefficients(FREQUENCIES_TO_CHECK) #calculates seizure band coeficients
SAFE_COEFFICIENTS = precalculate_coefficients(SAFE_FREQUENCIES) #calculates non seizure band coefficients
SEIZURE_FREQUENCY_INDICIES = [0,1,2,3,4,5] #indices of seizure band frequencies
SAFE_FREQUENCY_INDICIES = [0,1,2] #indices of non-seizure band freuquencies



@micropython.native
def three_axis_goertzel(xb, yb, zb, frequency_indices):
    """
    three_axis_goertzel extends the general Goertzel Discrete Fourier Transform to perform the same operations
    over three buffers of seperate data simulaenously. Coefficients are precalculated for each frequency, allowing
    for a single for loop to be run for each frequency, with an interior for loop iterating over each value within
    the 500 index buffer. This way, one for loop is run for each frequency, calculating the power of that specific frequency
    in all x,y,z bands.
    
    Effectively, this approach to the Goertzel DFT allows three calculations to run simultaneously of seperate buffer data
    using the same buffer index and frequency coefficient for each frequency analyzed. This is because, goertzel at its core
    is really just an algorithmic and sequential application of a coefficient multiplied by two sequencing values, and added to
    the buffer index. By maintaining s_1 and s_2 for each axis, these calculations for each axis are neatly applied simultaneously,
    iteratively adding to the overall power within the seizure band until all frequencies have been analyzed over xyz axes.
    
    A limitation of this approach is that x,y,z power values are not distinct from one another in the final power calculation.
    However, this is a standard approach, and the limit of what can computationally be achieved using Micropython to regularly
    isolate power values in frequency bands.
    """
    power=0.0 #initialize power value to a float

#iteratively analyze each frequency in the frequencies to be checked
    for frequency_index in frequency_indices:
        #s_1 and s_2 are standard constants used to algorithmically calculate the power of bands using Goertzel.
        #by assigning s_1 and s_2 to each axis, Goertzel is easily applied to the data from each axis because the coefficient is the same per axis, as the coefficient relies solely on values not relevant to axis.
        sx1 = 0.0
        sx2 = 0.0
        sy1 = 0.0
        sy2 = 0.0
        sz1 = 0.0
        sz2 = 0.0
        c = COEFFICIENTS[frequency_index] #set coefficient per frequency index (maps to a frequency)
        
#perform tri-axis Goertzel by extending the standard Goertzel algorithm three times
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
            
        #increment the power value by adding each final goertzel output for each axis.
        power += sx1 * sx1 + sx2 * sx2 - c * sx1 * sx2 
        power += sy1 * sy1 + sy2 * sy2 - c * sy1 * sy2
        power += sz1 * sz1 + sz2 * sz2 - c * sz1 * sz2
    return power

@micropython.native
def safe_three_axis_goertzel(xb, yb, zb, frequency_indices):
    """
    safe_three_axis_goertzel runs identically to three_axis goertzel, but instead of using the precalculated
    seizure band coefficients, it instead uses the precalculated safe frequency band coefficients.
    
    Refer to the three_axis goertzel documenation for instruction as to how the algorithm operates.
    
    The reason these functions were broken up into two seperate functions is because it was the easiest way
    of cleanly drawing a line between a function that handles the safe coefficients and the seizure band coefficients.
    It would be easily to merge the two functions into one and pass seperate arguments, but this was a design choice
    for general simplicity at the cost of 30 extra lines of code. 
    """
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




