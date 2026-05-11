# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 10, 2026
# Filename: seizure_logger.py
# Description: seizure_logger.py allows interface between the Pico W's filesystem and other modules as well
#              as the user. Through the SeizureLogger class, seizure events can be logged and timestamped
#              for given days, as such events are stored to files titled the day of the seizure event.
#              Events logged to these files are inserted as the time at which a seizure event was recorded.
# ==========================================
import os #necessary for Micropython interface with system .txt files
import gps #import allows for safety checks, ensuring the GPS has time / date values prior to attempting to write or read files given time / date values which may be the None type


class SeizureLogger:
    
    """
    The SeizureLogger class allows for the reading and writing of seizure event recordings on the Pico W's storage.
    Files may be accessed via get_log_from_file, where a string of previous seizure events is extracted from a file
    if such a file exists in a string format, and returned to whichever function called get_log_from_file.
    Similarly, log_seizure_event allows for the recording of seizure events to the Pico's filesystem.
    Events are grouped by date and time, where date serves as a filename for a text file, collecting all
    seizures on that date by timestamps.

    The GPS module is crucial to the operation of this module, as files are only written to if
    it has been confirmed that the GPS module has been initialized, meaning the time / date values are not 'None'.
    Because log_seizure_event relies on writing the current date / time to files in order to categorize them,
    the GPS time / date must be initialized in order for any write to occur.
    """

    def __init__(self, gps):
        self.gps = gps
        
    """
    init initializes the gps module
    """

    def get_log_from_file(self, date):
        print('cd', date)
        date = date.replace('/', '_') + '.txt'
        print('query date', date)
        if self.gps.fix and self.file_exists(date):
            try:
                with open(date, 'r') as fr:
                    data = fr.read()
                    print('data', data)
                    return data
            except:
                print('error')
    
    """
    attempts to safely open a file if it exists, returning the raw data
    from the file if that file exists.
    """

                
    def log_seizure_event(self):
        
        if self.gps.date and self.gps.time:
            current_date = self.gps.current_date()
            current_time = self.gps.current_time()
            

            date = current_date
            year = date[-2] + date[-1]
            date = date[:-4] + year
            date = date.replace('/', '_') + '.txt'
            print('log date', date)
            
            try:
                with open(date, 'a') as fw:
                    fw.write(f"{str(self.gps.current_time())}\n")

            except:
                print('nope!')
                
    """
    using a try / except block, attempts to safely write a seizure event as a
    timestamp to a file by the name of the current date. If the file does not already
    exist, it should be created by the write action. Events are each recorded on their own
    line.
    """

    def file_exists(self, date):
        try:
            os.stat(date)
            return True
        except OSError:
            return False

    """
    Quickly determines if a file exists
    """



