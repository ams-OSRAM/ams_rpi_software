#!/usr/bin/env python
import io
import numpy as np
import pathlib
import time
import os
from threading import Condition
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from picamera2.sensor_format import SensorFormat
from zipfile import ZipFile
from PIL import Image
from flask.views import MethodView
from flask import Flask, jsonify, redirect, render_template, Response, flash, request, url_for
from werkzeug.utils import secure_filename
from wtforms import Form, BooleanField, StringField, PasswordField, validators, DecimalRangeField, DecimalField, SubmitField , IntegerField, SelectField


import sys
sys.path.append("../common")
sys.path.append("../../common")

from driver_access import v4l2Ctrl
from config_parser import ConfigParser


class Camera():
    """
    states:
    open
    started
    stopped
    closed
    """
    def __del__(self):
        self.close()

    def __init__(self, exposure_us = 1000, gain = 1, bitmode = 12, illumination=True):
        self.controls = {'exposure_us' : exposure_us, 'gain' : gain, 'bitmode' : bitmode, 'illumination': True}
        self.picam2 = None
        self.cam_info = None
    
    def open(self):
        if not(self.picam2):
            self.picam2 = Picamera2()
            self.cam_info = self.picam2.camera_properties
            pixelsize = self.picam2.camera_properties['PixelArraySize']
            self.size = (pixelsize[0],pixelsize[1])
        if self.is_started:
            self.stop_recording()        
        if not(self.picam2.is_open):
            self.picam2.__init__()

    @property
    def is_started(self):
        if self.picam2:
            return self.picam2.started
        else:
            return False
    @property
    def is_opened(self):
        if self.picam2:
            return self.picam2.is_open
        else:
            return False
    # def open(self):
    #     self.picam2.__init__()

    def close(self):
        if self.picam2:
            self.stop_recording()
            if self.picam2.is_open:
                self.picam2.close()
        
    def update_controls(self):
        if self.is_opened:
            print('setting controls')
            self.picam2.set_controls({"ExposureTime": camera.controls['exposure_us'], "AnalogueGain": camera.controls['gain']})
        print(camera.controls['illumination'])
        # if camera.controls['illumination']=='on': 
        #     print('enable illum')
        #     self.set_illum_trigger( en_trig_illum = True)
        # else:  
        #     print('disable illum')
        #     self.set_illum_trigger( en_trig_illum = False)

    def write_register(self, addr, val):
        i2c = v4l2Ctrl(sensor="mira050", printFunc=print)
        result=i2c.rwReg(addr=addr, value=val, rw=1, flag=0)
        print(f'write {addr } to {val} with result {result}')

    def set_illum_trigger(self, en_trig_illum=True, illum_width_us=None, illum_delay_us=0):
        # exp_val = i2c.rwReg(addr=addr, value=val, rw=1, flag=0)
        data_rate = 1000
        if not illum_width_us:
            illum_width_us=camera.controls['exposure_us']
        illum_width = int(illum_width_us * data_rate / 8)
        illum_delay = int(illum_delay_us + 2**19)
        split_value = lambda x, y: x >> (8*y) & 255
        self.write_register(0xe004,  0)
        self.write_register(0xe000,  1)
        self.write_register(0x001C, int(en_trig_illum))

        self.write_register(0x0019, split_value(illum_width, 2))
        self.write_register(0x001A, split_value(illum_width, 1))
        self.write_register(0x001B, split_value(illum_width, 0))

        self.write_register(0x0016, split_value(illum_delay, 2))
        self.write_register(0x0017, split_value(illum_delay, 1))
        self.write_register(0x0018, split_value(illum_delay, 0))



    def start_recording(self,output):
        self.picam2.start_recording(JpegEncoder(), FileOutput(output))
    
    def stop_recording(self):
        if self.is_started:
            print(f'status of is started: {self.is_started}')
            try:
                self.picam2.stop_recording()
            except Exception as e:
                print(e)
amount = 1
download_option = 'tiff'
cam_info = ''
UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# app = Flask(__name__)
# App Globals
app = Flask(__name__, template_folder='templates', static_folder='static')

app.config['SECRET_KEY'] = 'secret_key_for_flask'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

dirpath = "/tmp"
users = []
    
camera = Camera()
# camera.open()

class ControlGroupAPI(MethodView):
    def __init__(self,camera):
        self.camera = camera
    def get(self):
        return jsonify(camera.controls)
    def put(self):
        print('put')
        print(request.json)
        self.camera.controls = request.json
        self.camera.update_controls()
        print(request.json['exposure_us'])
        return request.json
        # return 'hello put'

