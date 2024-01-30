import cv2
import numpy as np
from typing import Optional, Tuple
import sys
import os
import argparse
import time
import logging
import subprocess
import tifffile as tiff
import rawpy
from PIL import Image

# picamera2 for Mira220 with NIR pixels
from picamera2 import Picamera2
from picamera2.controls import Controls
picam2 = Picamera2()

# visualization
from scipy.ndimage import convolve
from joblib import dump, load


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


class CalibrationPipeline:
    def __init__(self, cfg, calibration):
        # Read parameters from config file
        self.calibration = calibration

        # Create masks for each color
        self.height = cfg['height']  # rows
        self.width = cfg['width']  # cols
        
        self.mask_r = np.zeros((self.height, self.width), dtype=bool)
        self.mask_g = np.zeros((self.height, self.width), dtype=bool)
        self.mask_b = np.zeros((self.height, self.width), dtype=bool)
        self.nir_mask = np.zeros((self.height, self.width), dtype=bool)
    
        self.mask_g[0::2,0::2] = True
        self.mask_g[1::2,1::2] = True
    
        self.mask_r[1::4,0::4] = True
        self.mask_r[3::4,2::4] = True
    
        self.mask_b[1::4,2::4] = True
        self.mask_b[3::4,0::4] = True

        self.nir_mask[0::2,1::2] = True

        if calibration:
            self.gain = None
            self.ccm = None
            self.ccm_model = None
        else:
            self.pre_gain = np.array([[1., 1.35591342], [1.50867157, 1.]])
            self.ccm = np.array([[ 6.90796609, -3.74769344, -3.63070901],
                                 [ 8.54922552, 17.27399007,  2.19044354],
                                 [-7.69600579, -2.91365167,  8.24670768]])

            

            # Load saved parameters for ccm model
            src_loaded = np.load('ccm_src_data.npy')
            model_params_loaded = load('ccm_model_parameters.joblib')

            # Reconstruct and retrain the model
            self.ccm_model = cv2.ccm_ColorCorrectionModel(src_loaded, cv2.ccm.COLORCHECKER_Macbeth)
            self.ccm_model.setLinear(model_params_loaded['linear'])
            self.ccm_model.setLinearGamma(model_params_loaded['gamma'])
            self.ccm_model.setLinearDegree(model_params_loaded['degree'])
            self.ccm_model.setSaturatedThreshold(*model_params_loaded['saturated_threshold'])
            self.ccm_model.run()

    def bilinear_interpolation_nir(self, image: np.ndarray) -> np.ndarray:
        # Initialize an empty array for interpolated NIR values
        nir_interpolated = np.copy(image)

        # Inverting the NIR mask to identify non-NIR pixels
        non_nir_mask = ~self.nir_mask

        # Define a convolution kernel for bilinear interpolation
        kernel = np.array([[1, 2, 1],
                        [2, 4, 2],
                        [1, 2, 1]], dtype=np.float32) / 4.0

        # Interpolate only non-NIR pixels
        interpolated_values = convolve(image * self.nir_mask, kernel, mode='constant', cval=0.0)
        nir_interpolated[non_nir_mask] = interpolated_values[non_nir_mask]

        return nir_interpolated

    def demosaic_optimized(self, image, mode='bilinear'):
        
        rgb_image = np.zeros((self.height, self.width, 3), dtype=np.float32)
    
        # Extract channels using masks
        rgb_image[:, :, 0] = image * self.mask_r  # Red channel
        rgb_image[:, :, 1] = image * self.mask_g  # Green channel
        rgb_image[:, :, 2] = image * self.mask_b  # Blue channel
    
        # Interpolate missing pixels
        if mode == 'bilinear':
            kernel = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]]) / 4.0
        elif mode == 'bicubic':
            kernel = np.array([[-1, 2, -1], [2, 4, 2], [-1, 2, -1]]) / 4.0
        else:
            raise NotImplementedError
        
        for c in range(3):
            missing_pixels = np.logical_not([self.mask_r, self.mask_g, self.mask_b][c])
            rgb_image[missing_pixels, c] = convolve(rgb_image[:, :, c], kernel, mode='nearest')[missing_pixels]
    
        # Normalize each channel
        for c in range(3):
            channel = rgb_image[:, :, c]
            min_val, max_val = channel.min(), channel.max()
            if max_val > min_val:
                rgb_image[:, :, c] = (channel - min_val) / (max_val - min_val) * 255

        return rgb_image.astype(np.uint8)

    @staticmethod
    def search_macbeth_chart(bgr_image, visualization=False):
        # Search macbeth chart
        detector = cv2.mcc.CCheckerDetector_create()
        detector.process(bgr_image, cv2.mcc.MCC24, 1)
        checkers = detector.getListColorChecker()
        
        for checker in checkers:
            cdraw = cv2.mcc.CCheckerDraw_create(checker)
            img_draw = bgr_image.copy()
            cdraw.draw(img_draw)
            chartsRGB = checker.getChartsRGB()
            width, height = chartsRGB.shape[:2]
            roi = chartsRGB[0:width, 1]
            rows = int(roi.shape[:1][0])
            src = chartsRGB[:, 1].copy().reshape(int(rows / 3), 1, 3)
            src /= 255

        return src, img_draw

    def compute_ccm(self, src):
        model = cv2.ccm_ColorCorrectionModel(src, cv2.ccm.COLORCHECKER_Macbeth)
        model.setColorSpace(cv2.ccm.COLOR_SPACE_sRGB)
        model.setCCM_TYPE(cv2.ccm.CCM_3x3)
        model.setDistance(cv2.ccm.DISTANCE_CIE2000)

        # model.setLinear(cv2.ccm.LINEARIZATION_COLORLOGPOLYFIT)
        model.setLinear(cv2.ccm.LINEARIZATION_GAMMA)
        # model.setLinear(cv2.ccm.LINEARIZATION_IDENTITY)
        model.setLinearGamma(1.7)
        model.setLinearDegree(2)
        model.setSaturatedThreshold(0, 0.95)
        model.run()
        
        self.ccm = model.getCCM()
        print(f'ccm:\n{self.ccm}\n')

        self.ccm_model = model
        
        loss = model.getLoss()
        print(f'loss:\n{loss}')

        # Save the ccm_model
        # np.savetxt('ccm_src_data.csv', src, delimiter=',')
        np.save('ccm_src_data.npy', src)

        # If there are other parameters or settings, save them as well
        # For example, using a dictionary to store parameters
        model_params = {
            'linear': cv2.ccm.LINEARIZATION_GAMMA,
            'gamma': 1.7,
            'degree': 2,
            'saturated_threshold': [0, 0.95]
            # Add other relevant parameters here
        }
        
        dump(model_params, 'ccm_model_parameters.joblib')

    def apply_ccm(self, image_bgr, visualization=False):
        if self.calibration:
            # Detect Macbeth chart
            src, _ = self.search_macbeth_chart(image_bgr, visualization=False)
            
            # Get CCM
            self.compute_ccm(src)
        
        # Apply CCM
        rgb_image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        img_ = rgb_image.copy()
        img_ = img_.astype(np.float64)
        img_ = img_ / 255
        calibratedImage = self.ccm_model.infer(img_)
        out_ = calibratedImage * 255
        out_[out_ < 0] = 0
        out_[out_ > 255] = 255
        out_ = out_.astype(np.uint8)

        scale = 1
        COLS_ = np.uint16(self.width/scale)
        ROWS_ = np.uint16(self.height/scale)
        dim = (COLS_, ROWS_)
        
        temp = cv2.cvtColor(out_, cv2.COLOR_RGB2BGR)

        out_img = cv2.resize(temp, dim, interpolation=cv2.INTER_CUBIC)

        return out_img
    
    @staticmethod
    def black_correction(image):
        return image - np.min(image)

    def get_gain(self, src):
        # Extract WB from patch 20
        patch = 20
        gain_b = (src[patch][0][1] - src[23][0][1]) / (src[patch][0][0] - src[23][0][0])
        gain_g1 = 1
        gain_g2 = 1
        gain_r = (src[patch][0][1] - src[23][0][1]) / (src[patch][0][2] - src[23][0][2])

        gain = [[gain_g1, gain_b], [gain_r, gain_g2]]

        self.gain = np.tile(gain, (np.uint16(self.height/2), np.uint16(self.width/2)))

        print('Gain matrix is: \n', self.gain[0:2, 0:2])

        return gain_b, gain_r
    
    def auto_white_balance(self, rgb_image, bgr_image):
        if self.calibration:
            src, _ = self.search_macbeth_chart(bgr_image, visualization=False)
            gain_b, gain_r = self.get_gain(src)
        else:
            gain_b = self.pre_gain[0, 1]
            gain_r = self.pre_gain[1, 0]
            self.gain = np.tile(self.pre_gain, (np.uint16(self.height/2), np.uint16(self.width/2)))

        R = rgb_image[:, :, 0]
        G = rgb_image[:, :, 1]
        B = rgb_image[:, :, 2]

        R = R * gain_b
        B = B * gain_r

        img_color_RGB = np.dstack((R, G, B))

        img_color_RGB_ = np.array(img_color_RGB, dtype=np.uint8)
        img_color_BGR = cv2.cvtColor(img_color_RGB_, cv2.COLOR_RGB2BGR)
        # print(f'img_color_BGR range: {np.min(img_color_BGR)} - {np.max(img_color_BGR)}')

        img_color_BGR = cv2.medianBlur(img_color_BGR, 5)
        # print(f'img_color_BGR range + blur: {np.min(img_color_BGR)} - {np.max(img_color_BGR)}')

        return img_color_BGR

    def image_processing_pipeline(self, raw_image, lens_shading_map=None, verbose=False):
        # 1. Black Correction
        corrected_image = self.black_correction(raw_image)

        # 2. Lens Shading Correction
        # corrected_image = lens_shading_correction(corrected_image, lens_shading_map)

        # 3. RGB Demosaicking
        rgb_image = self.demosaic_optimized(corrected_image)

        # 4. NIR Extraction and Interpolation
        grayscale_image_cv = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)  # need to do something else
        nir_image = self.bilinear_interpolation_nir(grayscale_image_cv)

        # 5. Auto White Balancing using Macbeth Chart
        bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
        awb_image = self.auto_white_balance(rgb_image, bgr_image)

        # 6. Color Correction Matrix (CCM) application
        ccm_image = self.apply_ccm(awb_image)

        return rgb_image, nir_image, awb_image, ccm_image

    def run(self, raw_image):
        rgb_image, nir_image, awb_image, ccm_image = self.image_processing_pipeline(raw_image, lens_shading_map=None)

        return rgb_image, nir_image, awb_image, ccm_image

class CameraStreamInput:
    capture_array = "raw"
    """
    Initializes a camera stream and returns it as an iterable object
    """
    def __init__(self, width=640, height=480, AeEnable=True, FrameRate = 10.0, bit_depth=8, ExposureTime=1000, AnalogueGain=1.0):
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

    cfg = {'height': height, 'width': width}

    pipeline = CalibrationPipeline(cfg, calibration=False)

    # Per-frame operation
    for frame, frame_idx in input_camera_stream:
        rgb_image, nir_image, awb_image, ccm_image = pipeline.run(frame.view(np.uint8))

        nir_image_stacked = np.stack((nir_image, nir_image, nir_image), axis=-1)

        # Combine images for display
        combined_image = np.hstack((rgb_image,
                                    cv2.cvtColor(awb_image, cv2.COLOR_BGR2RGB), 
                                    cv2.cvtColor(ccm_image, cv2.COLOR_BGR2RGB), 
                                    nir_image_stacked))


        # Display the images
        # Create a named window
        cv2.namedWindow("Sensor Output", cv2.WINDOW_NORMAL)

        # Set the window size
        cv2.resizeWindow("Sensor Output", 1280, 720)

        cv2.imshow("Sensor Output", combined_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit(0)

