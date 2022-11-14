import cv2
import numpy as np
from typing import Optional, Tuple
import sys
import os
import argparse
import time
import logging
import subprocess

# picamera2 
from picamera2 import Picamera2
from picamera2.controls import Controls
picam2 = Picamera2()

class CameraStreamInput:
    """
    Initializes a camera stream and returns it as an iterable object
    """
    def __init__(self, width=320, height=240, AeEnable=True, FrameRate = 200.0, bit_depth=12):
        camera_properties = picam2.camera_properties
        sensor_modes = picam2.sensor_modes
        picam2.preview_configuration.enable_raw()
        for index, mode in enumerate(sensor_modes):
            if bit_depth == mode['bit_depth']:
                picam2.preview_configuration.raw.format = mode['unpacked']
        picam2.preview_configuration.main.size = (width, height)
        picam2.preview_configuration.main.format = "RGB888"
        picam2.preview_configuration.controls.AeEnable = AeEnable
        picam2.preview_configuration.controls.FrameRate = FrameRate
        picam2.preview_configuration.align()
        picam2.configure("preview")
        self._index = 0

    def __iter__(self):
        """
        Creates an iterator for this container.
        """
        self._index = 0
        return self

    def __next__(self) -> Optional[Tuple[np.ndarray, int]]:
        """
        @return tuple containing current image and meta data if available, otherwise None
        """
        frame = picam2.capture_array("main")
        self._index += 1
        return (frame, self._index)

    def start(self):
        picam2.start()

if __name__ == "__main__":

    # Initialize classes
    input_camera_stream = CameraStreamInput(AeEnable=True)

    # Start streaming
    input_camera_stream.start()

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        cv2.imshow('output', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit(0)

