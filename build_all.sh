#!/usr/bin/env bash
set -e

cd "$( dirname "${BASH_SOURCE[0]}" )"

echo "${PWD}"

# clone libcamera source, and checkout a proved commit
# The tested commit is on 2022 April 4th.
COMMIT=302731cd
if [[ ! -d $PWD/libcamera ]]
then
	echo "Clone libcamera source and checkout commit id ${COMMIT}"
	git clone https://git.libcamera.org/libcamera/libcamera.git
    (cd $PWD/libcamera && git checkout $COMMIT)
fi

# apply patches and sources
echo "Applying patches to libcamera source"
(cd $PWD/mira220/patch && ./apply_patch.sh)
echo "Copying source files to libcamera source"
(cd $PWD/mira220/src && ./apply_src.sh)
echo "Applying patches to libcamera source"
(cd $PWD/mira050/patch && ./apply_patch.sh)
echo "Copying source files to libcamera source"
(cd $PWD/mira050/src && ./apply_src.sh)


# config, build, and install libcamera
echo "Inside libcamera dir, configure the build with meson"
(cd $PWD/libcamera && meson build)
echo "Inside libcamera dir, build and install with ninja"
(cd $PWD/libcamera && ninja -C build -j 2 )
(cd $PWD/libcamera && sudo ninja -C build install )
echo "Post-installation update"
sudo ldconfig

