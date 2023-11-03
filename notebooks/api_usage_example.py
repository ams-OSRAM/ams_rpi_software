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

# replace the current controls
controls['exposure_us']=3000
r = requests.put(f'http://{pi_address}:8000/controls', json = controls)
print(r.content)

# replace single controls
controls['exposure_us']=3000
r = requests.put(f'http://{pi_address}:8000/controls/exposure_us', 'true')
print(r)

# replace single controls
controls['analog_gain']=1.1
r = requests.put(f'http://{pi_address}:8000/controls/', json = controls)
print(r)

# replace single controls
controls['analog_gain']=1.1
r = requests.put(f'http://{pi_address}:8000/controls/', json = controls)
print(r)
# r = requests.get(f'http://{pi_address}:8000/index')
# print(r.content)

# CAPTURE IMAGE ARRAY
r = requests.get(f'http://{pi_address}:8000/captureraw')
print(r.content)

# DOWNLOAD IMAGE ARRAY
r = requests.get(f'http://{pi_address}:8000/uploads/imgraw0.tiff')
print(r)
i = Image.open(BytesIO(r.content))
arr=np.asarray(i)
print(arr)

# READ REGISTER EXAMPLE
message = {"reg": "0x100d"}
r = requests.put(f'http://{pi_address}:8000/registers/read', json = message)
print(r.content)

# WRITE REGISTER EXAMPLE
message = {"reg": "0x100d", "val": "0x2"}
r = requests.put(f'http://{pi_address}:8000/registers/write', json = message)
print(r.content)

# ENABLE MANUAL MODE (disable reg upload and reset)
message = {"enable": "1"}
r = requests.put(f'http://{pi_address}:8000/registers/manual_mode', json = message)
print(r.content)

# DISABLE MANUAL MODE (disable reg upload and reset)
message = {"enable": "0"}
r = requests.put(f'http://{pi_address}:8000/registers/manual_mode', json = message)
print(r.content)

# ENABLE STREAM CONTROL (while in manual mode, still let picam2 write start/stop stream register)
message = {"enable": "1"}
r = requests.put(f'http://{pi_address}:8000/registers/stream_ctrl', json = message)
print(r.content)

# (default) DISABLE STREAM CONTROL (while in manual mode, user manually write start/stop stream register)
message = {"enable": "0"}
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

