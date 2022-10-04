import cv2
import numpy as np
from typing import Optional, Tuple
import sys
import os
import argparse
import time
import logging
import subprocess

# picamera2 
from picamera2 import Picamera2
from picamera2.controls import Controls
picam2 = Picamera2()

# V4L2 control
import v4l2
import fcntl
import ctypes

class CameraStreamInput:
    """
    Initializes a camera stream and returns it as an iterable object
    """
    def __init__(self, video=None, brightness=0.0):
        picam2.preview_configuration.main.size = (572, 768)
        picam2.preview_configuration.main.format = "RGB888"
        picam2.preview_configuration.controls.FrameRate = 100.0
        # Brightness between -1.0 and 1.0
        picam2.preview_configuration.controls.Brightness = brightness
        picam2.preview_configuration.align()
        picam2.configure("preview")
        picam2.start()
        self._index = 0

    def __iter__(self):
        """
        Creates an iterator for this container.
        """
        self._index = 0
        return self

    def __next__(self) -> Optional[Tuple[np.ndarray, int]]:
        """
        @return tuple containing current image and meta data if available, otherwise None
        """
        frame = picam2.capture_array("main")
        self._index += 1
        return (frame, self._index)

class fastIOCTL:

    def __init__(self, printFunc):
        self.__AMS_CAMERA_CID_MIRA050_REG_FLAG_FOR_READ = 0x01
        self.__AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK = 0x02
        self.__AMS_CAMERA_CID_MIRA050_REG_FLAG_BANK = 0x04
        self.__AMS_CAMERA_CID_MIRA050_REG_FLAG_CONTEXT = 0x08
        self.fname = "/dev/v4l-subdev0"
        self.pr = printFunc
        try:
            self.f = os.open(self.fname, os.O_RDWR)
        except:
            self.pr("ERROR: Unable to open driver")
        cp = v4l2.v4l2_capability()
        self.card = cp.card

    def close(self):
        os.close(self.f)
        return (0)

    def execI2C(self, addr, value, rw, print_en=True):
        try:
            if rw > 0:
                # Write register
                reg_flag = 0 & 0xFF
                reg_addr = addr & 0xFFFF
                reg_val = value & 0xFF
                value = (reg_flag << 24) | (reg_addr << 8) | (reg_val);
                subprocess.Popen('v4l2-ctl -d  /dev/v4l-subdev0 --set-ctrl {}=0x{:08x}'.format("mira050_reg_w", value), shell=True)
            else:
                # Dummy write with FLAG_FOR_READ, to cache reg addr for read later
                reg_flag = (self.__AMS_CAMERA_CID_MIRA050_REG_FLAG_FOR_READ | self.__AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK | self.__AMS_CAMERA_CID_MIRA050_REG_FLAG_BANK ) & 0xFF
                reg_addr = addr & 0xFFFF
                reg_val = value & 0xFF
                value = (reg_flag << 24) | (reg_addr << 8) | (reg_val);
                subprocess.Popen('v4l2-ctl -d  /dev/v4l-subdev0 --set-ctrl {}=0x{:08x}'.format("mira050_reg_w", value), shell=True)
                # Read register value with previously cached reg addr
                out_str = subprocess.check_output('v4l2-ctl -d  /dev/v4l-subdev0 --get-ctrl {}'.format("mira050_reg_r"), shell=True)
                out_arr = out_str.decode("utf-8").split(":")
                reg = int(out_arr[1])
                reg_flag = (reg >> 24) & 0xFF
                reg_addr = (reg >> 8) & 0xFFFF
                reg_val = reg & 0xFF
        except:
            if print_en:
                txt = "ERROR: I2C access error to ADDR={},VALUE={},RW={}".format(addr, value, rw)
                self.pr(txt)
            raise IOError(txt)
        return int(reg_val)

input_camera_stream = CameraStreamInput(brightness=0.0)
i2c = fastIOCTL(print)

for frame, frame_idx in input_camera_stream:
    exp_val = i2c.execI2C(0x0011, 0x00, 0)
    print("LSB exp: {}".format(exp_val))
    cv2.imshow('output', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        sys.exit(0)

