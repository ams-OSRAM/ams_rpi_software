import sys
import os
sys.path.append("../../common")
from driver_access import v4l2Ctrl

def gray_to_dec(gray):
    '''Converts Gray encoded number to decimal number.

    Parameters
    ----------
    gray : int
        Gray encoded number

    Returns
    -------
    int : 
        Decoded number
    '''
    mask = gray
    while(mask):
        mask = mask >> 1
        gray ^= mask
    return gray


def sensor_temperature_conversion(signal, reset, gain):
    '''Converts temperature register value to degrees Celcius.

    Parameters
    ----------
    signal : int
        Temperature sensor signal value VPTAT

    reset : int
        Temperature sensor reset value VREF
    
    gain : int
        The analog gain of the sensor (1, 2 or 4)

    Returns
    -------
    float : 
        Temperature in degrees Celcius 
    ''' 
    lsb = 0.181 # mV/DN
    mvc = 1.63  # mV/degC
    v25 = 140   # mV @ 25degC
    tsens_sig = gray_to_dec(signal)
    tsens_rst = gray_to_dec(reset)
    tsens = (tsens_sig - tsens_rst) / gain
    temperature_degrees = ((tsens * lsb) - v25) / mvc + 25
    return temperature_degrees


if __name__ == "__main__":
    # Initialize classes
    i2c = v4l2Ctrl(sensor="mira220", printFunc=print)
    # Read temperature registers
    tsens_sig_lo = i2c.rwReg(addr=0x3188, value=0, rw=0, flag=0)
    tsens_sig_hi = i2c.rwReg(addr=0x3189, value=0, rw=0, flag=0)
    tsens_sig = tsens_sig_hi * 256 + tsens_sig_lo
    print(f"tsens_sig: {tsens_sig}")
    tsens_rst_lo = i2c.rwReg(addr=0x318E, value=0, rw=0, flag=0)
    tsens_rst_hi = i2c.rwReg(addr=0x318F, value=0, rw=0, flag=0)
    tsens_rst = tsens_rst_hi * 256 + tsens_rst_lo
    print(f"tsens_rst: {tsens_rst}")
    uncal_degree_C = sensor_temperature_conversion(tsens_sig, tsens_rst, 1)
    print(f"Uncalibrated temperature in degree Celcius: {uncal_degree_C}")
    exit(1)

