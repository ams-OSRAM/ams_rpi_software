import cv2
import numpy as np
from typing import Optional, Tuple
import sys
import time

sys.path.append("../../common")
from driver_access import v4l2Ctrl

class Mira220():
    def __init__(self):
        self.i2c = v4l2Ctrl(sensor="mira220", printFunc=print)
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_OFF)
        time.sleep(1)
        # (2) Optionally power on the sensor
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_ON)
        time.sleep(3)

        # (3) Disable base register sequence upload and reset
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_REG_UP_OFF)
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_RESET_OFF)
        pass
    def __del__(self):
        # (5) power off
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_POWER_OFF)
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_REG_UP_ON)
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA220_REG_FLAG_RESET_ON)

    def write_register(self, address, value):
        '''Write value to the given address.
        
        Parameters
        ----------
        address : int
            Address of register

        value : int
            Value to write
        '''
        exp_val = self.i2c.rwReg(addr=address, value=value, rw=1, flag=0)
        return exp_val

    def read_register(self, address):
        '''Read the register value at given address.
        
        Parameters
        ----------
        address : int
            Address of register

        Returns
        -------
        int : 
            Value at given address
        '''
        exp_val = self.i2c.rwReg(addr=address, value=0, rw=0, flag=0)
        return exp_val

    def otp_power_on(self):
        '''Power up the OTP of the sensor.
        '''
        self.write_register(0x0080, 0x04)

    def otp_power_off(self):
        '''Power down the OTP of the sensor.
        '''
        self.write_register(0x0080, 0x08)

    def get_sap_material(self):
        '''Get the internal id of the sensor programmed in OTP.

        Returns
        -------
        str : 
            internal id
        '''


        self.otp_power_on()
        b0 = '{0:0{1}X}'.format(self.otp_read(0x3e, 0), 2)
        b1 = '{0:0{1}X}'.format(self.otp_read(0x3e, 1), 2)
        b2 = '{0:0{1}X}'.format(self.otp_read(0x3e, 2), 2)
        b3 = '{0:0{1}X}'.format(self.otp_read(0x3e, 3), 2)     
        self.otp_power_off()
        return int(b0,16) + int(b1,16)*256 + int(b2,16)*256**2 + int(b3,16)*256**3
        return b0 + ':' + b1 + ':' + b2 + ':' + b3     
    def get_internal_id(self):
        '''Get the internal id of the sensor programmed in OTP.

        Returns
        -------
        str : 
            internal id
        '''
        self.otp_power_on()
        b0 = '{0:0{1}X}'.format(self.otp_read(0x25, 0), 2)
        b1 = '{0:0{1}X}'.format(self.otp_read(0x1e, 0), 2)
        b2 = '{0:0{1}X}'.format(self.otp_read(0x1e, 1), 2)
        b3 = '{0:0{1}X}'.format(self.otp_read(0x1e, 2), 2)
        b4 = '{0:0{1}X}'.format(self.otp_read(0x1d, 0), 2)
        b5 = '{0:0{1}X}'.format(self.otp_read(0x1d, 1), 2)
        b6 = '{0:0{1}X}'.format(self.otp_read(0x1d, 2), 2)
        b7 = '{0:0{1}X}'.format(self.otp_read(0x1d, 3), 2)      
        self.otp_power_off()
        return b0 + ':' + b1 + ':' + b2 + ':' + b3 + ':' + b4 + ':' + b5 + ':' + b6 + ':' + b7 
    def otp_read(self, otp_address, offset):
        '''Read the given OTP address.
        
        Parameters
        ----------
        otp_address : int
            OTP address to be read

        offset : int
            The byte to be read from the 32 bit (4 bytes) OTP word
            
        Returns
        -------
        int : 
            OTP value
        '''
        self.write_register(0x0086, otp_address)
        self.write_register(0x0080, 0x02)
        return self.read_register(0x0082 + offset)


if __name__ == "__main__":

    # Before stream on, upload register sequence
    # Create a config parse to parse the register sequence txt


    mira = Mira220()
    id=mira.get_internal_id()
    print(f'unique id {id}')

    id=mira.get_sap_material()

    print(f'sap number {id}')
    sap = {
    509780018	:		'Mono (Plain glass with PF)',\
    509780037	:		'Mono (Plain glass without PF)',\
    509780022	:		'Mono (AR glass with PF)',\
    509780027	:		'RGB (Plain glass with PF)',\
    509780038	:		'RGB (Plain glass without PF)',\
    509780029	:		'RGB (AR glass with PF)',\
    509780034	:		'RGB-IR (Plain glass with PF)',\
    509780039	:		'RGB-IR (Plain glass without PF)',\
    509780036	:		'RGB-IR (AR glass with PF)'		
    }
    print(f'your device is {sap[id]}')
