#!/usr/bin/python3

# Configure a raw stream and capture an image from it.
import time
import numpy as np
from picamera2 import Picamera2, Preview

picam2 = Picamera2()
#picam2.start_preview(Preview.QTGL)

preview_config = picam2.create_preview_configuration(raw={'format': 'SGRBG12', "size": picam2.sensor_resolution})
print(preview_config)
picam2.configure(preview_config)
picam2.set_controls({"ExposureTime": 30000, "AnalogueGain": 1.0})

picam2.start()
time.sleep(2)
#raw = picam2.capture_buffer()
#np.from_buffer
raw = picam2.capture_array("raw")
#print(raw.shape)
print(raw.dtype)
print(picam2.stream_configuration("raw"))
lsb=raw[::,::2]
msb=raw[::,1::2]
new=(msb*256+lsb)/1
import matplotlib.pyplot as plt
plt.imshow(new,cmap='gray',vmin=0,vmax=4095)
plt.show()