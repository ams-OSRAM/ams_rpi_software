LIBCAMERA_PATH=../../libcamera
PATCH_PATH=.

insert_file_A_into_file_B_before_pattern_C_if_pattern_D_does_not_exist () {
	A="$1"
	B="$2"
	C="$3"
	D="$4"
	grep -qF "$D" "$B"
	if [ $? -ne 0 ]; then
		echo "File $B does not contain pattern $D."
		echo "Insert contents of file $A before pattern $C."
		sed -i '/'"${C}"'/e cat '"${A}"'' $B
	else
		echo "File $B already contains pattern $D."
		echo "Skip inserting."
	fi
}

# Patch camera_sensor_properties.cpp

INSERT_FILE=$PATCH_PATH/camera_sensor_properties.cpp.txt
TARGET_FILE=$LIBCAMERA_PATH/src/libcamera/sensor/camera_sensor_properties.cpp
INSERT_BEFORE="imx219"
INSERT_IF_NOT_EXIST="poncha110"
insert_file_A_into_file_B_before_pattern_C_if_pattern_D_does_not_exist "$INSERT_FILE" "$TARGET_FILE" "$INSERT_BEFORE" "$INSERT_IF_NOT_EXIST" 

# Patch rpi data meson.build     'poncha110.json',   'poncha110color.json',

INSERT_FILE=$PATCH_PATH/rpi_data_meson.build.txt
TARGET_FILE=$LIBCAMERA_PATH/src/ipa/rpi/vc4/data/meson.build
INSERT_BEFORE="imx219.json"
INSERT_IF_NOT_EXIST="poncha110.json"
insert_file_A_into_file_B_before_pattern_C_if_pattern_D_does_not_exist "$INSERT_FILE" "$TARGET_FILE" "$INSERT_BEFORE" "$INSERT_IF_NOT_EXIST" 

# Patch rpi meson.build     'cam_helper_poncha110.cpp',

INSERT_FILE=$PATCH_PATH/rpi_meson.build.txt
TARGET_FILE=$LIBCAMERA_PATH/src/ipa/rpi/cam_helper/meson.build
INSERT_BEFORE='])'
INSERT_IF_NOT_EXIST="cam_helper_poncha110.cpp"
insert_file_A_into_file_B_before_pattern_C_if_pattern_D_does_not_exist "$INSERT_FILE" "$TARGET_FILE" "$INSERT_BEFORE" "$INSERT_IF_NOT_EXIST" 

