import os
import time
import gps

class SeizureLogger:
    def __init__(self, gps):
        self.gps = gps
                
        
    def get_log_from_file(self, date):
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

                
    def log_seizure_event(self, date):
        date = date.replace('/', '_') + '.txt'
        if self.gps.fix:
            try:
                with open(date, 'a') as fw:
                    fw.write(f"{str(self.gps.time)}\n")
            except:
                print('nope!')

    def file_exists(self, date):
        try:
            os.stat(date)
            return True
        except OSError:
            return False

