import network
import urequests
import time
import socket

states = {"idle": 0, "connecting": 1, "listening": 2, "reading_request": 3, "sending": 4}

class WebServer:
    
    
    def __init__(self, gps, ssid="UHM", password="", port=80):
        self.gps = gps
        self.ssid = ssid
        self.password = password
        self.port = port
        self.wlan = network.WLAN(network.STA_IF)
        
        self.STATE_IDLE = 0
        self.STATE_CONNECTING = 1
        self.STATE_LISTENING = 2
        self.STATE_READING_REQUEST = 3
        self.STATE_SENDING_RESPONSE = 4
        
        
        
        self.state = self.STATE_IDLE
        self.sock = None
        self.client_sock = None
        self.client_buffer = ""
        self.response_data = b""
        
        # Data callback for getting system info
        self.data_callback = None
        
    def start(self):
        """Initialize WiFi and socket (non-blocking)"""
        if not self.wlan.isconnected():
            if not self.wlan.active():
                self.wlan.active(True)
            self.wlan.connect(self.ssid, self.password)
            self.state = states["connecting"]
        else:
            if self.state == states["idle"] or self.state == states["connecting"]:
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    self.sock.bind(('0.0.0.0', self.port))
                    self.sock.listen(1)
                    self.sock.setblocking(False)
                    print(f"Web server running at http://{self.wlan.ifconfig()[0]}")
                    self.state = states["listening"]
                except Exception as e:
                    print(f"Server bind error: {e}")
                    self.state = states["idle"]
                    
    def send_seizure_alert(self):
        try:
            response = urequests.post(
            "https://ntfy.sh/ece-296-pico-w-seizure-detector",
            data = "Seizure Detected!"
            )
            response.close()
        except:
            print("not connected")

    def update(self):
        
        # check connected
        if self.state == states["connecting"]:
            if self.wlan.isconnected():
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
                        self.client_buffer += data.decode()
                    except:
                        pass
                    
                    if '\r\n\r\n' in self.client_buffer:
                        print("Request received, processing...")
                        self._prepare_response()
                        self.state = states["sending"]
                else:
                    print("Client disconnected during request")
                    self._close_client()
            except OSError:
                pass

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
        """Prepare complete HTTP response before sending"""
        
        request_line = self.client_buffer.split('\r\n')[0] if '\r\n' in self.client_buffer else ""
        

        content = self.send_html()
        response_body = content
        content_type = "text/html"
        
        response_body_bytes = response_body.encode('utf-8')
        header = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nConnection: close\r\nContent-Length: {len(response_body_bytes)}\r\n\r\n"
        self.response_data = (header + response_body).encode('utf-8')

    def _close_client(self):
        try:
            if self.client_sock:
                time.sleep_ms(50)
                self.client_sock.close()
        except:
            pass
        finally:
            self.client_sock = None
            self.state = states["listening"]

    def send_html(self):
        html = f"""<!DOCTYPE html>
<html>
<body>
<h1>Seizure Detection System</h1>
<p>Status: no seizing</p>
<p>Last Seizure Count: count?</p>
<p>GPS Lat: {self.gps.lat}</p>
<p>GPS Lon: {self.gps.lon}</p>
</body>
</html>"""
        return html


