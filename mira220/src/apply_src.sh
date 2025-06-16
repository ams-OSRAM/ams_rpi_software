LIBCAMERA_PATH=../../libcamera
SRC_PATH=.

cp $SRC_PATH/cam_helper_mira220.cpp $LIBCAMERA_PATH/src/ipa/rpi/cam_helper/
#pisp - pi5
cp $SRC_PATH/pisp/mira220.json $LIBCAMERA_PATH/src/ipa/rpi/pisp/data/
cp $SRC_PATH/pisp/mira220color.json $LIBCAMERA_PATH/src/ipa/rpi/pisp/data/
#vc4 - other
cp $SRC_PATH/vc4/mira220.json $LIBCAMERA_PATH/src/ipa/rpi/vc4/data/
cp $SRC_PATH/vc4/mira220color.json $LIBCAMERA_PATH/src/ipa/rpi/vc4/data/
