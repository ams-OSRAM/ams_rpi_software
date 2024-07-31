# camera tuning works as follows:

The Camera Tuning Tool (CTT) is a Python program designed to produce a fully working camera tuning JSON
file from a relatively small set of calibration images. Once the tool has run, there should be either no or only
minimal further tweaking to the JSON file required in order to obtain the desired image quality. The tuning
algorithms are furthermore designed to work with a minimum amount of expensive or specialised equipment.
The processes required in creating a finished camera tuning are as follows.
1. Firstly, a functional V4L2 camera driver must be written (see Chapter 3). For the purposes of writing the
camera driver, an uncalibrated tuning file can be copied which should provide recognisable images. Copy
one of vc4/data/uncalibrated.json (Pi 4 and earlier devices) or pisp/data/uncalibrated.json
(Pi 5), depending on the platform you are using. Care should also be taken that the black level listed in
the file is adjusted to match the black level specified in the sensor data sheet (and scaled up to a 16-bit
range).
2. The set of calibration images must be captured. Again, this should use the uncalibrated tuning file. There
are two types of calibration images, those with a Macbeth chart, and a further set of completely uniform
images for measuring lens shading.
3. On a Pi 5 you may optionally capture some images to tune the Chromatic Aberration Correction (CAC)
block. These images can also be omitted. This feature does not exist on Pi 4 or earlier devices.
4. With the calibration images all correctly named and stored in a folder, the CTT can be run. The CTT finds
Macbeth charts in images automatically and uses them to measure noise profiles, green imbalance, white
balance and colour matrices.
5. The output JSON file of the CTT can be used directly, possibly with minor further tweaking.

# Python Requirements
matplotlib
scipy
numpy
cv2
imutils
sklearn
pyexiv2
rawpy

# System requirements
sudo apt install python3-pip libexiv2-dev libboost-python-dev
pip3 install opencv-python imutils matplotlib scikit-learn py3exiv2 rawpy

# capturing images
## color checker
rpicam-still -r -o image.jpg --ev -1.0

imx219_2954k_1749l.dng for an image captured in 1749 lux with a colour temperature of 2954K, or
• 1749L_2954K.dng for the same image.

## lens shading imgs
alsc_3850k_1.dng and alsc_3850k_2.dng