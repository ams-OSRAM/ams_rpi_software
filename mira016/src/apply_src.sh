LIBCAMERA_PATH=../../libcamera
SRC_PATH=.

cp $SRC_PATH/cam_helper_mira016.cpp $LIBCAMERA_PATH/src/ipa/rpi/cam_helper/
#pisp - pi5
cp $SRC_PATH/pisp/mira016.json $LIBCAMERA_PATH/src/ipa/rpi/pisp/data/
#vc4 - other
cp $SRC_PATH/vc4/mira016.json $LIBCAMERA_PATH/src/ipa/rpi/vc4/data/
