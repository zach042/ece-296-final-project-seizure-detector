import goertzel
import oled
import _thread
import time
import buzzer

class SeizureDetector:
    
    def __init__(self, display, buzzer):
        self.seize_count = 0
        self.display = display
        self.buzzer = buzzer
        self.warning = False
        self.input_x = None
        self.input_y = None
        self.input_z = None
        self.output_data = None
        self.seizure_power = 0.0
        self.total_power = 0.0
        self.safe_power = 0.0
        self.run_goertzel = False
        try:
            _thread.start_new_thread(self.core2_worker, ())
            print("Worker thread started")
        except Exception as e:
            print(f"Failed to start worker: {e}")
        
    @micropython.native
    def analyze(self, x_b, y_b, z_b):

        self.input_x = x_b
        self.input_y = y_b
        self.input_z = z_b
        self.run_goertzel = True
        
        if self.seizure_power != None:
            if self.seizure_power >= 1000 and self.seizure_power / self.total_power >= 0.9:
                self.seize_count += 1
                print(self.seize_count)
                
                if self.seize_count >= 10:
                    self.display.draw_seizure_alert()
                    self.buzzer.trigger()
                    
                if self.seize_count > 5 and self.seize_count < 10: #if seize count for > 10 seconds
                    self.display.trigger_seizure_warning()
                    self.warning = True
                    self.buzzer.trigger()
            else:
                self.seize_count = 0
                self.display.draw_same_menu()
                self.warning = False
        
    def core2_worker(self):
        while True:
            st = time.ticks_us()
            if self.input_x != None and self.run_goertzel == True:
                self.seizure_power = goertzel.three_axis_goertzel(self.input_x, self.input_y, self.input_z, [0,1,2,3,4,5])        
                self.safe_power = goertzel.safe_three_axis_goertzel(self.input_x, self.input_y, self.input_z, [0,1,2])
                self.total_power = self.seizure_power + self.safe_power
                self.run_goertzel = False
            
            self.buzzer.update()
            print('time for goertzel: ', time.ticks_us() - st)
                

            time.sleep_ms(10)
                











