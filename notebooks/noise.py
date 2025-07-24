#!/usr/bin/python3

# This example adds multiple exposures together to create a much longer exposure
# image. It does this by adding raw images together, correcting the black level,
# and saving a DNG file. Currentl you need to use a raw converter to obtain the
# final result (e.g. "dcraw -w -W accumulated.dng").

#some imports
import time
from PIL import Image
import numpy as np
import pathlib
from picamera2 import Picamera2, Preview
import pprint
import matplotlib.pyplot as plt
from characterization_ams.stats_engine import stats
from characterization_ams.emva import emva
from characterization_ams.standard_tests import ptc




import argparse

def main():
    parser = argparse.ArgumentParser(description="Parse camera settings and image saving options.")

    parser.add_argument(
        "--gain",
        type=float,
        required=True,
        default=1,
        help="Set the camera gain (e.g., 1.0 to 16.0). Default is 1.0."
    )

    parser.add_argument(
        "--exposure",
        type=int,
        default=1000,
        help="Set the camera exposure time in microseconds (e.g., 100 to 100000). Default is 1000."
    )

    parser.add_argument(
        "--bitmode",
        type=int,
        required=True,
        choices=[8, 10, 12],
        help="Set the camera's bit depth for images (8, 10, or 12 bits). Default is 8."
    )
    parser.add_argument(
        "--amount",
        type=int,
        default=20,
        help="Set the number of images to capture per setting. Default is 20."
    )
    parser.add_argument(
        "--mode",
        type=int,
        help="Set the sensor mode. this is an optional override."
    )
    parser.add_argument(
        "--save_images",
        action='store_true',
        help="Specify whether to save captured images. Use '--save_images' to save images, or do not use it to skip saving. Default is 'no'."
    )
    parser.add_argument(
        "--save_csv",
        action='store_true',
        help="Specify whether to save captured images. Use '--save_images' to save images, or do not use it to skip saving. Default is 'no'."
    )
    parser.add_argument(
        "--save_npz",
        action='store_true',
        help="Specify whether to save npz stack of images. Use '--save_npz' to save save_npz, or do not use it to skip saving. Default is 'no'."
    )

    parser.add_argument(
        "--appendix",
        type=str,
        default="noisecalcs",
        help="filename appendix for csv results. Default is 'noisecalcs'."
    )

    args = parser.parse_args()

    print(f"Gain: {args.gain}")
    print(f"Mode: {args.mode}")
    print(f"Exposure: {args.exposure} us")
    print(f"Bit Mode: {args.bitmode} bits")
    print(f"Save Images: {args.save_images} Save CSV: {args.save_csv} Save NPZ: {args.save_npz}")
    filename = pathlib.Path(f"noise_{args.gain}_gain_{args.exposure}_exposure_{args.bitmode}_bitmode_{args.appendix}.csv")
    foldername = pathlib.Path(f"./noise_{args.gain}_gain_{args.exposure}_exposure_{args.bitmode}_bitmode_{args.appendix}")
    foldername.mkdir(parents=False, exist_ok=True)

    print(f"Results will be stored at :{foldername.resolve()}")



    #settings
    mode_override = args.mode
    amount = args.amount #numbers of pictures to capture per setting
    bit_mode = args.bitmode
    analog_gain = args.gain
    exposure = args.exposure #in us #np.arange(1000, 10000, 500, dtype=int) #start, stop, step - this must be an array type. can also be, [100,200,300,400] etc..
    #select mode a few cells below.

    #view camera model
    #pprint.pprint(Picamera2.global_camera_info() ) #before init ;
    #print all sensor modes
    with Picamera2() as picam2:
        modes = picam2.sensor_modes
        pprint.pprint(picam2.sensor_modes)
    if mode_override is not None:
        print('override mode')
        mode =modes[mode_override]
    else:
        print('no override mode')
        for mode in modes:
            if mode['bit_depth']==bit_mode:
                break
    selected_mode=mode
    time.sleep(1)

    with Picamera2() as picam2:
        preview_config = picam2.create_preview_configuration(main={"size": selected_mode["size"]},
            raw={"format": selected_mode["unpacked"],
                "size": selected_mode["size"],
            })
        picam2.configure(preview_config)
    
    with Picamera2() as picam2:
        preview_config = picam2.create_preview_configuration(main={"size": selected_mode["size"]},
            raw={"format": selected_mode["unpacked"],
                "size": selected_mode["size"],
            })
        picam2.configure(preview_config)

        with picam2.controls as ctrl:
            ctrl.AeEnable = False
            ctrl.AwbEnable = False
            ctrl.AnalogueGain = analog_gain
            ctrl.ExposureTime = exposure
            ctrl.ColourGains = (1.0, 1.0)
        
        picam2.start()
        print(picam2.camera_controls)


        picam2.set_controls({"ExposureTime": exposure , "AnalogueGain": analog_gain})
        
        time.sleep(2)
        #raw = picam2.capture_buffer()
        #np.from_buffer
        
        size = selected_mode["size"]

        width = size[0]
        height = size[1]
        im_stack = []
        for i in range(amount):
            if bit_mode == 8:
                image = picam2.capture_array("raw").view(np.uint8)
            else:
                image = picam2.capture_array("raw").view(np.uint16)
            im_stack.append(image[0:height, 0:width])
            if args.save_images:
                # save images    
                pilim = Image.fromarray(im_stack[-1])
                tiffname = str(f"{foldername}/img_exposure{exposure}_gain{analog_gain}{i}.tiff")
                pilim.save(tiffname)
            
        # get & save images
        if args.save_npz:
            name = filename.name.replace('.csv', '.npz')
            temp_im_dir = foldername
            temp_im_path = pathlib.Path(temp_im_dir / name)
            np.savez(str(temp_im_path), im_stack)

        results = stats.agg_results(im_stack, rename=True)

        print(results.T)
        if args.save_csv:
            results.to_csv(foldername/filename)
    
        metadata=picam2.capture_metadata()
        print(metadata["ExposureTime"], metadata["AnalogueGain"])
        if abs(metadata["AnalogueGain"]-analog_gain)>0.1:
            raise ValueError(f"expected {metadata['AnalogueGain']} but configured {analog_gain}")
            

if __name__ == "__main__":
    main()

