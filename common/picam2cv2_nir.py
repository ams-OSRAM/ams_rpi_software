import cv2
import numpy as np
from typing import Optional, Tuple
import sys
import os
import argparse
import time
import logging
import subprocess

# picamera2 for Mira220 with NIR pixels
from picamera2 import Picamera2
from picamera2.controls import Controls
picam2 = Picamera2()

# visualization
from scipy.ndimage import convolve


def bilinear_interpolation_nir(image: np.ndarray, nir_mask: np.ndarray) -> np.ndarray:
    # Initialize an empty array for interpolated NIR values
    nir_interpolated = np.copy(image)

    # Inverting the NIR mask to identify non-NIR pixels
    non_nir_mask = ~nir_mask

    # Define a convolution kernel for bilinear interpolation
    kernel = np.array([[1, 2, 1],
                       [2, 4, 2],
                       [1, 2, 1]], dtype=np.float32) / 4.0

    # Interpolate only non-NIR pixels
    interpolated_values = convolve(image * nir_mask, kernel, mode='constant', cval=0.0)
    nir_interpolated[non_nir_mask] = interpolated_values[non_nir_mask]

    return nir_interpolated

def demosaic_optimized(image: np.ndarray,
                       mask_g: np.ndarray, mask_r: np.ndarray, mask_b: np.ndarray) -> np.ndarray:
    
    height, width = image.shape
    rgb_image = np.zeros((height, width, 3), dtype=np.float32)

    # Extract channels using masks
    rgb_image[:, :, 0] = image * mask_r  # Red channel
    rgb_image[:, :, 1] = image * mask_g  # Green channel
    rgb_image[:, :, 2] = image * mask_b  # Blue channel

    # Interpolate missing pixels
    kernel = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]]) / 4.0
    for c in range(3):
        missing_pixels = np.logical_not([mask_r, mask_g, mask_b][c])
        rgb_image[missing_pixels, c] = convolve(rgb_image[:, :, c], kernel, mode='nearest')[missing_pixels]

    # Normalize each channel
    for c in range(3):
        channel = rgb_image[:, :, c]
        min_val, max_val = channel.min(), channel.max()
        if max_val > min_val:
            rgb_image[:, :, c] = (channel - min_val) / (max_val - min_val) * 255

    return rgb_image.astype(np.uint8)

class CameraStreamInput:
    capture_array = "main"
    """
    Initializes a camera stream and returns it as an iterable object
    """
    def __init__(self, width=1600, height=1400, AeEnable=True, FrameRate = 2.0, bit_depth=12, ExposureTime=1000, AnalogueGain=1.0):
        camera_properties = picam2.camera_properties
        sensor_modes = picam2.sensor_modes
        picam2.preview_configuration.enable_raw()
        for index, mode in enumerate(sensor_modes):
            if bit_depth == mode['bit_depth']:
                picam2.preview_configuration.raw.format = str(mode['format'])
        picam2.preview_configuration.main.size = (width, height)
        picam2.preview_configuration.main.format = "RGB888"
        picam2.preview_configuration.raw.size = (width, height)
        picam2.preview_configuration.controls.AeEnable = AeEnable
        picam2.preview_configuration.controls.FrameRate = FrameRate
        if AeEnable == False:
            picam2.preview_configuration.controls.ExposureTime = ExposureTime
            picam2.preview_configuration.controls.AnalogueGain = AnalogueGain
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
        if self.capture_array == "lores":
            frame = picam2.capture_array("lores")
        elif self.capture_array == "raw":
            frame = picam2.capture_array("raw")
        else:
            frame = picam2.capture_array("main")
        self._index += 1
        return (frame, self._index)

    def start(self):
        picam2.start()

    def stop(self):
        picam2.stop_preview()
        picam2.stop()

if __name__ == "__main__":

    # Initialize classes
    input_camera_stream = CameraStreamInput(AeEnable=True)

    # Start streaming
    input_camera_stream.start()

    (width, height) = picam2.preview_configuration.main.size

    # Create masks for each color
    mask_r = np.zeros((height, width), dtype=bool)
    mask_g = np.zeros((height, width), dtype=bool)
    mask_b = np.zeros((height, width), dtype=bool)

    mask_g[0::2,0::2] = True
    mask_g[1::2,1::2] = True

    mask_r[1::4,0::4] = True
    mask_r[3::4,2::4] = True

    mask_b[1::4,2::4] = True
    mask_b[3::4,0::4] = True

    nir_mask = np.zeros((height, width), dtype=bool)
    nir_mask[0::2,1::2] = True

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:

        grayscale_image_cv = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # Process the raw image to get RGB and NIR images
        rgb_image = demosaic_optimized(grayscale_image_cv, mask_g, mask_r, mask_b)
        nir_image = bilinear_interpolation_nir(grayscale_image_cv, nir_mask)

        nir_image_stacked = np.stack((nir_image, nir_image, nir_image), axis=-1)

        # Combine images for display
        combined_image = np.hstack((frame, rgb_image, nir_image_stacked))

        # Display the images
        # Create a named window
        cv2.namedWindow("Sensor Output", cv2.WINDOW_NORMAL)

        # Set the window size
        cv2.resizeWindow("Sensor Output", 640, 480)

        cv2.imshow("Sensor Output", combined_image)

        # cv2.imshow('output', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit(0)

