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
    input_camera_stream = CameraStreamInput(width=572, height=768, AeEnable=False, FrameRate=50.0, bit_depth=12, ExposureTime=1000, AnalogueGain=1.0)
    i2c = v4l2Ctrl(sensor="mira050", printFunc=print)

    # Other I2C devices are powered on, but Mira sensor itself is not powered on until calling start().

    # Example: Controlling LED driver chip (LM2759) via I2C
    # Set the I2C device address to 0x53 for LM2759
    i2c.rwReg(addr=0x00, value=0x53, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_SET_TBD)
    # Optionally, set torch current to max
    i2c.rwReg(addr=0xA0, value=0x0F, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_TBD)
    # Turn on torch
    # i2c.rwReg(addr=0x10, value=1, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_TBD)
    # Turn off torch
    i2c.rwReg(addr=0x10, value=0, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_TBD)

    # Test by reading torch current
    current_reg_val = i2c.rwReg(addr=0xA0, value=0x0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_TBD)
    current_reg_val = np.uint8(np.uint32(current_reg_val) & 0x0000000F)
    print(f"Read back torch current register 4-bit value 0x{current_reg_val:X}")

    # Start streaming. Mira sensor is powered on. From here, Mira sensor is accessible via I2C.
    input_camera_stream.start()

    # Test by reading VERSION_ID
    VERSION_ID = i2c.rwReg(addr=0x011B, value=0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK)
    print("VERSION_ID: {}".format(VERSION_ID))

    # Example: Enable illumination trigger, set ILLUM_WIDTH and ILLUM_DELAY.
    illum_delay_us = 0
    illum_delay_reg_val = np.uint32((1<<19) + illum_delay_us)
    # Write 20 bits of ILLUM_DELAY. 8 LSB of ILLUM_WIDTH maps to value; 12 MSB of ILLUM_WIDTH maps to addr.
    i2c.rwReg(addr=((illum_delay_reg_val >> 8) & 0x0FFF), value=(illum_delay_reg_val & 0xFF), rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_DELAY)
    # Set auto_illum_width to 1 to let the driver automatically set it to exposure time. Otherwise use a manual width.
    auto_illum_width = 1
    if (auto_illum_width == 1):
        # Configure illumination trigger width to track exposure time
        i2c.rwReg(addr=0x00, value=0x00, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_EXP_T_ON)
    else:
        # Manually set width to 1ms for exposure time of 1ms.
        illum_width_us = 1000
        illum_width_reg_val = np.uint32(illum_width_us * 1000 / 8 )
        # Write 24 bits of ILLUM_WIDTH. 8 LSB of ILLUM_WIDTH maps to value; 16 MSB of ILLUM_WIDTH maps to addr.
        i2c.rwReg(addr=((illum_width_reg_val >> 8) & 0xFFFF), value=(illum_width_reg_val & 0xFF), rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_WIDTH)
        # Disable illumination trigger tracking exposure time
        i2c.rwReg(addr=0x00, value=0x00, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_EXP_T_OFF)
    # Enable illumination trigger
    i2c.rwReg(addr=0x00, value=0x00, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_TRIG_ON)


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
    sys.exit(0)


