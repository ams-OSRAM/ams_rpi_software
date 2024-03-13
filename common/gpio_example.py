# AMS Osram
# Press ctrl C to kill app
# Befor use: pip install RPi.GPIO
import signal
import sys
import RPi.GPIO as GPIO
BUTTON_GPIO = 16  

from picamera2 import Picamera2
from picamera2.sensor_format import SensorFormat
import numpy as np
from PIL import Image

exposure_time = 600
num_frames = 60
framerate = 10


global picam2
picam2 = Picamera2()
raw_format = SensorFormat('SGRBG10_CSI2P')
print(raw_format)
raw_format.packing = None
config = picam2.create_still_configuration(raw={"format": raw_format.format}, buffer_count=2)
picam2.configure(config)
picam2.set_controls({"ExposureTime": exposure_time , "AnalogueGain": 1.0, "FrameRate":framerate})
picam2.start()




def signal_handler(sig, frame):
    GPIO.cleanup()
    print('done')
    sys.exit(0)
    
    
    
def button_pressed_callback(channel):
    images = []
    global picam2

    print('button pressed')
    request = picam2.capture_request()
    request.save("main", "image.jpg")
    print(request.get_metadata()) # this is the metadata for this image
    images.append(picam2.capture_array("raw").view(np.uint16))
    metadata = picam2.capture_metadata()
    request.release()
    ##ADD code for frame grab
    ## Variable that holds the image needs to be declared as global   
    print(images[0].shape)
    print(images[0])
    for index, image in enumerate(images):
        pilim = Image.fromarray(image)
        pilim.save(f"imgraw{index}.tiff")
        print(metadata['SensorTimestamp'])

    
if __name__ == '__main__':
    ##ADD this section to the main code of the mira220 script on the folder ams_software/mira220/scripts
    GPIO.setmode(GPIO.BOARD)              ##GPIO 
    GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   #internal pull ul resistor 

    GPIO.add_event_detect(BUTTON_GPIO, GPIO.RISING,callback=button_pressed_callback, bouncetime=100)   # deboudnce is for preventing multiple button press
                                                                                         # callback function is the interrupt pin handler function
    signal.signal(signal.SIGINT, signal_handler)       ## pin gets tied to signal handler 
    signal.pause()


