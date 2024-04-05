import cv2
import numpy as np
from typing import Optional, Tuple
import sys
import os
import argparse
import time
import logging
import subprocess

sys.path.append("../../common")
from picam2cv2 import CameraStreamInput
from driver_access import v4l2Ctrl

if __name__ == "__main__":

    # Initialize classes
    input_camera_stream = CameraStreamInput(width=400, height=400, AeEnable=False, FrameRate=100.0, bit_depth=8, ExposureTime=100, AnalogueGain=1.0)

    # Configure to use "raw" (rather than "main")
    input_camera_stream.capture_array = "raw"

    # Start streaming. Upload long register sequence before this step.
    input_camera_stream.start()

    last_time = time.time()

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        current_time = time.time()
        fps = 1 / (current_time - last_time)
        print(f"frame_idx: {frame_idx}, frame.shape: {frame.shape}, fps: {fps}, output: capture_{frame_idx}.raw")
        frame.astype(np.uint8).tofile(f"capture_{frame_idx}.raw")
        if frame_idx >= 5:
            break
        last_time = current_time

    sys.exit(0)
 
