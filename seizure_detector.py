import goertzel
import oled

class SeizureDetector:
    
    def __init__(self, display):
        self.seize_count = 0
        self.display = display
        self.warning = False
    
    def analyze(self, x_b, y_b, z_b):
    
        x_power = goertzel.multi_goertzel(x_b, [0,1,2,3])
        y_power = goertzel.multi_goertzel(y_b, [0,1,2,3])
        z_power = goertzel.multi_goertzel(z_b, [0,1,2,3])
        
        seizure_frequency_power = x_power + y_power + z_power
        safe_frequency_power = goertzel.safe_multi_goertzel(x_b, [0,1,2]) + goertzel.safe_multi_goertzel(y_b, [0,1,2]) + goertzel.safe_multi_goertzel(z_b, [0,1,2])
        total_frequency_power = seizure_frequency_power + safe_frequency_power
        
        print("power")
        print(safe_frequency_power)
        print("power2")
        print(seizure_frequency_power)
        
        
        if seizure_frequency_power >= 1300 and seizure_frequency_power / total_frequency_power >= 0.75:
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







