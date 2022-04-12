# For prerequisites and explanations, see https://qengineering.eu/install-gstreamer-1.18-on-raspberry-pi-4.html
cd $(dirname "${BASH_SOURCE[0]}") && ./pmic_reset.sh
gst-launch-1.0 libcamerasrc ! video/x-raw, width=1600, height=1400, framerate=5/1 ! videoconvert ! videoscale ! clockoverlay time-format="%D %H:%M:%S" ! autovideosink

