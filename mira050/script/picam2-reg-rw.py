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

    def start(self):
        picam2.start()

class v4l2Ctrl:
    # Most significant Byte is flag, and most significant bit is unused.
    AMS_CAMERA_CID_MIRA050_REG_FLAG_FOR_READ = 0b00000001
    AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK = 0b00000010
    AMS_CAMERA_CID_MIRA050_REG_FLAG_BANK     = 0b00000100
    AMS_CAMERA_CID_MIRA050_REG_FLAG_CONTEXT  = 0b00001000
    # When sleep bit is set, the other 3 Bytes is sleep values in us.
    AMS_CAMERA_CID_MIRA050_REG_FLAG_SLEEP_US = 0b00010000
    # Bit 6&7 of flag are combined to specify I2C dev (default is Mira)
    AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_SEL  = 0b01100000
    AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_MIRA = 0b00000000
    AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_PMIC = 0b00100000
    AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_UC   = 0b01000000
    AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_TBD  = 0b01100000
 
    def __init__(self, printFunc):
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

    def rwReg(self, addr, value, rw, flag=0, print_en=True):
        try:
            if rw > 0:
                # Write register
                reg_flag = ((~ self.AMS_CAMERA_CID_MIRA050_REG_FLAG_FOR_READ) & flag) & 0xFF
                reg_addr = addr & 0xFFFF
                reg_val = value & 0xFF
                value = (reg_flag << 24) | (reg_addr << 8) | (reg_val);
                subprocess.Popen('v4l2-ctl -d  /dev/v4l-subdev0 --set-ctrl {}=0x{:08x}'.format("mira050_reg_w", value), shell=True)
            else:
                # Dummy write with FLAG_FOR_READ, to cache reg addr for read later
                reg_flag = (self.AMS_CAMERA_CID_MIRA050_REG_FLAG_FOR_READ | flag ) & 0xFF
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

if __name__ == "__main__":

    # Initialize classes
    input_camera_stream = CameraStreamInput(brightness=0.0)
    i2c = v4l2Ctrl(print)

    # Before stream on, upload register sequence
    # Test by uploading a list of values for LSB of exposure reg
    for reg_val in range(1,10):
        exp_val = i2c.rwReg(addr=0x0011, value=reg_val, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK | i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_BANK)

    input_camera_stream.start()

    # Test by reading VERSION_ID
    VERSION_ID = i2c.rwReg(addr=0x011B, value=0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK)
    print("VERSION_ID: {}".format(VERSION_ID))

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        # Test by reading CURRENT_ACTIVE_CONTEXT, NEXT_ACTIVE_CONTEXT
        CURRENT_ACTIVE_CONTEXT = i2c.rwReg(addr=0x4002, value=0, rw=0, flag=0)
        print("CURRENT_ACTIVE_CONTEXT: {}".format(CURRENT_ACTIVE_CONTEXT))
        # GUI element
        cv2.imshow('output', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit(0)

