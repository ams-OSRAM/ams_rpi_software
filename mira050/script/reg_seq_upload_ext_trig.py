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
from ExtTrigPWM import ExtTrigPWM

if __name__ == "__main__":

    # Before stream on, upload register sequence
    # Create a config parse to parse the register sequence txt
    config_parser = ConfigParser()
    reg_seq = config_parser.parse_file('config_files/Mira050_register_sequence_10bhsgain1_test2.txt')
    print(f"Parsed {len(reg_seq)} register writes from file.")

    # Create a v4l2Ctrl class for register read/write over i2c.
    i2c = v4l2Ctrl(sensor="mira050", printFunc=print)

    #########################################################
    # Steps to upload reg sequence txt:
    # (1) manually power off the sensor
    # (3) manaully power on the sensor
    # (3) disable base register upload and reset
    # (4) upload register sequence
    # (5) set external trigger
    # (6) force stream control by picamera2
    # (7) power off
    #########################################################

    # (1) Manually power off the sensor
    print(f"Manually power off the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_POWER_OFF)
    time.sleep(3)

    # (2) Manually power on the sensor
    print(f"Manually power on the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_POWER_ON)
    time.sleep(3)

    # (3) Disable base register sequence upload and reset
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_REG_UP_OFF)
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_RESET_OFF)

    # (4) Upload register sequence from txt file
    print(f"Writing {len(reg_seq)} registers to sensor via V4L2 interface.")
    for reg in reg_seq:
        exp_val = i2c.rwReg(addr=reg[0], value=reg[1], rw=1, flag=0)

    # (5) enable external trigger. Use single pin REQ_1, labeled as "REQ EXP" on some mira050 boards.
    # On the sensor side:
    # (a) CTRL_MODE register 0x0011 at Bank 0. Value 0x00: external mode. Value 0x03: master streaming.
    i2c.rwReg(addr=0x0011, value=0x00, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK)
    # (b) SINGLE_PIN_CTRL register 0x011D at Bank 0.
    #     value 0x00 : dual pin control, capture via REG_1, exp_time via REQ_2.
    #     value 0x01 : single pin control, capture via REQ_1, exp_time via PWM width.
    i2c.rwReg(addr=0x011D, value=0x01, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK)
    # (c) set STREAM_CTRL_OFF to disable stream start/stop.
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_STREAM_CTRL_OFF)
    # Below are codes that use RPi PWM pin as external trigger. Not needed if ext trig is from elsewhere.
    # Config: Broadcom GPIO 18 (PCM CLK) at header position 12. Frequency 30Hz. Duty cycle 5 percent.
    ext_trig_pwm = ExtTrigPWM(ext_trig_pwm_pin=18, ext_trig_pwm_hz=30, ext_trig_pwm_dc=5)
    ext_trig_pwm.start()

    # (6) Initialize camera stream according to width, height, bit depth etc. from register sequence
    input_camera_stream = CameraStreamInput(width=572, height=768, AeEnable=False, FrameRate=50.0, bit_depth=10)

    # Start streaming. Upload long register sequence before this step.
    input_camera_stream.start()

    # Test by reading VERSION_ID
    VERSION_ID = i2c.rwReg(addr=0x011B, value=0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK)
    print("VERSION_ID: {}".format(VERSION_ID))

    last_time = time.time()
    it = 0
    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        # GUI element
        current_time = time.time()
        fps = 1 / (current_time - last_time)
        cv2.putText(frame, f"fps: {fps:.1f}",
                (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow('output', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        last_time = current_time
        it+=1
    # (7) power off
    print(f"Manually power off the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_POWER_OFF)
    sys.exit(0)


