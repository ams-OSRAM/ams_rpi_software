import cv2
import numpy as np
from typing import Optional, Tuple
import sys
import os
import argparse
import time
import logging
import subprocess

sys.path.append("../../common")
# from picam2cv2 import CameraStreamInput
from driver_access import v4l2Ctrl
from config_parser import ConfigParser


import numpy as np
from picamera2 import Picamera2
from picamera2.sensor_format import SensorFormat

do_upload = True
exposure_time = 60000
num_frames = 6
framerate = 100
# Configure an unpacked raw format as these are easier to add.

picam2 = Picamera2()

raw_format = SensorFormat('SGRBG10_CSI2P')
print(raw_format)

# Before stream on, upload register sequence
# Create a config parse to parse the register sequence txt
config_parser = ConfigParser()
reg_seq = config_parser.parse_file('config_files/Mira050_register_sequence_10bhsgain1_test2.txt')
print(f"Parsed {len(reg_seq)} register writes from file.")

# Create a v4l2Ctrl class for register read/write over i2c.
i2c = v4l2Ctrl(sensor="mira050", printFunc=print)
# Disable base register sequence upload (overwriting skip-reg-upload in dtoverlay )
i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_REG_UP_OFF)
# Upload register sequence from txt file
print(f"Writing {len(reg_seq)} registers to sensor via V4L2 interface.")

if do_upload==True:
    for reg in reg_seq:
        exp_val = i2c.rwReg(addr=reg[0], value=reg[1], rw=1, flag=0)
# Disable reset during stream on or off
i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_RESET_OFF)

# Initialize camera stream according to width, height, bit depth etc. from register sequence
# input_camera_stream = CameraStreamInput(width=572, height=768, AeEnable=False, FrameRate=50.0, bit_depth=10)


# raw_format = SensorFormat(picam2.sensor_format)

raw_format = SensorFormat('SGRBG10_CSI2P')
print(raw_format)
raw_format.packing = None
config = picam2.create_still_configuration(raw={"format": raw_format.format}, buffer_count=3)
picam2.configure(config)
images = []
picam2.set_controls({"AeEnable":False})

# picam2.set_controls({"ExposureTime": exposure_time , "AnalogueGain": 1.0, "FrameRate":framerate, "AeEnable":False})
picam2.start()
old = 0
new = 0
# The raw images can be added directly using 2-byte pixels.
for i in range(num_frames):
    images.append(picam2.capture_array("raw").view(np.uint16))
    metadata = picam2.capture_metadata()
    new = metadata['SensorTimestamp']
    diff = new - old 
    old = new
    print(metadata['SensorTimestamp'])
    print(diff/1000)

print(images[0].shape)
print(images[0])

# Test by reading VERSION_ID
VERSION_ID = i2c.rwReg(addr=0x011B, value=0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK)
print("VERSION_ID: {}".format(VERSION_ID))

