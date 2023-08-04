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
from picam2cv2 import CameraStreamInput
from driver_access import v4l2Ctrl
from config_parser import ConfigParser

if __name__ == "__main__":

    # Before stream on, upload register sequence
    # Create a config parse to parse the register sequence txt
    config_parser = ConfigParser()
    reg_seq = config_parser.parse_file('config_files/Mira016_Register_Writes_10bit_60fps_1xgain.txt')
    print(f"Parsed {len(reg_seq)} register writes from file.")

    # Create a v4l2Ctrl class for register read/write over i2c.
    i2c = v4l2Ctrl(sensor="mira016", printFunc=print)

    #########################################################
    # Important note for Mira016:
    # If user wants to upload reg sequence txt:
    # (1) manually power off the sensor
    # (2) upload register sequence
    # (3) optionally manaully power on the sensor
    # Such that the reg seq writes are buffer by driver.
    # Driver writes the reg seq to sensor after "start()".
    # Reversing (2) and (3) hangs mira016.
    #########################################################

    # (1) Manually power off the sensor
    print(f"Manually power off the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_POWER_OFF)
    time.sleep(3)

    # (2) Upload register sequence from txt file
    print(f"Writing {len(reg_seq)} registers to driver buffer via V4L2 interface.")
    for reg in reg_seq:
        exp_val = i2c.rwReg(addr=reg[0], value=reg[1], rw=1, flag=0)

    # (3) Manually power on the sensor
    print(f"Manually power on the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_POWER_ON)

    # Disable base register sequence upload (overwriting skip-reg-upload in dtoverlay )
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_REG_UP_OFF)

    # Initialize camera stream according to width, height, bit depth etc. from register sequence
    input_camera_stream = CameraStreamInput(width=400, height=400, AeEnable=False, FrameRate=50.0, bit_depth=10)

    # Configure to use "raw" (rather than "main")
    input_camera_stream.capture_array = "raw"

    # Start streaming. Upload long register sequence before this step.
    input_camera_stream.start()

    last_time = time.time()

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        current_time = time.time()
        fps = 1 / (current_time - last_time)
        print(f"frame_idx: {frame_idx}, frame.shape: {frame.shape}, fps: {fps}, output: capture_{frame_idx}.raw")
        frame.astype(np.uint8).tofile(f"capture_{frame_idx}.raw")
        if frame_idx >= 5:
            print(f"Manually power off the sensor via V4L2 interface.")
            i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_POWER_OFF)
            sys.exit(0)
        last_time = current_time

