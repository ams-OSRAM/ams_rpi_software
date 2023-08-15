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
    input_camera_stream = CameraStreamInput(width=1080, height=1280, AeEnable=True)
    i2c = v4l2Ctrl(sensor="mira130", printFunc=print)

    # Start streaming. Upload long register sequence before this step.
    input_camera_stream.start()

    # Test by reading sensor ID
    sensor_id_high = i2c.rwReg(addr=0x3107, value=0, rw=0)
    sensor_id_low = i2c.rwReg(addr=0x3108, value=0, rw=0)
    print(f"Sensor ID high 0x{sensor_id_high:X}, low 0x{sensor_id_low:X}")

    last_time = time.time()

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        # GUI element
        current_time = time.time()
        fps = 1 / (current_time - last_time)
        cv2.putText(frame, f"fps: {fps:.1f}",
                (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow('output', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit(0)
        last_time = current_time

