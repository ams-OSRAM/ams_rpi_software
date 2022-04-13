
# clone libcamera source, and checkout a proved commit
# The tested commit is on 2022 April 4th.
COMMIT=302731cd
echo "Clone libcamera source and checkout commit id ${COMMIT}"
git clone https://git.libcamera.org/libcamera/libcamera.git
(cd libcamera && git checkout $COMMIT)

# apply patches and sources
echo "Applying patches to libcamera source"
(cd mira220/patch && ./apply_patch.sh)
echo "Copying source files to libcamera source"
(cd mira220/src && ./apply_src.sh)

# config, build, and install libcamera
echo "Inside libcamera dir, configure the build with meson"
(cd ./libcamera && meson build)
echo "Inside libcamera dir, build and install with ninja"
(cd ./libcamera && sudo ninja -C build install)
echo "Post-installation update"
sudo ldconfig

