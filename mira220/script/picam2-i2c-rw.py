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
    input_camera_stream = CameraStreamInput(width=960, height=720, AeEnable=False, FrameRate=30.0, bit_depth=12, ExposureTime=1000, AnalogueGain=1.0)
    i2c = v4l2Ctrl(sensor="mira220", printFunc=print)

    # Other I2C devices are powered on, but Mira sensor itself is not powered on until calling start().

    # Example: Controlling LED driver chip (LM2759) via I2C
    # Set the I2C device address to 0x53 for LM2759
    i2c.rwReg(addr=0x00, value=0x53, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_I2C_SET_TBD)
    # Optionally, set torch current to max
    i2c.rwReg(addr=0xA0, value=0x0F, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_I2C_TBD)
    # Turn on torch
    # i2c.rwReg(addr=0x10, value=1, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_I2C_TBD)
    # Turn off torch
    i2c.rwReg(addr=0x10, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_I2C_TBD)

    # Test by reading torch current
    current_reg_val = i2c.rwReg(addr=0xA0, value=0x0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_I2C_TBD)
    current_reg_val = np.uint8(np.uint32(current_reg_val) & 0x0000000F)
    print(f"Read back torch current register 4-bit value 0x{current_reg_val:X}")


    # Start streaming. Mira sensor is powered on. From here, Mira sensor is accessible via I2C.
    input_camera_stream.start()

    # Example: Enable illumination trigger, set ILLUM_WIDTH and ILLUM_DELAY.
    # ILLUM_WIDTH is in unit of rows. When set to 0, width equal to exposure time.
    illum_width_reg_val = np.uint32(0)
    # ILLUM_DELAY is in unit of rows. Default to 0.
    illum_delay_reg_val = np.uint32(0)
    # Write 16 bits of ILLUM_WIDTH. 8 LSB of ILLUM_WIDTH maps to value; 8 MSB of ILLUM_WIDTH maps to addr.
    i2c.rwReg(addr=((illum_width_reg_val >> 8) & 0x00FF), value=(illum_width_reg_val & 0xFF), rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_ILLUM_WIDTH)
    # Write 17 bits of ILLUM_DELAY including sign. 8 LSB of ILLUM_WIDTH maps to value; 9 MSB of ILLUM_WIDTH maps to addr.
    i2c.rwReg(addr=((illum_delay_reg_val >> 8) & 0x01FF), value=(illum_delay_reg_val & 0xFF), rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_ILLUM_DELAY)
    # Enable illumination trigger
    i2c.rwReg(addr=0x00, value=0x00, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_ILLUM_TRIG_ON)

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
            sys.exit(0)
        last_time = current_time

