import goertzel
import oled

class SeizureDetector:
    
    def __init__(self, oled):
        self.seize_count = 0
        self.is_sezure = False
        oled.display.text("hey", 0, 0)
        oled.show()
        
    
    def analyze(x_b, y_b, z_b):
    
        x_power = goertzel.multi_goertzel(x_b, [0,1,2,3])
        y_power = goertzel.multi_goertzel(y_b, [0,1,2,3])
        z_power = goertzel.multi_goertzel(z_b, [0,1,2,3])
        
        if x_power + y_power + z_power >= 500:
            sieze_count += 1
            
            if sieze_count >= 5:
                self.is_seizure = True
            else:
                self.is_seizure = False
                
        else:
            self.sieze_count = 0
            self.is_seizure = False
            
        if is_seizure:
            oled.draw_seizure_alert()
            oled.show()
            print("seizure")
    


oled = oled.Oled()
test = SeizureDetector(oled)
