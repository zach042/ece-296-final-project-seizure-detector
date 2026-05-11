# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 10, 2026
# Filename: goertzel.py
# Description: this file aggregates the necessary functions to perform complex frequency analysis of
# motion data, using the modified Discrete Fourier Transform known as the Goertzel Algorithm.
# This file has thre primary functions:
# 1) precalculate_coefficients - a function which allows for the constants specific to each
#    frequency analyzed in the DFT to be calculated prior to the foor loop's work, allowing
#    for nearly double the performance of computing the coefficients during the DFT loop.
#    Because the frequency values are predetermined, this is a necessary and critical optimization.
# 2) three_axis_goertzel - a function which performs the goertzel alogrithm over three seperate
#    axes at once (xyz), allowing for extremely performant signal strenght analysis within the given bands
#    This function uses the coefficients calculated for frequencies within the seizure band
# 3) safe_three_axis_goertzel - an identical function to three_axis_goertzel apart fromt the use of
#    SAFE_COEFFICIENTS, the non-seizure frequency band coefficients rather than seizure band coefficients.
#
#    Both functions are critical, as the modern standard for analyzing seizures with wearable technology
#    generally considers some comparison of signal strength in seizure frequency bands to non seizure frequency bands.
# ==========================================
import math #math is necessary to deal with the cos calculations
import array #array allows for better optimization than lists [] while providing the same functionality for this use case
import config #config imports configured values


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
def precalculate_coefficients(frequencies_to_check):
    coefficients = array.array('f')
    for f in frequencies_to_check:
        N = BUFFER_SIZE
        k = round(f * N / SAMPLE_RATE)
        w_0 = 2 * math.pi * k / N
        coefficients.append(2 * math.cos(w_0))
    return coefficients 

SAMPLE_RATE = config.SAMPLE_RATE #hz
BUFFER_SIZE = config.BUFFER_SIZE
FREQUENCIES_TO_CHECK = config.FREQUENCIES_TO_CHECK
SAFE_FREQUENCIES = config.SAFE_FREQUENCIES

COEFFICIENTS = precalculate_coefficients(FREQUENCIES_TO_CHECK)
SAFE_COEFFICIENTS = precalculate_coefficients(SAFE_FREQUENCIES)
SEIZURE_FREQUENCY_INDICIES = [0,1,2,3,4,5]
SAFE_FREQUENCY_INDICIES = [0,1,2,3,4,5]


"""
three_axis_goertzel 
"""
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




