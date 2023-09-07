
"""
this script can be ran from any device, when connected to a pi.
this will disable the pi sensor driver and do the i2c uploads manually from a file.
then, capture a raw file.
make sure to have the config parser file too.

"""

import cv2
import numpy as np
import sys
sys.path.append("../../common")
from config_parser import ConfigParser
from PIL import Image
from io import BytesIO
import numpy as np
import requests

# pi_address = 'raspberrypi.local'
pi_address = '10.61.100.177'

# have a look at the current controls
r = requests.get(f'http://{pi_address}:8000/controls')
print(r.content)
controls = r.json()
for key,value in controls.items():
    print(f'{key} {value}')


config_parser = ConfigParser()
reg_seq = config_parser.parse_file('./Mira220_register_sequence_12b_1600x1400.txt')
print(f"Parsed {len(reg_seq)} register writes from file.")

message = {"enable": "1"}
r = requests.put(f'http://{pi_address}:8000/registers/manual_mode', json = message)
print(r.content)

# DISABLE POWER EXAMPLE (reset pin)
message = {"enable": "0"}
r = requests.put(f'http://{pi_address}:8000/registers/power', json = message)
print(r.content)

# ENABLE POWER EXAMPLE
message = {"enable": "1"}
r = requests.put(f'http://{pi_address}:8000/registers/power', json = message)
print(r.content)


print(f"Writing {len(reg_seq)} registers to driver buffer via V4L2 interface.")
for reg in reg_seq:
    # WRITE REGISTER EXAMPLE
    message = {"reg": hex(reg[0]) , "val": hex(reg[1])}
    r = requests.put(f'http://{pi_address}:8000/registers/write', json = message)
    print(r.content)

# CAPTURE IMAGE ARRAY
r = requests.get(f'http://{pi_address}:8000/captureraw')
print(r.content)

# DOWNLOAD IMAGE ARRAY
r = requests.get(f'http://{pi_address}:8000/uploads/imgraw0.tiff')
print(r)
i = Image.open(BytesIO(r.content))
arr=np.asarray(i)
