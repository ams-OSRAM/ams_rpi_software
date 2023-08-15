# how to use css in python_ flask
# flask render_template example
 
from flask import Flask, render_template
import io
import logging
import socketserver
from http import server
from threading import Condition, Thread

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
# WSGI Application
# Provide template folder name
# The default folder name should be "templates" else need to mention custom folder name
app = Flask(__name__, template_folder='templates', static_folder='static')
 
# @app.route('/')
# def welcome():
#     return "This is the home page of Flask Application"
 
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/ams')
def ams():
    return render_template('main.html') 
if __name__=='__main__':

    picam2 = Picamera2()
    pixelsize = picam2.camera_properties['PixelArraySize']
    size = (pixelsize[0],pixelsize[1])
    picam2.configure(picam2.create_video_configuration(main={"size": size}))
    output = StreamingOutput()
    picam2.start_recording(JpegEncoder(), FileOutput(output))


    app.run(debug = True)

    picam2.stop_recording()
    picam2.close()