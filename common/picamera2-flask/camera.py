import io
import sys
import time
import logging

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from picamera2.sensor_format import SensorFormat
from threading import Condition
from config_parser import ConfigParser
from driver_access import v4l2Ctrl

log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
log.addHandler(ch)

fh = logging.FileHandler("logs.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

log.addHandler(fh)


log.info("app started")

sys.path.append("../common")
sys.path.append("../../common")


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class Registers:
    def __del__(self):
        self.set_manual_mode(False)
        self.close()

    def __init__(self, sensor) -> None:
        self.register_sequence = ["test"]
        self.i2c = v4l2Ctrl(sensor, printFunc=print)
        self.power = True
        self.manual_mode = False
        self.stream_ctrl = False
        self.illum = True
        self.set_manual_mode(False)

    def set_power(self, enable=True):
        self.power = enable
        log.debug(f" {__class__} {enable}")
        if enable:
            # flags are same for all sensors
            self.i2c.rwReg(
                addr=0x0,
                value=0,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_POWER_ON,
            )
        else:
            self.i2c.rwReg(
                addr=0x0,
                value=0,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_POWER_OFF,
            )
        # Must wait for a while for power on/off. Otherwise subsequent actions may hang.
        time.sleep(1)

    def set_manual_mode(self, enable=False):
        log.debug(f" {__class__} {enable}")
        self.manual_mode = enable
        if enable:
            self.i2c.rwReg(
                addr=0x0,
                value=0,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_REG_UP_OFF,
            )
            self.i2c.rwReg(
                addr=0x0,
                value=0,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_RESET_OFF,
            )
        else:
            self.i2c.rwReg(
                addr=0x0,
                value=0,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_REG_UP_ON,
            )
            self.i2c.rwReg(
                addr=0x0,
                value=0,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_RESET_ON,
            )

    def set_stream_ctrl(self, enable = False):
        log.debug(f" {__class__} {enable}")
        self.stream_ctrl = enable
        if enable:
            self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_STREAM_CTRL_ON)
        else:
            self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_STREAM_CTRL_OFF)

    def set_illum_trig(self, enable = True):
        log.debug(f" {__class__} {enable}")
        self.illum = enable
        if enable:
            self.i2c.rwReg(
                addr=0x00,
                value=0x00,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_TRIG_ON,
            )
            self.i2c.rwReg(
                addr=0x00,
                value=0x00,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_EXP_T_ON,
            )
        else:
            self.i2c.rwReg(
                addr=0x00,
                value=0x00,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_TRIG_OFF,
            )
            self.i2c.rwReg(
                addr=0x00,
                value=0x00,
                rw=1,
                flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_EXP_T_OFF,
            )

    def write_register(self, reg, val):
        exp_val = self.i2c.rwReg(addr=reg, value=val, rw=1, flag=0)
        log.debug(f" {__class__} writereg {reg} {val} {exp_val}")

        return exp_val

    def read_register(self, reg):
        exp_val = self.i2c.rwReg(addr=reg, value=0, rw=0, flag=0)
        log.debug(f" {__class__} reg read {reg} {exp_val}")
        return exp_val

    @property
    def json(self):
        return self.__dict__


class Controls:
    def __init__(self) -> None:
        self.amount = 1
        self.exposure_us = 10000
        self.analog_gain = 1.0
        self.illumination = True
        self.mode = 0

    @property
    def json(self):
        return self.__dict__


