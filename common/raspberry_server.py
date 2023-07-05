import numpy as np
from picamera2 import Picamera2
from picamera2.sensor_format import SensorFormat
import random
import time
from Pyro5.api import expose, Daemon, locate_ns


HOST_IP = "10.61.100.201"    # Set accordingly (i.e. "192.168.1.99")
HOST_PORT = 9092         # Set accordingly (i.e. 9876)

@expose
class StockMarket(object):
    def __init__(self, marketname, symbols):
        self._name = marketname
        self._symbols = symbols

    def quotes(self):
        while True:
            symbol = random.choice(self.symbols)
            yield symbol, round(random.uniform(5, 150), 2)
            time.sleep(random.random()/2.0)

    @property
    def name(self):
        return self._name

    @property
    def symbols(self):
        return self._symbols
    
@expose
class RaspberryServer():
    def __init__(self) -> None:
        self._name = 'rasp'
        self.picam2 = Picamera2()
        raw_format = SensorFormat(self.picam2.sensor_format)
        raw_format.packing = None
        config = self.picam2.create_still_configuration(raw={"format": raw_format.format}, buffer_count=2)
        self.picam2.configure(config)
        self.picam2.set_controls({"ExposureTime": 1000 , "AnalogueGain": 1.0})
        self.picam2.start()


    def control(self,exp,gain):
        self.picam2.set_controls({"ExposureTime": exp , "AnalogueGain": gain})
        return True


    def capture_frames(self, num_frames: int):
        images = []
        for i in range(num_frames):
            images.append(self.picam2.capture_array("raw").view(np.uint16))
            metadata = self.picam2.capture_metadata()

        return images    
    def write_reg_16_8(i2c_addr, reg_addr, reg_value):
        pass
    def read_reg_16_8(i2c_addr, reg_addr, reg_value):
        pass

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
    rasp = RaspberryServer()
    ret=rasp.capture_frames(1)
    print(ret)
    with Daemon(host=HOST_IP, port=HOST_PORT) as daemon:
        rasp_uri = daemon.register(rasp)
        with locate_ns() as ns:
            # ns.register("example.stockmarket.nasdaq", nasdaq_uri)
            # ns.register("example.stockmarket.newyork", newyork_uri)
            ns.register("example.stockmarket.raspberry", rasp_uri)

        print("Stockmarkets available.")
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