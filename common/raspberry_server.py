import numpy as np
from picamera2 import Picamera2
from picamera2.sensor_format import SensorFormat
import random
import time
from Pyro5.api import expose, Daemon, locate_ns
import Pyro5.socketutil
from driver_access import v4l2Ctrl
# from picam2cv2 import CameraStreamInput
# from driver_access import v4l2Ctrl
# from config_parser import ConfigParser
import logging


#`HOST_IP = "192.168.137.67"    # Set accordingly (i.e. "192.168.1.99")
#HOST_IP = "raspberrypi.local"    # Set accordingly (i.e. "192.168.1.99")
HOST_PORT = 9092         # Set accordingly (i.e. 9876)
sensor = 'mira050'
bit_depth = 10
    
@expose
class RaspberryServer():
    def __init__(self) -> None:
        self._name = 'rasp'
        self.picam2=None

    def start_server(self):
        if self.picam2:
            if self.picam2.is_open:
                logger.debug('already open')
                return
        self.picam2=Picamera2()
        raw_format = SensorFormat('SGRBG10')
        # raw_format = SensorFormat(self.picam2.sensor_format)

        raw_format.packing = None
        config = self.picam2.create_still_configuration(raw={"format": raw_format.format}, buffer_count=2)
        self.picam2.configure(config)
        self.picam2.set_controls({"ExposureTime": 1000 , "AnalogueGain": 1.0})


        self.i2c = v4l2Ctrl(sensor="mira050", printFunc=print)
        
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_REG_UP_ON)
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_RESET_ON)
        # self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_REG_UP_OFF)
        # self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_RESET_OFF)

        # Disable base register sequence upload (overwriting skip-reg-upload in dtoverlay )
    
    def stop_server(self):
        self.picam2.stop()
        self.picam2.close()
        pass

    def control(self,exp,gain):
        self.picam2.set_controls({"ExposureTime": exp , "AnalogueGain": gain})
        return True


    def capture_frames(self, num_frames: int):
        self.picam2.start()
        images = []
        for i in range(num_frames):
            images.append(self.picam2.capture_array("raw").view(np.uint16))
            print(f'capture img {i}')
            #metadata = self.picam2.capture_metadata()
        self.picam2.stop()
        return images    
    
    def write_reg_16_8(self, i2c_addr, reg_addr, reg_value):
        print(f'write reg on server: {i2c_addr} {reg_addr} {reg_value}')
        self.i2c.rwReg(addr=reg_addr, value=reg_value, rw=1)
        pass
    
    def power_on(self):
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_POWER_ON)
        print(f'pw on')
        return ret

    def power_off(self):
        self.i2c.rwReg(addr=0x0, value=0, rw=1, flag=self.i2c.AMS_CAMERA_CID_MIRA050_REG_FLAG_POWER_OFF)
        print(f'pw off')
        return ret

    @property
    def name(self):
        return self._name
    
    @property
    def picamera(self):
        return self.picam2



    def images(self,num):
        print('grab img')
        list = [frame.tolist() for frame in self.capture_frames(num)]
        return list

    def quotes(self):
        while True:
            symbol = 'raspisymbol'
            yield symbol, round(random.uniform(5, 150), 2)
            time.sleep(random.random()/2.0)

if __name__=="__main__":
    logger=logging.getLogger('raspiserver')
    logging.basicConfig(filename='ams_server.log', encoding='utf-8', level=logging.DEBUG)
    HOST_IP=Pyro5.socketutil.get_ip_address('raspberrypi.local',version=4)
    logger.info(f'host ip is {HOST_IP}')
    rasp = RaspberryServer()
    with Daemon(host=HOST_IP, port=HOST_PORT) as daemon:
        rasp_uri = daemon.register(rasp)
        with locate_ns(host=HOST_IP, port=9091, broadcast=True) as ns:
            ns.register("ams.raspberry", rasp_uri)

        print(f"Stockmarkets available. {rasp_uri}")
        daemon.requestLoop()
        


"""
implement these:
ARDUCAM_API Uint32 ArduCam_writeReg_8_8( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32 val );
ARDUCAM_API Uint32 ArduCam_readReg_8_8( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32* pval );
ARDUCAM_API Uint32 ArduCam_writeReg_8_16( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32 val );
ARDUCAM_API Uint32 ArduCam_readReg_8_16( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32* pval );
ARDUCAM_API Uint32 ArduCam_writeReg_16_8( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32 val );
ARDUCAM_API Uint32 ArduCam_readReg_16_8( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32* pval );
ARDUCAM_API Uint32 ArduCam_writeReg_16_16( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32 val );
ARDUCAM_API Uint32 ArduCam_readReg_16_16( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32* pval );
ARDUCAM_API Uint32 ArduCam_writeReg_16_32( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32 val );
ARDUCAM_API Uint32 ArduCam_readReg_16_32( ArduCamHandle useHandle, Uint32 i2cAddr, Uint32 regAddr, Uint32* pval );
"""
