class Oled:
    x_left = 0.0
    x_right = 127.0
    y_top = 0.0
    y_bottom = 63.0
    page = 0
    
    def draw_main_menu(self, display):
        display.text("Time:", 0,0)
        
    def draw_right_menu(self, display):
        display.text("", 0,0)
        
    def draw_left_menu(self, display):
        display.text("", 0,0)
        
    def draw_seizure_alert(self, display):
        display.text("SEIZURE DETECTED", 0, 0)
        display.text("ALERTING IN 15", 0, 0)
    def show(self, display):
        display.show()
        
        
      