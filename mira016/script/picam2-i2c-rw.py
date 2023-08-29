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
    i2c = v4l2Ctrl(sensor="mira016", printFunc=print)

    # Other I2C devices are powered on, but Mira sensor itself is not powered on until calling start().

    # Example: Communicating with gauge IC LTC2941 via I2C
    # Set the I2C device address to 0x64 for LTC2941
    i2c.rwReg(addr=0x00, value=0x64, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_SET_TBD)
    # Optionally, write control register A to default
    i2c.rwReg(addr=0x00, value=0b00000101, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_TBD)
    # Test by reading control register A back
    ctrl_reg_val = i2c.rwReg(addr=0x00, value=0x0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_TBD)
    ctrl_reg_val = np.uint8(np.uint32(ctrl_reg_val) & 0x000000FF)
    print(f"Read back LTC2941 control register A 8-bit value 0x{ctrl_reg_val:X}")

    # Start streaming. Mira sensor is powered on. From here, Mira sensor is accessible via I2C.
    input_camera_stream.start()

    # Test by reading VERSION_ID
    VERSION_ID = i2c.rwReg(addr=0x011B, value=0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_USE_BANK)
    print("VERSION_ID: {}".format(VERSION_ID))

    # Example: Enable illumination trigger, set ILLUM_WIDTH and ILLUM_DELAY.
    illum_delay_us = 0
    illum_delay_reg_val = np.uint32((1<<19) + illum_delay_us)
    # Write 20 bits of ILLUM_DELAY. 8 LSB of ILLUM_WIDTH maps to value; 12 MSB of ILLUM_WIDTH maps to addr.
    i2c.rwReg(addr=((illum_delay_reg_val >> 8) & 0x0FFF), value=(illum_delay_reg_val & 0xFF), rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_DELAY)
    # Set auto_illum_width to 1 to let the driver automatically set it to exposure time. Otherwise use a manual width.
    auto_illum_width = 1
    if (auto_illum_width == 1):
        # Configure illumination trigger width to track exposure time
        i2c.rwReg(addr=0x00, value=0x00, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_EXP_T_ON)
    else:
        # Manually set width to 5ms for 100fps.
        illum_width_us = 5000
        illum_width_reg_val = np.uint32(illum_width_us * 1000 / 8 )
        # Write 24 bits of ILLUM_WIDTH. 8 LSB of ILLUM_WIDTH maps to value; 16 MSB of ILLUM_WIDTH maps to addr.
        i2c.rwReg(addr=((illum_width_reg_val >> 8) & 0xFFFF), value=(illum_width_reg_val & 0xFF), rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_WIDTH)
        # Disable illumination trigger tracking exposure time
        i2c.rwReg(addr=0x00, value=0x00, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_EXP_T_OFF)
    # Enable illumination trigger
    i2c.rwReg(addr=0x00, value=0x00, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_TRIG_ON)

    last_time = time.time()

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        # GUI element
        current_time = time.time()
        fps = 1 / (current_time - last_time)
        cv2.putText(frame, f"fps: {fps:.1f}",
                (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow('output', frame)
        # Every 100 frames, read power gauge 
        if (frame_idx % 100 == 0):
            power_msb2 = i2c.rwReg(addr=0x05, value=0x0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_TBD)
            power_msb1 = i2c.rwReg(addr=0x06, value=0x0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_TBD)
            power_lsb = i2c.rwReg(addr=0x07, value=0x0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_TBD)
            power_12bit = np.uint16( ((np.uint32(power_lsb) & 0x000000FF) << 0) | ((np.uint32(power_msb1) & 0x000000FF) << 8) | ((np.uint32(power_msb2) & 0x000000FF) << 16) )
            print(f"Read back LTC2941 power register 12-bit value 0x{power_12bit:X}")
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        last_time = current_time
    sys.exit(0)
 
