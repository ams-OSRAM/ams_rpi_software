#!/usr/bin/env python
import io
import numpy as np
import pathlib
import time
import os
import sys
import json

# importing required modules
from zipfile import ZipFile
from threading import Condition
from camera import Camera, StreamingOutput
from zipfile import ZipFile
from PIL import Image
from flask.views import MethodView
from flask import Flask, jsonify, redirect, render_template, Response, flash, request, url_for, send_from_directory

from werkzeug.utils import secure_filename
from wtforms import Form, BooleanField, StringField, PasswordField, validators, DecimalRangeField, DecimalField, SubmitField , IntegerField, SelectField
#Todo implement logging
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
log.info("Hello, world")
#TODO get rid of these paths


UPLOAD_FOLDER = pathlib.Path(__file__).parent/'images'
UPLOAD_FOLDER.mkdir(parents=False, exist_ok = True)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

camera = Camera()
# ensure camera opens only once during debug.
if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    camera.open()
else:
    log.debug("Hello, world")

class RegisterItemAPI(MethodView):
    """
    definition of register api
    get: read a register
    put: write a register
    
    """
    def __init__(self,camera):
        self.camera = camera
    def get(self, id):
        ret = self.camera.registers.json[id]
        return jsonify(ret)
    def put(self, id):
        log.debug(f"put {__class__} put ID: {id} ")
        # data= request.get_data()
        # print(data)
        print(request.json)
        dict_of_items = request.json
        if id == 'read':
            retval = self.camera.registers.read_register(int(dict_of_items['reg'],16))
            return jsonify(retval)
        if id == 'write':
            retval = self.camera.registers.write_register(int(dict_of_items['reg'],16), int(dict_of_items['val'],16))
            return jsonify(retval)
        if id == 'manual_mode':
            retval = self.camera.registers.set_manual_mode(int(dict_of_items['enable']))
            return jsonify(retval)
        if id == 'power':
            retval = self.camera.registers.set_power(int(dict_of_items['enable']))
            return jsonify(retval)
        
        # for key,value in dict_of_items.items():
        # self.camera.controls.json[key] = value

        # self.camera.controls.json = request.json #TODO make a setter

        # self.camera.controls.json = data
        # self.camera.update_controls()
        # return jsonify(camera.controls.json)
    # def post(self):
    #     log.debug("put request {request.json}")
    #     self.camera.registers.json = request.json #TODO make a setter
    #     # self.camera.update_controls()
    #     return request.json
        # return 'hello put'

class ControlGroupAPI(MethodView):
    def __init__(self,camera):
        self.camera = camera
    def get(self):
        return jsonify(camera.controls.json)
    def put(self):
        log.debug(f"put {__class__} ")
        data= request.get_data()
        print(data)
        print(request.json)
        dict_of_items = request.json
        for key,value in dict_of_items.items():
            self.camera.controls.json[key] = value

        # self.camera.controls.json = request.json #TODO make a setter

        # self.camera.controls.json = data
        self.camera.update_controls()
        return jsonify(camera.controls.json)

        # self.camera.update_controls()
        # return request.json
        # return 'hello put'

class ControlItemAPI(MethodView):
    def __init__(self,camera):
        self.camera = camera
    def get(self, id):
        return jsonify(camera.controls.json[id])
    def put(self,id):
        log.debug(f"put {__class__} ")
        print(request.get_data())
        if id == 'illumination':
            data= bool(request.get_data())
        elif id =='analog_gain':
            data= float(request.get_data())
        else:
            data= int(request.get_data())

        self.camera.controls.json[id] = data
        self.camera.update_controls()
        return jsonify(data)
        # return 'hello put'

def register_api(app: Flask, camera: Camera , name: str, name2: str):
    item = ControlItemAPI.as_view(f"{name}-item", camera)
    group = ControlGroupAPI.as_view(f"{name}-group", camera)
    regitem = RegisterItemAPI.as_view(f"{name2}-regitem", camera)

    app.add_url_rule(f"/{name}/<id>", view_func=item)
    app.add_url_rule(f"/{name}/", view_func=group)
    app.add_url_rule(f"/{name2}/<id>", view_func=regitem)

register_api(app, camera, 'controls', 'registers')

class ControlForm(Form):
    # def __init__(self, form, expmin, expmax):
    exposure_us = DecimalField('Exposure (us)', default = 1000, validators=[validators.NumberRange(min=10, max=100000)])
    analog_gain = SelectField('Analog gain', default = 1, choices=[1, 2, 4])
    # bitmode = SelectField('Sensor ADC bitmode', default = 12, choices=[8, 10,12])
    mode = SelectField('Sensor mode', default = None, choices=[])

    illumination = SelectField('Illumination', default = 'off', choices=['on','off'])

    amount = IntegerField('Number of images to capture', default = 1, validators=[validators.NumberRange(min=1, max=20)])
    download_option = SelectField('Download option', default = 'tiff', choices=[('tiff', 'tiff single image'), ('npz', 'numpy array (multi)'), ('zip', 'zip of tiff files (multi)')])

    download = SubmitField(label = 'Download image and stop stream')
    apply = SubmitField(label = 'Apply settings and resume stream')

        #     log.debug(camera.picam2.camera_controls["ExposureTime"][0])        
        # log.debug(camera.picam2.camera_controls["ExposureTime"][1])
        # super().__init__(form)



@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name,as_attachment=True)
    
