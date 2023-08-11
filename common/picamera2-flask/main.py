#!/usr/bin/env python

from picamera2 import Picamera2

from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
# from libcamera import Transform
import io
from threading import Condition
import time
import os

from flask import Flask, jsonify, redirect, render_template, Response

dirpath = "/tmp"


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class Camera:
    """
    states:
    open
    started
    stopped
    closed
    """
    def __del__(self):
        self.close()

    def __init__(self):
        self.picam2 = None
    def open(self):
        if not(self.picam2):
            self.picam2 = Picamera2()
            pixelsize = self.picam2.camera_properties['PixelArraySize']
            self.size = (pixelsize[0],pixelsize[1])
        if not(self.picam2.is_open):
            self.picam2.__init__()
        if self.is_started:
            self.stop_recording()
    @property
    def is_started(self):
        return self.picam2.started
    @property
    def is_opened(self):
        return self.picam2.is_open
    
    # def open(self):
    #     self.picam2.__init__()

    def close(self):
        if self.picam2.is_open:
            self.picam2.close()
        

    def start_recording(self,output):
        self.picam2.start_recording(JpegEncoder(), FileOutput(output))
    
    def stop_recording(self):
        if self.is_started:
            self.picam2.stop_recording()


    
camera = Camera()

# App Globals
app = Flask(__name__, template_folder='templates', static_folder='static')

app.config['SECRET_KEY'] = 'secret_key_for_flask'
# login_manager = LoginManager(app)



def genFrames(camera):
    camera.open()
    output = StreamingOutput()
    video_config = camera.picam2.create_video_configuration(main={
                "size": camera.size})
    camera.picam2.configure(video_config)
    camera.picam2.set_controls({"ExposureTime": 100, "AnalogueGain": 1.0})
    camera.start_recording(output)
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def captureImage(camera):
    camera.open()
    status = "failed"
    try:
        camera_config = camera.picam2.create_still_configuration(main={
                "size": camera.size})
        filename = time.strftime("%Y%m%d-%H%M%S") + '.jpg'
        savepath = os.path.join(dirpath, filename)
        # camera.picam2.start()
        camera.picam2.switch_mode_and_capture_file(camera_config, savepath)
        status = "success"
        print('caputre successful')
    except Exception as e:
        print(e)
    finally:
        camera.stop_recording()
        # camera.picam2.stop()
        # camera.picam2.close()
    return {'status': status}



@app.route('/index.html')
def indexhtml():
    return redirect('/')


@app.route('/')
def index():
    return render_template('index.html')  # you can customze index.html here


@app.route('/capture')
def capture():
    global camera
    print('capture routinge')
    outcome = captureImage(camera)
    return jsonify(outcome)


# defines the route that will access the video feed and call the feed function
@app.route('/video_feed')
def video_feed():
    return Response(genFrames(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# @app.route('/stop')
# def stop():
#     global camera
#     camera.close()
#     outcome = {'status': 'stopped'}
#     return jsonify(outcome)


# @app.route('/start')
# def start():
#     global camera
#     camera.open()
#     outcome = {'status': 'started'}
#     return jsonify(outcome)


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User()
#         if user is not None and user.check_password(form.password.data):
#             login_user(user, remember=form.remember_me.data)
#             next_page = request.args.get('next')
#             if not next_page or url_parse(next_page).netloc != '':
#                 next_page = url_for('index')
#             return redirect(next_page)
#     return render_template('login_form.html', form=form)
#
#
# @app.route('/logout')
# def logout():
#     logout_user()
#     return redirect(url_for('index'))
#
#
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
