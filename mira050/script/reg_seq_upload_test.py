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
    reg_seq = config_parser.parse_file('config_files/Mira050_register_sequence_10bhsgain1_test2.txt')
    print(f"Parsed {len(reg_seq)} register writes from file.")

    # Create a v4l2Ctrl class for register read/write over i2c.
    i2c = v4l2Ctrl(sensor="mira050", printFunc=print)
    for reg in reg_seq:
        exp_val = i2c.rwReg(addr=reg[0], value=reg[1], rw=1, flag=0)

    # Initialize camera stream according to width, height, bit depth etc. from register sequence
    input_camera_stream = CameraStreamInput(width=572, height=768, AeEnable=True, FrameRate=50.0, bit_depth=10)

    # Start streaming. Upload long register sequence before this step.
    input_camera_stream.start()

    # Test by reading VERSION_ID
    VERSION_ID = i2c.rwReg(addr=0x011B, value=0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK)
    print("VERSION_ID: {}".format(VERSION_ID))

    last_time = time.time()

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        # GUI element
        current_time = time.time()
        fps = 1 / (current_time - last_time)
        cv2.putText(frame, f"fps: {fps:.1f}",
                (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow('output', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit(0)
        last_time = current_time

