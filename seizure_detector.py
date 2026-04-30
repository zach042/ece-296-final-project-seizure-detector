import goertzel
import oled

class SeizureDetector:
    
    def __init__(self, display):
        self.seize_count = 0
        self.is_sezure = False
        self.display = display

        
    
    def analyze(self, x_b, y_b, z_b):
    
        x_power = goertzel.multi_goertzel(x_b, [0,1,2,3])
        y_power = goertzel.multi_goertzel(y_b, [0,1,2,3])
        z_power = goertzel.multi_goertzel(z_b, [0,1,2,3])
        
        safe_power = goertzel.safe_multi_goertzel(x_b, [0,1,2]) + goertzel.safe_multi_goertzel(y_b, [0,1,2]) + goertzel.safe_multi_goertzel(z_b, [0,1,2])
        
        print("power")
        print(safe_power)
        print("power2")
        print(x_power + y_power + z_power)
        
        
        if x_power + y_power + z_power >= 500:
            self.seize_count += 1
            
            if self.seize_count >= 5:
                self.is_seizure = True
            else:
                self.is_seizure = False
                
        else:
            self.seize_count = 0
            self.is_seizure = False
            
        if self.is_seizure:
            self.display.draw_seizure_alert()
            self.display.show()
            print("seizure")
    






