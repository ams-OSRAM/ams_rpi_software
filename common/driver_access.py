import cv2
import numpy as np
from typing import Optional, Tuple
import sys
import os
import argparse
import time
import logging
import subprocess

# V4L2 control
import v4l2
import fcntl
import ctypes

class v4l2Ctrl:
    #########################
    # Mira050 8-bit flags
    #########################
    # Most significant Byte is flag, and most significant bit is unused.
    AMS_CAMERA_CID_MIRA050_REG_FLAG_FOR_READ       = 0b00000001
    AMS_CAMERA_CID_MIRA050_REG_FLAG_USE_BANK       = 0b00000010
    AMS_CAMERA_CID_MIRA050_REG_FLAG_BANK           = 0b00000100
    AMS_CAMERA_CID_MIRA050_REG_FLAG_CONTEXT        = 0b00001000
    # Use bit 5 to indicate spacial command, bit 1,2,3,4 for command.
    AMS_CAMERA_CID_MIRA050_REG_FLAG_CMD_SEL        = 0b00010000
    # When sleep bit is set, the other 3 Bytes is sleep values in us.
    AMS_CAMERA_CID_MIRA050_REG_FLAG_SLEEP_US       = 0b00010000
    AMS_CAMERA_CID_MIRA050_REG_FLAG_RESET_ON       = 0b00010010
    AMS_CAMERA_CID_MIRA050_REG_FLAG_RESET_OFF      = 0b00010100
    AMS_CAMERA_CID_MIRA050_REG_FLAG_REG_UP_ON      = 0b00010110
    AMS_CAMERA_CID_MIRA050_REG_FLAG_REG_UP_OFF     = 0b00011000
    AMS_CAMERA_CID_MIRA050_REG_FLAG_POWER_ON       = 0b00011010
    AMS_CAMERA_CID_MIRA050_REG_FLAG_POWER_OFF      = 0b00011100
    AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_TRIG_ON  = 0b00011110
    AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_TRIG_OFF = 0b00010001
    AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_WIDTH    = 0b00010011
    AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_DELAY    = 0b00010101
    AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_EXP_T_ON = 0b00010111
    AMS_CAMERA_CID_MIRA050_REG_FLAG_ILLUM_EXP_T_OFF= 0b00011001
    # Bit 6&7 of flag are combined to specify I2C dev (default is Mira)
    AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_SEL        = 0b01100000
    AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_MIRA       = 0b00000000
    AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_TBD        = 0b00100000
    AMS_CAMERA_CID_MIRA050_REG_FLAG_I2C_SET_TBD    = 0b01000000
    #########################
    # Mira160 8-bit flags
    #########################
    # Most significant Byte is flag, and most significant bit is unused.
    AMS_CAMERA_CID_MIRA016_REG_FLAG_FOR_READ       = 0b00000001
    AMS_CAMERA_CID_MIRA016_REG_FLAG_USE_BANK       = 0b00000010
    AMS_CAMERA_CID_MIRA016_REG_FLAG_BANK           = 0b00000100
    AMS_CAMERA_CID_MIRA016_REG_FLAG_CONTEXT        = 0b00001000
    # Use bit 5 to indicate spacial command, bit 1,2,3,4 for command.
    AMS_CAMERA_CID_MIRA016_REG_FLAG_CMD_SEL        = 0b00010000
    # When sleep bit is set, the other 3 Bytes is sleep values in us.
    AMS_CAMERA_CID_MIRA016_REG_FLAG_SLEEP_US       = 0b00010000
    AMS_CAMERA_CID_MIRA016_REG_FLAG_RESET_ON       = 0b00010010
    AMS_CAMERA_CID_MIRA016_REG_FLAG_RESET_OFF      = 0b00010100
    AMS_CAMERA_CID_MIRA016_REG_FLAG_REG_UP_ON      = 0b00010110
    AMS_CAMERA_CID_MIRA016_REG_FLAG_REG_UP_OFF     = 0b00011000
    AMS_CAMERA_CID_MIRA016_REG_FLAG_POWER_ON       = 0b00011010
    AMS_CAMERA_CID_MIRA016_REG_FLAG_POWER_OFF      = 0b00011100
    AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_TRIG_ON  = 0b00011110
    AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_TRIG_OFF = 0b00010001
    AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_WIDTH    = 0b00010011
    AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_DELAY    = 0b00010101
    AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_EXP_T_ON = 0b00010111
    AMS_CAMERA_CID_MIRA016_REG_FLAG_ILLUM_EXP_T_OFF= 0b00011001
    # Bit 6&7 of flag are combined to specify I2C dev (default is Mira)
    AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_SEL        = 0b01100000
    AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_MIRA       = 0b00000000
    AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_TBD        = 0b00100000
    AMS_CAMERA_CID_MIRA016_REG_FLAG_I2C_SET_TBD    = 0b01000000
    #########################
    # Mira220 8-bit flags
    #########################
    # Most significant Byte is flag, and most significant bit is unused.
    AMS_CAMERA_CID_MIRA220_REG_FLAG_FOR_READ       = 0b00000001
    # Use bit 5 to indicate spacial command, bit 1,2,3,4 for command.
    AMS_CAMERA_CID_MIRA220_REG_FLAG_CMD_SEL        = 0b00010000
    # When sleep bit is set, the other 3 Bytes is sleep values in us.
    AMS_CAMERA_CID_MIRA220_REG_FLAG_SLEEP_US       = 0b00010000
    AMS_CAMERA_CID_MIRA220_REG_FLAG_RESET_ON       = 0b00010010
    AMS_CAMERA_CID_MIRA220_REG_FLAG_RESET_OFF      = 0b00010100
    AMS_CAMERA_CID_MIRA220_REG_FLAG_REG_UP_ON      = 0b00010110
    AMS_CAMERA_CID_MIRA220_REG_FLAG_REG_UP_OFF     = 0b00011000
    AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_ON       = 0b00011010
    AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_OFF      = 0b00011100
    AMS_CAMERA_CID_MIRA220_REG_FLAG_ILLUM_TRIG_ON  = 0b00011110
    AMS_CAMERA_CID_MIRA220_REG_FLAG_ILLUM_TRIG_OFF = 0b00010001
    AMS_CAMERA_CID_MIRA220_REG_FLAG_ILLUM_WIDTH    = 0b00010011
    AMS_CAMERA_CID_MIRA220_REG_FLAG_ILLUM_DELAY    = 0b00010101
    # Bit 6&7 of flag are combined to specify I2C dev (default is Mira)
    AMS_CAMERA_CID_MIRA220_REG_FLAG_I2C_SEL        = 0b01100000
    AMS_CAMERA_CID_MIRA220_REG_FLAG_I2C_MIRA       = 0b00000000
    AMS_CAMERA_CID_MIRA220_REG_FLAG_I2C_TBD        = 0b00100000
    AMS_CAMERA_CID_MIRA220_REG_FLAG_I2C_SET_TBD    = 0b01000000
    #########################
    # Mira130 8-bit flags
    #########################
    # Most significant Byte is flag, and most significant bit is unused.
    AMS_CAMERA_CID_MIRA130_REG_FLAG_FOR_READ       = 0b00000001
    # Use bit 5 to indicate spacial command, bit 1,2,3,4 for command.
    AMS_CAMERA_CID_MIRA130_REG_FLAG_CMD_SEL        = 0b00010000
    # When sleep bit is set, the other 3 Bytes is sleep values in us.
    AMS_CAMERA_CID_MIRA130_REG_FLAG_SLEEP_US       = 0b00010000
    AMS_CAMERA_CID_MIRA130_REG_FLAG_RESET_ON       = 0b00010010
    AMS_CAMERA_CID_MIRA130_REG_FLAG_RESET_OFF      = 0b00010100
    AMS_CAMERA_CID_MIRA130_REG_FLAG_REG_UP_ON      = 0b00010110
    AMS_CAMERA_CID_MIRA130_REG_FLAG_REG_UP_OFF     = 0b00011000
    AMS_CAMERA_CID_MIRA130_REG_FLAG_POWER_ON       = 0b00011010
    AMS_CAMERA_CID_MIRA130_REG_FLAG_POWER_OFF      = 0b00011100
    AMS_CAMERA_CID_MIRA130_REG_FLAG_ILLUM_TRIG_ON  = 0b00011110
    AMS_CAMERA_CID_MIRA130_REG_FLAG_ILLUM_TRIG_OFF = 0b00010001
    # Bit 6&7 of flag are combined to specify I2C dev (default is Mira)
    AMS_CAMERA_CID_MIRA130_REG_FLAG_I2C_SEL        = 0b01100000
    AMS_CAMERA_CID_MIRA130_REG_FLAG_I2C_MIRA       = 0b00000000
    AMS_CAMERA_CID_MIRA130_REG_FLAG_I2C_TBD        = 0b00100000
    AMS_CAMERA_CID_MIRA130_REG_FLAG_I2C_SET_TBD    = 0b01000000


    def __init__(self, sensor, printFunc=print):
        self.fname = "/dev/v4l-subdev0"
        self.pr = printFunc
        self.sensor = str(sensor).lower()
        if self.sensor == "mira220":
            self.reg_flag_for_read = self.AMS_CAMERA_CID_MIRA220_REG_FLAG_FOR_READ
        elif self.sensor == "mira050":
            self.reg_flag_for_read = self.AMS_CAMERA_CID_MIRA050_REG_FLAG_FOR_READ
        elif self.sensor == "mira016":
            self.reg_flag_for_read = self.AMS_CAMERA_CID_MIRA016_REG_FLAG_FOR_READ
        elif self.sensor == "mira130":
            self.reg_flag_for_read = self.AMS_CAMERA_CID_MIRA130_REG_FLAG_FOR_READ
        else:
            txt = "WARNING: sensor={} is not supported, falls back to mira050 v4l2 cmd".format(sensor)
            self.pr(txt)
            self.reg_flag_for_read = self.AMS_CAMERA_CID_MIRA050_REG_FLAG_FOR_READ
        try:
            self.f = os.open(self.fname, os.O_RDWR)
        except:
            self.pr("ERROR: Unable to open driver")
        cp = v4l2.v4l2_capability()
        self.card = cp.card

    def close(self):
        os.close(self.f)
        return (0)

    def rwReg(self, addr, value, rw, flag=0, print_en=True):
        try:
            if rw > 0:
                # Write register
                reg_flag = flag & 0xFF
                reg_addr = addr & 0xFFFF
                reg_val = value & 0xFF
                value = (reg_flag << 24) | (reg_addr << 8) | (reg_val);
                subprocess.Popen('v4l2-ctl -d  /dev/v4l-subdev0 --set-ctrl {}=0x{:08x}'.format("mira_reg_w", value), shell=True)
            else:
                # Dummy write with FLAG_FOR_READ, to cache reg addr for read later
                reg_flag = (self.reg_flag_for_read | flag ) & 0xFF
                reg_addr = addr & 0xFFFF
                reg_val = value & 0xFF
                value = (reg_flag << 24) | (reg_addr << 8) | (reg_val);
                subprocess.Popen('v4l2-ctl -d  /dev/v4l-subdev0 --set-ctrl {}=0x{:08x}'.format("mira_reg_w", value), shell=True)
                # Read register value with previously cached reg addr
                out_str = subprocess.check_output('v4l2-ctl -d  /dev/v4l-subdev0 --get-ctrl {}'.format("mira_reg_r"), shell=True)
                out_arr = out_str.decode("utf-8").split(":")
                reg = int(out_arr[1])
                reg_flag = (reg >> 24) & 0xFF
                reg_addr = (reg >> 8) & 0xFFFF
                reg_val = reg & 0xFF
        except:
            if print_en:
                txt = "ERROR: I2C access error to ADDR={},VALUE={},RW={}".format(addr, value, rw)
                self.pr(txt)
            raise IOError(txt)
        return int(reg_val)

