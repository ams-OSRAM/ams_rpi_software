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

r = requests.get(f'http://{pi_address}:8000/uploads/imgraw0.tiff')
print(r)

r = requests.get(f'http://{pi_address}:8000/capture')
i = Image.open(BytesIO(r.content))


arr=np.asarray(i)
print(arr)