class ControlItemAPI(MethodView):
    def __init__(self,camera):
        self.camera = camera
    def get(self, id):
        return jsonify(camera.controls[id])
    def put(self,id):
        print('put')
        data= int(request.get_data())
        self.camera.controls[id] = data
        self.camera.update_controls()
        return jsonify(data)
        # return 'hello put'

def register_api(app: Flask, camera: Camera , name: str):
    item = ControlItemAPI.as_view(f"{name}-item", camera)
    group = ControlGroupAPI.as_view(f"{name}-group", camera)
    app.add_url_rule(f"/{name}/<id>", view_func=item)
    app.add_url_rule(f"/{name}/", view_func=group)
register_api(app, camera, 'controls')

class ControlForm(Form):
    # def __init__(self, form, expmin, expmax):
    exposure = DecimalField('Exposure (us)', default = 1000, validators=[validators.NumberRange(min=10, max=100000)])
    analog_gain = SelectField('Analog gain', default = 1, choices=[1])
    bitmode = SelectField('Sensor ADC bitmode', default = 12, choices=[10,12])
    illumination = SelectField('Illumination', default = 'off', choices=['on','off'])

    amount = IntegerField('Number of images to capture', default = 1, validators=[validators.NumberRange(min=1, max=20)])
    download_option = SelectField('Download option', default = 'tiff', choices=[('tiff', 'tiff single image'), ('npz', 'numpy array (multi)'), ('zip', 'zip of tiff files (multi)')])

    download = SubmitField(label = 'Download image and stop')
    apply = SubmitField(label = 'Apply settings')

        #     print(camera.picam2.camera_controls["ExposureTime"][0])        
        # print(camera.picam2.camera_controls["ExposureTime"][1])
        # super().__init__(form)

# class RegistrationForm(Form):
#     username = StringField('Username', [validators.Length(min=4, max=25)])
#     email = StringField('Email Address', [validators.Length(min=6, max=35)])
#     password = PasswordField('New Password', [
#         validators.DataRequired(),
#         validators.EqualTo('confirm', message='Passwords must match')
#     ])
#     confirm = PasswordField('Repeat Password')
#     age = DecimalField('Age')

