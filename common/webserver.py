#!/usr/bin/python3

# Mostly copied from https://picamera.readthedocs.io/en/release-1.13/recipes2.html
# Run this script, then point a web browser at http:<this-ip-address>:8000
# Note: needs simplejpeg to be installed (pip3 install simplejpeg).

import io
import logging
import socketserver
from http import server
from threading import Condition, Thread

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

PAGE = """\
<html>
<head>
<title>ams MIRA</title>
</head>
<body>
<h1>ams MIRA web view</h1>
<img src="stream.mjpg" width="400" height="400" />
<form name="myform" action="none" method="post">
 <button name="left">stop video</button>
 <button name="right">start video</button>
<div class="slidecontainer">
  <input type="range" min="1" max="100" value="50" class="slider" id="myRange">
</div>
</form>

</body>
</html>
"""


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_POST(self):
        print('post req')
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        #self.send_response(204) # 204 is no content so we stay on page
        #self.end_headers()
        response = io.BytesIO()
        response.write(body)
        button = str(response.getvalue().decode('UTF-8'))
        print(f'button is {button}')
        if "left" in button:
            print('long exp')
            picam2.set_controls({"ExposureTime": 1000, "AnalogueGain": 1.0})
            picam2.stop_recording()
            picam2.close()
        if "right" in button:
            picam2.__init__()
            picam2.set_controls({"ExposureTime": 5000, "AnalogueGain": 1.0})
            picam2.start_recording(JpegEncoder(), FileOutput(output))
        #self.path='/'
        self.send_response(303)        
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', '/index.html')
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))
picam2.stop_recording()
picam2.close()
try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()
