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
    input_camera_stream = CameraStreamInput(width=572, height=768, AeEnable=True)
    i2c = v4l2Ctrl(sensor="mira050", printFunc=print)

    # Before stream on, upload register sequence
    # Dummy example: uploading a list of values for LSB of exposure reg.
    # for reg_val in range(1,10):
    #    exp_val = i2c.rwReg(addr=0x0011, value=reg_val, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK | i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_BANK)

    # Configure sensitivity of event detection between 0 (insensitive) and 3 (very sensitive)
    # TILE_THRESHOLD (0x0142), 0: 50%, 1: 25%, 2: 12.5%, 3: 6.25%
    i2c.rwReg(addr=0x0142, value=1, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK)

    # Start streaming. Upload long register sequence before this step.
    input_camera_stream.start()

    # Test by reading VERSION_ID
    VERSION_ID = i2c.rwReg(addr=0x011B, value=0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK)
    print("VERSION_ID: {}".format(VERSION_ID))

    last_time = time.time()
    CURRENT_ACTIVE_CONTEXT = 0

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        # Test by reading CURRENT_ACTIVE_CONTEXT, NEXT_ACTIVE_CONTEXT
        previous_active_context = CURRENT_ACTIVE_CONTEXT
        CURRENT_ACTIVE_CONTEXT = i2c.rwReg(addr=0x4002, value=0, rw=0, flag=0)
        # At frame 20, manually switch to Context B for event detection
        if frame_idx == 20:
            i2c.rwReg(addr=0xE003, value=1, rw=1, flag=0)
            print(f"Manually switching to context B at frame {frame_idx}.")
        if previous_active_context == 1 and CURRENT_ACTIVE_CONTEXT == 0:
            print(f"Event detected at frame {frame_idx}.")
        # GUI element
        current_time = time.time()
        fps = 1 / (current_time - last_time)
        cv2.putText(frame, f"Context: {CURRENT_ACTIVE_CONTEXT}, fps: {fps:.1f}",
                (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow('output', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit(0)
        last_time = current_time

