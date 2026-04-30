import goertzel
import oled
import _thread

class SeizureDetector:
    
    def __init__(self, display):
        self.seize_count = 0
        self.display = display
        self.warning = False
        
    @micropython.native
    def analyze(self, x_b, y_b, z_b, mag_b):
    
        #x_power = goertzel.multi_goertzel(x_b, [0,1,2,3,4,5])
        #y_power = goertzel.multi_goertzel(y_b, [0,1,2,3,4,5])
        #z_power = goertzel.multi_goertzel(z_b, [0,1,2,3,4,5])
        
        #seizure_frequency_power = goertzel.multi_goertzel(x_b, [0,1,2,3,4,5]) + goertzel.multi_goertzel(y_b, [0,1,2,3,4,5]) + goertzel.multi_goertzel(z_b, [0,1,2,3,4,5])
        seizure_frequency_power = goertzel.three_axis_goertzel(x_b, y_b, z_b, [0,1,2,3,4,5])
        #safe_frequency_power = goertzel.safe_multi_goertzel(x_b, [0,1,2]) + goertzel.safe_multi_goertzel(y_b, [0,1,2]) + goertzel.safe_multi_goertzel(z_b, [0,1,2])
        
        safe_frequency_power = goertzel.safe_three_axis_goertzel(x_b, y_b, z_b, [0,1,2])
        total_frequency_power = seizure_frequency_power + safe_frequency_power
        
        print("safe")
        print(safe_frequency_power)
        print("seiz")
        print(seizure_frequency_power)
        
        
        if seizure_frequency_power >= 1000 and seizure_frequency_power / total_frequency_power >= 0.7:
            self.seize_count += 1
            print(self.seize_count)
            
            
            if self.seize_count >= 10:
                self.display.draw_seizure_alert()
                
            if self.seize_count > 5 and self.seize_count < 10: #if seize count for > 10 seconds
                self.display.trigger_seizure_warning()
                self.warning = True
        


                
        else:
            self.seize_count = 0
            self.display.draw_main_menu()
            self.warning = False







