
# clone libcamera source, and checkout a proved commit
# The tested commit is on 2022 April 4th.
COMMIT=302731cd
git clone https://git.libcamera.org/libcamera/libcamera.git
(cd libcamera && git checkout $COMMIT)

# apply patches and sources
(cd mira220/patch && ./apply_patch.sh)
(cd mira220/src && ./apply_src.sh)

# config, build, and install libcamera
(cd ./libcamera && meson build)
(cd ./libcamera && sudo ninja -C build install)
sudo ldconfig

