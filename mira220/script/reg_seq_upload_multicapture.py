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

    # Create a v4l2Ctrl class for register read/write over i2c.
    i2c = v4l2Ctrl(sensor="mira220", printFunc=print)

    #########################################################
    # Process to upload reg sequence txt:
    # (1) Manually power off the sensor
    # (2) Manaully power on the sensor
    # (3) Disable reset, base reg upload; force stream ctrl
    # (4) Loop for a few iterations:
    #     (4a) Upload register seq (at leaast for 1st iter)
    #     (4b) Config camera stream and start capture
    #     (4c) Show frames in GUI until user stops (key 'q')
    #     (4d) Close camera stream and GUI.
    # (5) Power off
    #########################################################

    # (1) Manually power off the sensor
    print(f"Manually power off the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_OFF)
    time.sleep(3)

    # (2) Optionally power on the sensor
    print(f"Manually power on the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_ON)
    time.sleep(3)

    # (3) Disable base register sequence upload and reset
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_REG_UP_OFF)
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_RESET_OFF)
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_STREAM_CTRL_ON)

    # (4) Loop for a few iterations. Example: 2 iterations.
    for capture_iter in range(2):
        print(f"Starting capture loop interation {capture_iter}.")
        if capture_iter == 0:
            # (4a) upload register sequence at least for the first iteration
            # Create a config parse to parse the register sequence txt
            config_parser = ConfigParser()
            reg_seq = config_parser.parse_file('config_files/Mira220_register_sequence_12b_1600x1400.txt')
            print(f"Parsed {len(reg_seq)} register writes from file.")
            # Upload register sequence from txt file
            print(f"Writing {len(reg_seq)} registers to driver buffer via V4L2 interface.")
            for reg in reg_seq:
                exp_val = i2c.rwReg(addr=reg[0], value=reg[1], rw=1, flag=0)
        # (4b) Initialize camera stream according to width, height, bit depth etc. from register sequence
        input_camera_stream = CameraStreamInput(width=1600, height=1400, AeEnable=False, FrameRate=30.0, bit_depth=12)
        # Start streaming. Upload long register sequence before this step.
        input_camera_stream.start()
        # (4c) Show frames in GUI until user stops (key 'q')
        last_time = time.time()
        for frame, frame_idx in input_camera_stream:
            # GUI element
            current_time = time.time()
            fps = 1 / (current_time - last_time)
            cv2.putText(frame, f"fps: {fps:.1f}",
                    (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow('output', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                input_camera_stream.stop()
                break
            last_time = current_time
        # (4d) Close camera stream and GUI
        del input_camera_stream
        cv2.destroyAllWindows()
    # (5) power off
    print(f"Manually power off the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_OFF)

