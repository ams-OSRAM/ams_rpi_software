# For prerequisites and explanations, see https://qengineering.eu/install-gstreamer-1.18-on-raspberry-pi-4.html
gst-launch-1.0 libcamerasrc ! video/x-raw, width=576, height=768, framerate=5/1 ! videoconvert ! videoscale ! clockoverlay time-format="%D %H:%M:%S" ! autovideosink

