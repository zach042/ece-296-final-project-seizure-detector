import os
import time
import gps

class SeizureLogger:
    def __init__(self, gps):
        self.gps = gps
        self.living_logged_date_times = []
                
        
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

                
    def log_seizure_event(self):
        
        if self.gps.date and self.gps.time:
            current_date = self.gps.current_date()
            current_time = self.gps.current_time()
            
            if not (current_date + current_time) in self.living_logged_date_times:
                date = current_date
                year = date[-2] + date[-1]
                date = date[:-4] + year
                date = date.replace('/', '_') + '.txt'
                print('log date', date)
                
                if not ((current_date + current_time) in self.living_logged_date_times):
                    self.living_logged_date_times.append(current_date + current_time)
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



