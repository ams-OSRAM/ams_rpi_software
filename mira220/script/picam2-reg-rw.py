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

if __name__ == "__main__":

    # Initialize classes
    input_camera_stream = CameraStreamInput(width=960, height=720, AeEnable=True)
    i2c = v4l2Ctrl(sensor="mira220", printFunc=print)

    # Manually power on the sensor
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_ON)

    # Before stream on, upload register sequence
    # Dummy example: uploading a list of values for LSB of exposure reg.
    # for reg_val in range(1,10):
    #    exp_val = i2c.rwReg(addr=0x100C, value=reg_val, rw=1, flag=0)


    # Start streaming. Upload long register sequence before this step.
    input_camera_stream.start()

    last_time = time.time()

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        exp_lo = i2c.rwReg(addr=0x100C, value=0, rw=0, flag=0)
        exp_hi = i2c.rwReg(addr=0x100D, value=0, rw=0, flag=0)
        exp = exp_hi * 256 + exp_lo
        print(f"Exposure: {exp}")
        # GUI element
        current_time = time.time()
        fps = 1 / (current_time - last_time)
        cv2.putText(frame, f"fps: {fps:.1f}",
                (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow('output', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print(f"Manually power off the sensor via V4L2 interface.")
            i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_OFF)
            sys.exit(0)
        last_time = current_time