#     accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])
#     print(f'received: {email} {age}')

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user = (form.username.data, form.email.data,
                    form.password.data)
        users.append(user)
        flash('Thanks for registering')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# login_manager = LoginManager(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploadfile', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST': #TODO needs form validation using wtforms
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('download_file', name=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
      <input type=submit value=Download>

    </form>
    '''
from flask import send_from_directory

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name,as_attachment=True)
    
def genFrames(camera):
    # camera.open()
    camera.close()
    time.sleep(.1)
    camera.open()
    time.sleep(.1)
    output = StreamingOutput()
    bitmode = camera.controls['bitmode']
    if bitmode == 12:
        raw_format = SensorFormat('SGRBG12_CSI2P')
    elif bitmode ==10:
        raw_format = SensorFormat('SGRBG10_CSI2P')
    else:
        raw_format = SensorFormat('SGRBG8_CSI2P')

    raw_format.packing = None    
    video_config = camera.picam2.create_video_configuration(main={
                "size": camera.size}, raw={"format": raw_format.format}, buffer_count=2)
    
    # config = picam2.create_still_configuration(raw={"format": raw_format.format}, buffer_count=2)
    camera.picam2.configure(video_config)
    camera.update_controls()
    # camera.picam2.set_controls({"ExposureTime": camera.controls['exposure_us'], "AnalogueGain": camera.controls['gain']})
    camera.start_recording(output)
    if camera.cam_info['Model']=='mira050':
        camera.set_illum_trigger( en_trig_illum = True)
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def captureImage2(camera):
    request = camera.picam2.capture_request()
    request.save("main", "test3.jpg")
    request.release()
    print('caputre successful')


# importing required modules
from zipfile import ZipFile
import os

def get_all_file_paths(directory):
    # initializing empty file paths list
    file_paths = []
    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    # returning all file paths
    return file_paths		



def captureImageRaw(camera):
    request = camera.picam2.capture_request()
    global amount
    # request.save("main", "test3.jpg")
    imgs=[]
    for i in range(amount):
        image = camera.picam2.capture_array("raw").view(np.uint16)
        imgs.append(image)
        metadata = camera.picam2.capture_metadata()
        new = metadata['SensorTimestamp']
        print(f'timestamp meta {metadata}')
        pilim = Image.fromarray(image)
        pilim.save(f"imgraw{i}.tiff")
    # images = camera.picam2.capture_arrays(["raw","raw"])

    print(imgs)
    np.savez('img_array',imgs)

    request.release()

    directory = './'

    # calling function to get all file paths in the directory
    file_paths = get_all_file_paths(directory)

    file_paths = [f for f in pathlib.Path().glob("*.tiff")]    

    print('Following files will be zipped:')
    for file_name in file_paths:
        print(file_name)

    # writing files to a zipfile
    with ZipFile('my_python_files.zip','w') as zip:
        # writing each file one by one
        for file in file_paths:
            zip.write(file)

    print('All files zipped successfully!')		

    print('raw caputre successful')
    return 'done'		

    # raw_format = SensorFormat('SGRBG10_CSI2P')
    # print(raw_format)
    # raw_format.packing = None
    # config = picam2.create_still_configuration(raw={"format": raw_format.format}, buffer_count=2)
    # picam2.configure(config)
    # images = []
    # picam2.set_controls({"ExposureTime": exposure_time , "AnalogueGain": 1.0, "FrameRate":framerate})
    # picam2.start()
    # old = 0
    # new = 0
    # # The raw images can be added directly using 2-byte pixels.
    # for i in range(num_frames):
    #     images.append(picam2.capture_array("raw").view(np.uint16))
    #     metadata = picam2.capture_metadata()
    #     new = metadata['SensorTimestamp']
    #     diff = new - old 
    #     old = new
    #     print(metadata['SensorTimestamp'])
    #     print(diff/1000)

    # print(images[0].shape)
    # print(images[0])
    # for index, image in enumerate(images):
    #     pilim = Image.fromarray(image)
    #     pilim.save(f"imgraw{index}.tiff")


def captureImage(camera):
    camera.close()
    time.sleep(.1)
    print(f'status: {camera.picam2}')
    camera.open()

    print(f'status opened: {camera.picam2.is_open}')
    print(f'status started: {camera.picam2.started}')

    time.sleep(.1)
    status = "failed"
    try:
        camera_config = camera.picam2.create_still_configuration()
        # camera_config = camera.picam2.create_still_configuration(main={ "size": camera.size})
        camera.picam2.configure(camera_config)

        filename = time.strftime("%Y%m%d-%H%M%S") + '.jpg'
        savepath = os.path.join(dirpath, filename)
        camera.picam2.start()
        time.sleep(1)
        # camera.picam2.switch_mode_and_capture_file(camera_config, savepath)
        metadata = camera.picam2.capture_file("./test2.jpg")
        print(f'metadata {metadata}')
        # camera.picam2.capture_file(savepath, filename)
        status = "success"
        print('caputre successful')
    except Exception as e:
        print('capture failed')
        print(e)
    finally:
        pass
        # camera.stop_recording()
        # camera.picam2.stop()
        # camera.picam2.close()
    return {'status': status}



@app.route('/index.html')
def indexhtml():
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
def index():
    global camera
    form = ControlForm(request.form)
    # form = RegistrationForm(request.form)
    global download_option
    global amount
    global cam_info 
    if request.method == 'POST' and form.validate():

        camera.controls['exposure_us']=int(form.exposure.data)
        camera.controls['gain']=int(form.analog_gain.data)
        camera.controls['bitmode']=int(form.bitmode.data)
        camera.controls['illumination']=form.illumination.data
        camera.controls['amount']=int(form.amount.data)
        print(f'form {form.data}')

        if form.data["download"] == True:
            print('download button pressed')
            filename = 'requirements.txt'
            camera.picam2.capture_image()
            return redirect(url_for('capture'))
            # return redirect(url_for('download_file', name=filename))

        # camera.picam2.set_controls({"ExposureTime": exposure, "AnalogueGain": 1.0})

        # users.append(user)
        # flash('Thanks for setting exposure')
        # return render_template('index.html', form=form)
    # return redirect(url_for('indexhtml'))
    #TODO
    # if form.validate_on_submit():
    #     if 'download' in request.form:
    #         pass # do something
    #     elif 'watch' in request.form:
    #         pass # do something else
    return render_template('index.html', form=form, caminfo=camera.cam_info )  # you can customze index.html here



@app.route('/capturesimple')
def capturesimple():
    global camera
    print('capture routinge')
    outcome = captureImageRaw(camera)
    return outcome

@app.route('/capture')
def capture():
    global camera
    print('capture routinge')
    outcome = captureImageRaw(camera)
    # return jsonify(outcome)
    # return redirect(url_for('download_file', name='imgraw.tiff'))
    if download_option == 'zip':
        return redirect(url_for('download_file', name='my_python_files.zip'))
    elif download_option == 'npz':
        return redirect(url_for('download_file', name='img_array.npz'))
    else:
        return redirect(url_for('download_file', name='imgraw0.tiff'))

    return redirect('/')


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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
