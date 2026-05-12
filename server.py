# ==========================================
# Project: ECE 296 Seizure Detector
# Author: Zach Teagarden
# Date: May 11, 2026
# Filename: server.py
# Description: This file collects the WebServer class, a state machine based approach to a web server 
#              and notification system using ntfy. The web server implementation itself primarily uses
#              network, socket, and five arbitrary states:
#
#              idle -> waiting for connection / doing nothing
#              connecting -> in the proces of connecting to wifi
#              listening -> waiting for connections
#              reading_request
#              sending -> sending HTML response to user who previously made a request
#              
#              These states are maintained in the self.state variable such that outside
#              regularly interfacing wiht an instance of the WebServer class can perform multiple
#              operations over multiple cycles.
#
#              The web server itself is designed to run on core 2 / thread 1, managed by the core2_worker
#              within the seizure_detector, as the logic managing core 2 code exists within the seizure_detector.py
#              file. The update() function is called regularly from the core2_worker when Goertzel isn't actively running
#              such that the server can continuously serve and wait for requests.         
# ==========================================
#necessary imports
import network
import urequests
import time
import socket
import config

#state-machine states
states = {"idle": 0, "connecting": 1, "listening": 2, "reading_request": 3, "sending": 4}

class WebServer:
    """
    The WebServer class serves as a way to serve HTTP requests without having to pause
    Goertzel algorithms or the main thread to serve / listen to requests.
    
    The WebServer class should be instantiated inside of the SeizureDetector class and
    run within the core2_worker whenever Goertzel is not being requested. This behavior
    prevenst the server logic from interrupting timing in the main loop or with the general
    Goertzel analysis of frequencies.
    
    
    """
    
    def __init__(self, gps, sd):
        self.gps = gps
        self.ssid = config.ssid
        self.password = config.password
        self.port = config.port
        self.wlan = network.WLAN(network.STA_IF)
        self.sd = sd
        self.state = states["idle"]
        self.sock = None
        self.client_sock = None
        self.client_buffer = ""
        self.response_data = b""
        self.wifi_retries = 0
        
        """
        Initializes the instance of the WebServer class, accepting in
        wifi credentials from the config file as well as a seziure detection
        class instance and a gps class instance.
        
        The state is initially idle while sockets and buffers are also initially
        empty.
        """
        
    def start(self):
        """
        This function turns the web server on by binding the socket, ensuring there is a connection,
        and transitioning to the listening state once a connection is established.
        """
    #if the server is not connected to the wifi, set the wlan active flag to True and connect
        if not self.wlan.isconnected():
            if not self.wlan.active():
                self.wlan.active(True)
                time.sleep(1)
            try:
                self.wlan.disconnect()
            except:
                pass
            time.sleep_ms(100)
            self.wlan.connect(self.ssid, self.password)
            self.connect_start_ticks = time.ticks_ms()
            self.state = states["connecting"]
            #set the state to connecting to indicate connection is initializing
    #otherwise, if the device is idle or connecting, bind the socket 
        else:
            if self.state == states["idle"] or self.state == states["connecting"]:
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a network socket
                    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #establish that the port may be reused 
                    self.sock.bind(('0.0.0.0', self.port)) #bind to port 80
                    self.sock.listen(1) #listen on the socket
                    self.sock.setblocking(False) #ensure the socket is non blocking
                    print(f"Web server running at http://{self.wlan.ifconfig()[0]}") #if user is running program on PC, print the server address.
                    self.state = states["listening"] #set state to listening
                except Exception as e: #if fails go back to idle
                    self.state = states["idle"]
                    
    def send_seizure_alert(self):
        """
        This is the one function that can be run on core 1 because it's near instantaneous
        and simply sends an alert over HTTP.
        
        For organiational purposes, it was lumped into this class, and should be called whenever
        a seizure is detected.
        """
        try:
            response = urequests.post("https://ntfy.sh/ece-296-pico-w-seizure-detector",data = "Seizure Detected!") #send POST request over server to ntfy
            response.close() #close request
        except:
            print("not connected") #if there's an error do nothing

    def update(self):
        """
        The update function should be called frequently by the core2_worker.
        
        This function updates and maintains state logic.
        """
        
        # check connected
# replace the connecting block in update()
        if self.state == states["connecting"]:
            if self.wlan.isconnected():
                print("WiFi connected")
                self.start()
            elif time.ticks_diff(time.ticks_ms(), self.connect_start_ticks) > 15000:
                self.wifi_retries += 1
                print(f"WiFi timeout (attempt {self.wifi_retries}/{MAX_WIFI_RETRIES})")
                if self.wifi_retries >= 5:
                    print("WiFi: max retries reached, going idle")
                    self.state = states["idle"]
                else:
                    try:
                        self.wlan.disconnect()
                    except:
                        pass
                    self.wlan.active(False)
                    time.sleep(1)
                    self.state = states["idle"]
                    self.start()
            return
        # accept conn
        if self.state == states["listening"]:
            try:
                self.client_sock, addr = self.sock.accept()
                print(f"Client connected")
                self.client_buffer = ""
                self.state = states["reading_request"]
            except:
                pass 
        
        #read http
        if self.state == states["reading_request"]:
            try:
                data = self.client_sock.recv(1024)
                if data:
                    try:
                        self.client_buffer += data.decode() #decode response from client
                    except:
                        pass
                    
                #if this flag is seen the request is finished and we can move on
                    if '\r\n\r\n' in self.client_buffer:
                        self._prepare_response() #generate HTML and prepare it to be sent
                        self.state = states["sending"] #set the state to sending
                else:
                    self._close_client() #close client if data is not present or invalid
            except:
                pass #handle error by passing so the system doesn't crash on error
            

        # send html
        if self.state == states["sending"]:
            try:
                total_sent = 0
                while total_sent < len(self.response_data):
                    try:
                        sent = self.client_sock.send(self.response_data[total_sent:])
                        total_sent += sent
                    except:
                        break
                
                time.sleep_ms(50)  # Ensure client receives data
            except:
                pass
            
            finally:
                self._close_client()

    def _prepare_response(self):
        """
        Creates full HTTP response in a string.
        content is retreieved from the send_html function and displayed to the user.
        """        

        content = self.send_html() #get HTML
        response_body = content 
        content_type = "text/html"
        
        response_body_bytes = response_body.encode('utf-8') #encode the html into literal bytes for transmission
        header = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nConnection: close\r\nContent-Length: {len(response_body_bytes)}\r\n\r\n"
        self.response_data = (header + response_body).encode('utf-8')

    def _close_client(self):
        """
        Closes connection between a client and resets the state to listening.
        
        Ensures a connection doesn't stay open forever.
        """
        try:
            if self.client_sock:
                time.sleep_ms(50) #delay because errors were thrown when I didn't include it.
                self.client_sock.close()
        except:
            pass
        finally:
            self.client_sock = None #reset the socket
            self.state = states["listening"] #reset the state

    def send_html(self):
        """
        Function generates and sends HTML to other functions as a string
        """
        html = f"""<!DOCTYPE html>
<html>
<body>
<h1>Seizure Detection System</h1>
<p>Status: Having seizure?: {self.sd.seizing}</p>
<p>GPS Lat: {self.gps.lat}</p>
<p>GPS Lon: {self.gps.lon}</p>
</body>
</html>"""
        return html


