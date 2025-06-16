LIBCAMERA_PATH=../../libcamera
SRC_PATH=.
cp $SRC_PATH/cam_helper_mira130.cpp $LIBCAMERA_PATH/src/ipa/rpi/cam_helper/
cp $SRC_PATH/pisp/mira130.json $LIBCAMERA_PATH/src/ipa/rpi/pisp/data/
cp $SRC_PATH/mira130.json $LIBCAMERA_PATH/src/ipa/rpi/vc4/data/
