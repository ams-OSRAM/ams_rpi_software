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

    # Example: Communicating with gauge IC LTC2941 via I2C
    # Set the I2C device address to 0x64 for LTC2941
    i2c.rwReg(addr=0x00, value=0x64, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_SET_TBD)
    # Optionally, write control register A to default
    i2c.rwReg(addr=0x00, value=0b00000101, rw=1, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_TBD)
    # Test by reading control register A back
    ctrl_reg_val = i2c.rwReg(addr=0x00, value=0x0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_TBD)
    ctrl_reg_val = np.uint8(np.uint32(ctrl_reg_val) & 0x000000FF)
    print(f"Read back LTC2941 control register A 8-bit value 0x{ctrl_reg_val:X}")

    # Start streaming. Upload long register sequence before this step.
    input_camera_stream.start()

    # Test by reading VERSION_ID
    VERSION_ID = i2c.rwReg(addr=0x011B, value=0, rw=0, flag=i2c.AMS_CAMERA_CID_MIRA016_REG_FLAG_USE_BANK)
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
 