class Camera:
    """
        states:
        open
        started
        stopped
        closed

        sensor properties:
        picam2.sensor_modes
        >>> pi.sensor_modes
    [{'format': SGRBG10_CSI2P, 'unpacked': 'SGRBG10', 'bit_depth': 10, 'size': (576, 768), 'fps': 50.0, 'crop_limits': (0, 0, 576, 768), 'exposure_limits': (96, 1700107, None)}, {'format': SGRBG12_CSI2P, 'unpacked': 'SGRBG12', 'bit_depth': 12, 'size': (576, 768), 'fps': 50.0, 'crop_limits': (0, 0, 576, 768), 'exposure_limits': (96, 1700107, None)}, {'format': SGRBG8, 'unpacked': 'SGRBG8', 'bit_depth': 8, 'size': (576, 768), 'fps': 50.0, 'crop_limits': (0, 0, 576, 768), 'exposure_limits': (96, 1700107, None)}]

    {'Sharpness': (0.0, 16.0, 1.0), 'AwbEnable': (False, True, None), 'AeExposureMode': (0, 3, 0), 'Brightness': (-1.0, 1.0, 0.0), 'AeEnable': (False, True, None), 'ExposureTime': (96, 1700107, None), 'AeConstraintMode': (0, 3, 0), 'NoiseReductionMode': (0, 4, 0), 'FrameDurationLimits': (20001, 1700210, None), 'AwbMode': (0, 7, 0), 'ExposureValue': (-8.0, 8.0, 0.0), 'ColourCorrectionMatrix': (-16.0, 16.0, None), 'Contrast': (0.0, 32.0, 1.0), 'Saturation': (0.0, 32.0, 1.0), 'AeMeteringMode': (0, 3, 0), 'ScalerCrop': (libcamera.Rectangle(0, 0, 64, 64), libcamera.Rectangle(0, 0, 576, 768), libcamera.Rectangle(0, 168, 576, 432)), 'ColourGains': (0.0, 32.0, None), 'AnalogueGain': (1.0, 1.055999994277954, None)}

    >>> pi.global_camera_info()
    [{'Model': 'mira050', 'Location': 2, 'Rotation': 0, 'Id': '/base/soc/i2c0mux/i2c@1/mira050@36'}]

    """

    def __del__(self):
        self.close()

    def __init__(self, exposure_us=1000, analog_gain=1, bitmode=12, illumination=True):
        # {'amount': 1, 'exposure_us' : exposure_us, 'gain' : gain, 'bitmode' : bitmode, 'illumination': illumination}
        self.controls = Controls()
        self.picam2 = None
        self.form_data = None
        self.cam_info = None
        self.raw_format = "SGRBG10_CSI2P"
        self.registers = Registers("mira220")  # TODO

        log.debug("cam class init")

    def open(self):
        if not (self.picam2):
            try:
                self.picam2 = Picamera2()
            except RuntimeError as e:
                log.error(f"can't start picam2")
                return
            self.cam_info = self.picam2.camera_properties
            self.sensor_modes = self.picam2.sensor_modes

            log.debug(f"cam info {self.cam_info}")
            log.debug(f"cam modes {self.sensor_modes}")

            pixelsize = self.picam2.camera_properties["PixelArraySize"]
            self.size = (pixelsize[0], pixelsize[1])
        if self.is_started:
            self.stop_recording()
        if not (self.picam2.is_open):
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
        log.debug("close cam")
        if self.picam2:
            self.stop_recording()
            if self.picam2.is_open:
                self.picam2.close()

    def update_controls(self):
        if not self.is_opened:
            self.open()
        print("setting controls")
        print(self.controls.exposure_us)
        # fps=self.sensor_modes[int(self.controls.mode)]['fps']
        # if 1/fps > exposure
        # fps = 1/exposure
        self.picam2.set_controls(
            {
                "ExposureTime": int(self.controls.exposure_us),
                "FrameDurationLimits": (10000, 1000000),
                "AnalogueGain": float(self.controls.analog_gain),
            }
        )

        # if self.controls.bitmode == 12:
        #     self.raw_format = SensorFormat('SGRBG12_CSI2P')
        # elif self.controls.bitmode ==10:
        #     self.raw_format = SensorFormat('SGRBG10_CSI2P')
        # else:
        #     self.raw_format = SensorFormat('SGRBG8_CSI2P')
        # self.raw_format.packing = None

        if self.cam_info["Model"] == "mira050":
            if self.controls.illumination == "on":
                print("enable illum")
                #     self.set_illum_trigger( en_trig_illum = True)
                i2c = v4l2Ctrl(sensor="mira050", printFunc=print)
                i2c.rwReg(
                    addr=0x00,
                    value=0x00,
                    rw=1,
                    flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_TRIG_ON,
                )
                i2c.rwReg(
                    addr=0x00,
                    value=0x00,
                    rw=1,
                    flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_EXP_T_ON,
                )
            else:
                print("disable illum")
                i2c = v4l2Ctrl(sensor="mira050", printFunc=print)

                # self.set_illum_trigger( en_trig_illum = False)
                i2c.rwReg(
                    addr=0x00,
                    value=0x00,
                    rw=1,
                    flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_TRIG_OFF,
                )
        elif self.cam_info["Model"] == "mira016":
            if self.controls.illumination == "on":
                print("enable illum")
                #     self.set_illum_trigger( en_trig_illum = True)
                i2c = v4l2Ctrl(sensor="MIRA016", printFunc=print)
                i2c.rwReg(
                    addr=0x00,
                    value=0x00,
                    rw=1,
                    flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_TRIG_ON,
                )
                i2c.rwReg(
                    addr=0x00,
                    value=0x00,
                    rw=1,
                    flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_EXP_T_ON,
                )
            else:
                print("disable illum")
                i2c = v4l2Ctrl(sensor="MIRA016", printFunc=print)

                # self.set_illum_trigger( en_trig_illum = False)
                i2c.rwReg(
                    addr=0x00,
                    value=0x00,
                    rw=1,
                    flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_TRIG_OFF,
                )


    def start_recording(self, output):
        self.picam2.start_recording(JpegEncoder(), FileOutput(output))

    def stop_recording(self):
        log.debug("stop recording cam")

        if self.is_started:
            print(f"status of is started: {self.is_started}")
            try:
                self.picam2.stop_recording()
            except Exception as e:
                print(e)
                log.error(f"ERROR {e}")
