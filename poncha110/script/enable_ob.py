import cv2
import numpy as np
import sys
import os
import time
sys.path.append("../../common")
from driver_access import v4l2Ctrl
from config_parser import ConfigParser

i2c = v4l2Ctrl(sensor="poncha110", printFunc=print)

# check ywin size
ywin_ena = i2c.rwReg(addr=0x012, value=0x0, rw=0, flag=0) # READ ywin enable )
print(f'{ywin_ena = }')

r0=i2c.rwReg(addr=0x022, value=0x0, rw=0, flag=0) # READ registers )
r1=i2c.rwReg(addr=0x023, value=0x0, rw=0, flag=0) # READ registers )

print(f'ywin0 start val in decimal: { 256 * r0 + r1 }')# check xwin size


r0=i2c.rwReg(addr=0x024, value=0x0, rw=0, flag=0) # READ registers )
r1=i2c.rwReg(addr=0x025, value=0x0, rw=0, flag=0) # READ registers )

print(f' YWIN0_END val in decimal: { 256 * r0 + r1 }')# check xwin size

#//YWIN0_CROP_HEIGHT
#//	{ 0x0029, 0x03 },
#//	{ 0x002a, 0xd4 },

r0=i2c.rwReg(addr=0x029, value=0x0, rw=0, flag=0) # READ registers )
r1=i2c.rwReg(addr=0x02a, value=0x0, rw=0, flag=0) # READ registers )

print(f' YWIN0_CROP val in decimal: { 256 * r0 + r1 }')# check xwin size

print(r0,r1)
#ywin crop height
r0=i2c.rwReg(addr=0x029, value=4, rw=1, flag=0) # write registers )
r1=i2c.rwReg(addr=0x02a, value=50, rw=1, flag=0) # write registers )

r1=i2c.rwReg(addr=0x062, value=1, rw=1, flag=0) # write output OB)

print(f' OB enabled') # check xwin size

#termparture sensor
r1=i2c.rwReg(addr=0x06B, value=1, rw=1, flag=0) # write output OB)

r1=i2c.rwReg(addr=0x06, value=4, rw=1, flag=0) # write output OB)
r1=i2c.rwReg(addr=0x06, value=0, rw=1, flag=0) # write output OB)

temp1=i2c.rwReg(addr=0x06C, value=0, rw=0, flag=0) # write output OB)

print(f"{temp1=}")

temp2=i2c.rwReg(addr=0x06D, value=0, rw=0, flag=0) # write output OB)

print(f"{temp2=}")

tsens = temp1*256+temp2
celcius = (tsens * 10 -26020)/92 

print(celcius)