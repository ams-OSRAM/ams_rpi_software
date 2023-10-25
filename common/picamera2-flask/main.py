#!/usr/bin/env python
import io
import numpy as np
import pathlib
import time


# importing required modules
from zipfile import ZipFile
from threading import Condition
from camera import Camera, StreamingOutput
from zipfile import ZipFile
from PIL import Image
from flask.views import MethodView
from flask import Flask, jsonify, redirect, render_template, Response, flash, request, url_for, send_from_directory
from flaskext.markdown import Markdown
from urllib.parse import urlparse
from wtforms import Form, BooleanField, StringField, PasswordField, validators, DecimalRangeField, DecimalField, SubmitField , IntegerField, SelectField
#Todo implement logging
import logging
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
#logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

fh = logging.FileHandler('logs.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

log.addHandler(fh)


log.info("app started")
#TODO get rid of these paths


UPLOAD_FOLDER = pathlib.Path(__file__).parent/'images'
UPLOAD_FOLDER.mkdir(parents=False, exist_ok = True)

app = Flask(__name__, template_folder='templates', static_folder='static')
Markdown(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

camera = Camera()
# ensure camera opens only once during debug.
# if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
camera.open()
time.sleep(1)
camera.close()

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
        # log.debug(data)
        log.debug(request.json)
        if id == 'read':
            dict_of_items = request.json
            retval = self.camera.registers.read_register(int(dict_of_items['reg'],16))
            return jsonify(retval)
        if id == 'write':
            # Check is the JSON is a dictionary. If not, assume it is a list of dictionary.
            if isinstance(request.json, dict):
                # JSON is a dictionary, directly parse: {'reg': number, 'val', number}
                dict_of_items = request.json
                retval = self.camera.registers.write_register(int(dict_of_items['reg'],16), int(dict_of_items['val'],16))
                return jsonify(retval)
            else:
                # JSON is not a dictionary. Assume it is a list. Loop over the list.
                for dict_of_items in request.json:
                    retval = self.camera.registers.write_register(int(dict_of_items['reg'],16), int(dict_of_items['val'],16))
                return jsonify(retval)
        if id == 'manual_mode':
            dict_of_items = request.json
            retval = self.camera.registers.set_manual_mode(int(dict_of_items['enable']))
            return jsonify(retval)
        if id == 'power':
            dict_of_items = request.json
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
        log.debug(request.get_data())
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
    download_option = SelectField('Download option', default = 'tiff', choices=[('tiff', 'tiff single image'), ('npz', 'numpy array (multi)'), ('zip', 'zip of tiff files (multi)'), ('jpg', 'jpg compressed image')])

    cam_open = SubmitField(label = '(Re-)open camera')
    cam_close = SubmitField(label = 'Close camera')

    download = SubmitField(label = 'Download image and stop stream')
    apply = SubmitField(label = 'Apply settings and resume stream')

        #     log.debug(camera.picam2.camera_controls["ExposureTime"][0])        
        # log.debug(camera.picam2.camera_controls["ExposureTime"][1])
        # super().__init__(form)

class AdminForm(Form):
    # def __init__(self, form, expmin, expmax):
    sensor = SelectField('Sensor driver', default = None, choices=['mira050','mira050color', 'mira130', 'mira220','mira220color', 'mira016'])
    apply = SubmitField(label = 'Apply settings and reboot')

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
    log.debug(f'camera controls mode {camera.controls.mode} ----')
    if not camera.is_opened:
        camera.open()
    video_config = camera.picam2.create_video_configuration(main={
                "size": camera.sensor_modes[int(camera.controls.mode)]['size']}, raw={"format": camera.sensor_modes[int(camera.controls.mode)]['unpacked'], 'size': camera.sensor_modes[int(camera.controls.mode)]['size']}, buffer_count=2)

    # video_config = camera.picam2.create_video_configuration(main={
    #             "size": camera.size}, raw={"format": camera.raw_format}, buffer_count=2)

    # config = picam2.create_still_configuration(raw={"format": raw_format.format}, buffer_count=2)
    camera.stop_recording()
    camera.picam2.configure(video_config)
    camera.update_controls()
    output = StreamingOutput()
    camera.start_recording(output)
    time.sleep(1)
    log.debug(f"cam controls gain {camera.picam2.camera_controls['AnalogueGain']}")

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



@app.route('/capturefast')
def capturefast(videostream=False):
    """fast raw capture. dont forget to update controls before this."""
    global camera
    #TODO implemnet using completedrequest, see p36 picamera2-manual
    global UPLOAD_FOLDER
    log.debug(f'cam  open {camera.is_opened} {camera.is_started}')

    if not camera.is_opened:
        camera.open()
    camera.update_controls()

    # request.save("main", "test3.jpg")
    if not videostream:
        try:
            if not camera.is_opened:
                camera.open()
            if not camera.is_started:
                camera.picam2.stop()
                still_config = camera.picam2.create_still_configuration(main={
                "size": camera.sensor_modes[int(camera.controls.mode)]['size']}, raw={"format": camera.sensor_modes[int(camera.controls.mode)]['unpacked'], 'size': camera.sensor_modes[int(camera.controls.mode)]['size']}, buffer_count=2)
                # still_config = camera.picam2.create_still_configuration(main={
                #             "size": camera.size}, raw=camera.controls.mode, buffer_count=2)
                camera.picam2.configure(still_config)
                try:
                    camera.picam2.start()
                except RuntimeError:
                    log.debug('already started')
        except RuntimeError:
            log.debug('already started')
        

    # if not camera.is_opened:
    #     camera.open()
    # camera.update_controls()
    from io import BytesIO
    from flask import make_response
    log.debug('testfast')
    # create array
    amount = camera.controls.amount
    size = camera.sensor_modes[int(camera.controls.mode)]['size']
    width = size[0]
    height = size[1]

    
    request = camera.picam2.capture_request()
    log.debug('capture req started')

    imgs=[]
    for i in range(amount):
        if int(camera.sensor_modes[int(camera.controls.mode)]['bit_depth'])==8:
            image = camera.picam2.capture_array("raw").view(np.uint8)
        else:
            image = camera.picam2.capture_array("raw").view(np.uint16)
        imgs.append(image[0:height,0:width])



    request.release()
    #create bytes stream
    stream = io.BytesIO()  
    np.savez(stream, A=imgs)  
    stream.seek(0)
    response = make_response(stream.getvalue())
    response.headers.set('Content-Type', 'image/jpeg')
    return response



@app.route('/captureraw')
def captureImageRaw(videostream=False):
    global camera
    #TODO implemnet using completedrequest, see p36 picamera2-manual
    global UPLOAD_FOLDER
    if not camera.is_opened:
        camera.open()
    camera.update_controls()

    # request.save("main", "test3.jpg")
    if not videostream:
        try:
            if not camera.is_opened:
                camera.open()
            if camera.is_started:
                camera.picam2.stop()
        except RuntimeError:
            log.debug('already started')
        still_config = camera.picam2.create_still_configuration(main={
                "size": camera.sensor_modes[int(camera.controls.mode)]['size']}, raw={"format": camera.sensor_modes[int(camera.controls.mode)]['unpacked'], 'size': camera.sensor_modes[int(camera.controls.mode)]['size']}, buffer_count=2)
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
        filename = str(f"{UPLOAD_FOLDER}/imgisp{i}.jpg")
        camera.picam2.capture_file(filename)
        if int(camera.sensor_modes[int(camera.controls.mode)]['bit_depth'])==8:
            image = camera.picam2.capture_array("raw").view(np.uint8)
        else:
            image = camera.picam2.capture_array("raw").view(np.uint16)
        size = camera.sensor_modes[int(camera.controls.mode)]['size']
        width = size[0]
        height = size[1]
        image = image[0:height,0:width]
        imgs.append(image)
        log.debug(f'size of image: {image.shape}')
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

    if not videostream:
        log.debug('Stopping picam2')
        camera.picam2.stop()
        camera.close()

    return 'done'		



@app.route('/index.html')
def indexhtml():
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
def index():

    o = urlparse(request.base_url)
    host = o.hostname
    notebook = 'http://'+host+':8888'
    log.debug(f'link to jupyter is {notebook}')
    global camera
    form = ControlForm(request.form)

    form.mode.choices = [(ind, f"{mode['bit_depth']} bit {mode['size']}") for ind,mode  in enumerate(camera.sensor_modes)]
    current_mode = camera.sensor_modes[int(camera.controls.mode)]
    min = current_mode['exposure_limits'][0]
    max = current_mode['exposure_limits'][1]

    if camera.cam_info['Model']=='mira220':
        form.exposure_us.validators[0]= validators.NumberRange(min=min, max=max)
        form.analog_gain.choices=[1]

    elif camera.cam_info['Model']=='mira050':
        form.analog_gain.choices=[1,2,4]

    elif camera.cam_info['Model']=='mira016':
        form.analog_gain.choices=[1]

    # form.bitmode.choices = [8,10]
    if request.method == 'POST' and form.validate():
        form.populate_obj(camera.controls)


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

        if form.data["cam_open"] == True:
            log.debug('cam_open pressed')
            if camera.is_opened:
                camera.close()
            camera.open()

        if form.data["cam_close"] == True:
            log.debug('cam_close pressed')
            camera.close()
            return render_template('closed.html', form=form, model = camera.cam_info['Model'], caminfo=camera.sensor_modes[int(camera.controls.mode)] )  # you can customze index.html here

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
    return render_template('index.html', notebook=notebook, form=form, model = camera.cam_info['Model'], caminfo=camera.sensor_modes[int(camera.controls.mode)] )  # you can customze index.html here


@app.route('/changelog', methods=['GET', 'POST'])
def changelog():
    global camera
    #     if 'download' in request.form:
    #         pass # do something
    #     elif 'watch' in request.form:
    #         pass # do something else
    with open('logs.log','r',newline='') as f:
        logs = f.readlines()
#        logs = ['a','b','c']
    with open('../../CHANGELOG.md') as f:
        mkd_text = f.read()
    #mkd_text = "## Your Markdown Here "
    return render_template('changelog.html',mkd_text=mkd_text, logs=logs)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global camera
    form = AdminForm(request.form)

    if request.method == 'POST' and form.validate():
        # form.populate_obj(camera.controls)
        # log.debug(f'form data {camera.controls.json}')
        # log.debug(f'form data type {json.loads(camera.controls.mode)}')

        log.debug(f'form {form.data}')
        # camera.update_controls()
        if form.data["sensor"]:
            log.debug('download button pressed')
            import os
            sp = os.popen('echo {} | sudo -S sed -i "s/^dtoverlay=mira.*$/dtoverlay={}/" /boot/config.txt'.format('pi', form.data["sensor"]))
            result = sp.read()
            sp = os.popen('echo {} | sudo reboot'.format('pi'))
            result = sp.read()
            
            # grep -q '^dtoverlay=mira*' /boot/config.txt && sed -i 's/\r$//;s/^dtoverlay=mira.*$/dtoverlay=mira016/' /boot/config.txt
            # grep -q '^dtoverlay=mira*' /boot/config.txt || echo "dtoverlay=mira016" >> /boot/config.txt
            # echo "Mira added to dtoverlay. Below is /boot/config.txt"
            # cat /boot/config.txt

            # filename = 'requirements.txt'

            # camera.picam2.capture_image()
            # return redirect(url_for('capture'))
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
    return render_template('admin.html', form=form, model = camera.cam_info['Model'], caminfo=camera.sensor_modes[int(camera.controls.mode)] )  # you can customze index.html here



@app.route('/capture')
def capture():
    global camera
    download_option = camera.controls.download_option
    log.debug('capture routinge')
    outcome = captureImageRaw(True)

    if download_option == 'zip':
        log.debug('zip dl option')
        return redirect(url_for('download_file', name='my_images.zip'))
    elif download_option == 'npz':
        return redirect(url_for('download_file', name='img_array.npz'))
    elif download_option == 'jpg':
        return redirect(url_for('download_file', name='imgisp0.jpg'))
    else:
        return redirect(url_for('download_file', name='imgraw0.tiff'))



# defines the route that will access the video feed and call the feed function
@app.route('/video_feed')
def video_feed():
    return Response(genFrames(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

#

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
