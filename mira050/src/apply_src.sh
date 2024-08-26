LIBCAMERA_PATH=../../libcamera
SRC_PATH=.
cp $SRC_PATH/cam_helper_mira050.cpp $LIBCAMERA_PATH/src/ipa/rpi/cam_helper/
cp $SRC_PATH/mira050.json $LIBCAMERA_PATH/src/ipa/rpi/vc4/data/
cp $SRC_PATH/mira050color.json $LIBCAMERA_PATH/src/ipa/rpi/vc4/data/
cp $SRC_PATH/mira050_pisp.json $LIBCAMERA_PATH/src/ipa/rpi/pisp/data/mira050.json
cp $SRC_PATH/mira050color_pisp.json $LIBCAMERA_PATH/src/ipa/rpi/pisp/data/mira050color.json