def genFrames(camera, only_configure=False):
    # camera.open()
    # camera.close()
    # time.sleep(.1)
    # camera.open()
    time.sleep(.1)
    log.info(f'camea controls mode {camera.controls.mode} ----------------------------------------')
    video_config = camera.picam2.create_video_configuration(main={
                "size": camera.sensor_modes[int(camera.controls.mode)]['size']}, raw={"format": camera.sensor_modes[int(camera.controls.mode)]['format'], 'size': camera.sensor_modes[int(camera.controls.mode)]['size']}, buffer_count=2)

    # video_config = camera.picam2.create_video_configuration(main={
    #             "size": camera.size}, raw={"format": camera.raw_format}, buffer_count=2)

    # config = picam2.create_still_configuration(raw={"format": raw_format.format}, buffer_count=2)
    camera.stop_recording()
    camera.picam2.configure(video_config)
    camera.update_controls()
    output = StreamingOutput()
    camera.start_recording(output)
    time.sleep(1)
    log.info(f"cam controls gain {camera.picam2.camera_controls['AnalogueGain']}")

    # camera.picam2.set_controls({"ExposureTime": camera.controls['exposure_us'], "AnalogueGain": camera.controls['gain']})
    if only_configure:
        return
    else:


        while True:
            with output.condition:
                output.condition.wait()
                frame = output.frame
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/captureraw')
def captureImageRaw(videostream=False):
    global camera
    #TODO implemnet using completedrequest, see p36 picamera2-manual
    global UPLOAD_FOLDER
    camera.update_controls()

    # request.save("main", "test3.jpg")
    if not videostream:
        try:
            camera.picam2.stop()
        except RuntimeError:
            log.debug('already started')
        still_config = camera.picam2.create_still_configuration(main={
                "size": camera.sensor_modes[int(camera.controls.mode)]['size']}, raw={"format": camera.sensor_modes[int(camera.controls.mode)]['format'], 'size': camera.sensor_modes[int(camera.controls.mode)]['size']}, buffer_count=2)

        # still_config = camera.picam2.create_still_configuration(main={
        #             "size": camera.size}, raw=camera.controls.mode, buffer_count=2)
        camera.picam2.configure(still_config)
        try:
            camera.picam2.start()
        except RuntimeError:
            log.debug('already started')
    request = camera.picam2.capture_request()
    amount = camera.controls.amount
    camera.update_controls()

    imgs=[]
    for i in range(amount):
        if int(camera.sensor_modes[int(camera.controls.mode)]['bit_depth'])==8:
            image = camera.picam2.capture_array("raw").view(np.uint8)
        else:
            image = camera.picam2.capture_array("raw").view(np.uint16)
        imgs.append(image)
        metadata = camera.picam2.capture_metadata()
        new = metadata['SensorTimestamp']
        pilim = Image.fromarray(image)
        filename = str(f"{UPLOAD_FOLDER}/imgraw{i}.tiff")
        pilim.save(filename)
    # images = camera.picam2.capture_arrays(["raw","raw"])

    np.savez(UPLOAD_FOLDER/'img_array',imgs)
    request.release()
    # calling function to get all file paths in the directory
    file_paths = [f for f in UPLOAD_FOLDER.glob("*.tiff")]    

    for file_name in file_paths:
            log.debug(f'zip {file_name}')

    #TODO this does not take into account the amount properly
    # writing files to a zipfile
    with ZipFile(UPLOAD_FOLDER/'my_images.zip','w') as zip:
        # writing each file one by one
        for file in file_paths:
            zip.write(file, arcname=file.name)
    # for f in file_paths:
    #     os.remove(f)

    log.debug('raw caputre successful')
    return 'done'		



@app.route('/index.html')
def indexhtml():
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
def index():
    global camera
    form = ControlForm(request.form)

    for mode in camera.sensor_modes:
        print(mode)

    form.mode.choices = [(ind, f"{mode['bit_depth']} bit {mode['size']}") for ind,mode  in enumerate(camera.sensor_modes)]
    current_mode = camera.sensor_modes[int(camera.controls.mode)]
    min = current_mode['exposure_limits'][0]
    max = current_mode['exposure_limits'][1]

    if camera.cam_info['Model']=='mira220':
        form.exposure_us.validators[0]= validators.NumberRange(min=min, max=max)
        form.analog_gain.choices=[1]

    elif camera.cam_info['Model']=='mira050':
        form.analog_gain.choices=[1,2,4]


    # form.bitmode.choices = [8,10]
    if request.method == 'POST' and form.validate():
        form.populate_obj(camera.controls)
        print(f'form data {camera.controls.json}')
        print(f'form data type {json.loads(camera.controls.mode)}')

        # camera.controls['amount']=int(form.amount.data)
        # camera.controls['download_option']=str(form.download_option.data)
        # camera.controls['exposure_us']=int(form.exposure.data)
        # camera.controls['gain']=int(form.analog_gain.data)
        # camera.controls['bitmode']=int(form.bitmode.data)
        # camera.controls['illumination']=form.illumination.data
        log.debug(f'form {form.data}')
        camera.update_controls()
        if form.data["download"] == True:
            log.debug('download button pressed')
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
    return render_template('index.html', form=form, model = camera.cam_info['Model'], caminfo=camera.sensor_modes[int(camera.controls.mode)] )  # you can customze index.html here




@app.route('/capture')
def capture():
    global camera
    download_option = camera.controls.download_option
    log.debug('capture routinge')
    outcome = captureImageRaw()
    if not camera.is_opened:
        log.debug('camera not opened, return to main page')
        return redirect('/')

    if download_option == 'zip':
        log.debug('zip dl option')
        return redirect(url_for('download_file', name='my_images.zip'))
    elif download_option == 'npz':
        return redirect(url_for('download_file', name='img_array.npz'))
    else:
        return redirect(url_for('download_file', name='imgraw0.tiff'))



# defines the route that will access the video feed and call the feed function
@app.route('/video_feed')
def video_feed():
    return Response(genFrames(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

#

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
