import cv2
import numpy as np
from typing import Optional, Tuple
import sys
import os
import argparse
import time
import logging
import subprocess
import RPi.GPIO as GPIO

sys.path.append("../../common")
from picam2cv2 import CameraStreamInput
from driver_access import v4l2Ctrl
from config_parser import ConfigParser
from ExtTrigPWM import ExtTrigPWM

if __name__ == "__main__":

    # Before stream on, upload register sequence
    # Create a config parse to parse the register sequence txt
    config_parser = ConfigParser()
    reg_seq = config_parser.parse_file('config_files/Mira220_register_sequence_12b_1600x1400.txt')
    print(f"Parsed {len(reg_seq)} register writes from file.")

    # Create a v4l2Ctrl class for register read/write over i2c.
    i2c = v4l2Ctrl(sensor="mira220", printFunc=print)

    #########################################################
    # Steps to upload reg sequence txt:
    # (1) manually power off the sensor
    # (3) manaully power on the sensor
    # (3) disable base reg upload, reset; use external trigger
    # (4) upload register sequence
    # (5) enable external trigger PWM
    # (6) start capture
    # (7) power off
    #########################################################

    # (1) Manually power off the sensor
    print(f"Manually power off the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_OFF)
    time.sleep(3)

    # (2) Optionally power on the sensor
    print(f"Manually power on the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_ON)
    time.sleep(3)

    # (3) Disable base register sequence upload and reset; use external trigger
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_REG_UP_OFF)
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_RESET_OFF)

    # (4) Upload register sequence from txt file
    print(f"Writing {len(reg_seq)} registers to driver buffer via V4L2 interface.")
    for reg in reg_seq:
        exp_val = i2c.rwReg(addr=reg[0], value=reg[1], rw=1, flag=0)

    # (5) enable external trigger
    # On the sensor side:
    # (a) set slave mode register 0x1003. Value 0x08 : slave mode. Value 0x10: master mode.
    i2c.rwReg(addr=0x1003, value=0x08, rw=1, flag=0)
    # (b) set external selection register 0x1001.
    #     value 0x00 : single pin control via REQ_EXP, exp_time via PWM width.
    #     value 0x01 : single pin control via REG_EXP, exp_time via register.
    i2c.rwReg(addr=0x1001, value=0x00, rw=1, flag=0)
    # (c) set STREAM_CTRL_OFF to disable stream start/stop.
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_STREAM_CTRL_OFF)
    # Below are codes that use RPi PWM pin as external trigger. Not needed if ext trig is from elsewhere.
    # Config: Broadcom GPIO 18 (PCM CLK) at header position 12. Frequency 30Hz. Duty cycle 20 percent.
    ext_trig_pwm = ExtTrigPWM(ext_trig_pwm_pin=18, ext_trig_pwm_hz=30, ext_trig_pwm_dc=20)
    ext_trig_pwm.start()

    # (6) Initialize camera stream according to width, height, bit depth etc. from register sequence
    input_camera_stream = CameraStreamInput(width=1600, height=1400, AeEnable=False, FrameRate=30.0, bit_depth=12)

    # Start streaming. Upload long register sequence before this step.
    input_camera_stream.start()

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
            break
        last_time = current_time
    # (7) Power off
    print(f"Manually power off the sensor via V4L2 interface.")
    i2c.rwReg(addr=0x0, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_OFF)

