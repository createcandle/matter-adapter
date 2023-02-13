#!/bin/bash 

#-e


version=$(grep '"version"' manifest.json | cut -d: -f2 | cut -d\" -f2)

# Setup environment for building inside Dockerized toolchain
[ $(id -u) = 0 ] && umask 0

# Clean up from previous releases
echo "removing old files"
rm -rf *.tgz *.sha256sum package SHA256SUMS lib

if [ -z "${ADDON_ARCH}" ]; then
  TARFILE_SUFFIX=
else
  PYTHON_VERSION="$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d. -f 1-2)"
  TARFILE_SUFFIX="-${ADDON_ARCH}-v${PYTHON_VERSION}"
fi


echo "installing apt packages"
sudo apt-get update
sudo apt-get install cairo pkgconf gobject-introspection gtk3 libcairo2-dev libjpeg-dev libpango1.0-dev libgif-dev build-essential g++ libgirepository1.0-dev  -y
# Not sure is libjpeg-dev is the correct one

echo "installing rust compiler"
#curl https://sh.rustup.rs -sSf | sh -s -- -y

#exit 0
#echo "I SHOULD NOT BE SEEN"

# Prep new package
echo "creating package"
mkdir -p lib package

PY11="no"
python3.11 --version && PY11="yes"

PIPPY="pip3"
python3.11 --version && PIPPY="python3.11 -m pip"
echo "PIP STRING: $PIPPY"

# Is upgrading pip needed?
# "$PIPPY" install --upgrade pip

# Pull down Python dependencies


#wget https://github.com/home-assistant-libs/chip-wheels/releases/download/2022.12.0/home_assistant_chip_core-2022.12.0-cp37-abi3-manylinux_2_31_aarch64.whl
#pip3 install home_assistant_chip_core-2022.12.0-cp37-abi3-manylinux_2_31_aarch64.whl -t lib  --prefix ""

#wget  https://github.com/home-assistant-libs/chip-wheels/releases/download/2022.12.0/home_assistant_chip_repl-2022.12.0-py3-none-any.whl
#pip3 install home_assistant_chip_repl-2022.12.0-py3-none-any.whl -t lib  --prefix ""

#wget https://github.com/home-assistant-libs/chip-wheels/releases/download/2022.12.0/home_assistant_chip_clusters-2022.12.0-py3-none-any.whl
#pip3 install home_assistant_chip_clusters-2022.12.0-py3-none-any.whl -t lib  --prefix ""


#pip3 install aiohttp -t lib --no-binary :all: --prefix ""
#pip3 install aiorun -t lib --no-binary :all: --prefix ""
#pip3 install python-matter-server[server] -t lib  --prefix ""

#wget -c https://github.com/home-assistant-libs/chip-wheels/releases/download/2023.1.0/home_assistant_chip_core-2023.1.0-cp37-abi3-manylinux_2_31_aarch64.whl -O home_assistant_chip_core-2023.1.0-cp37-abi3-manylinux_2_31_aarch64.whl


#wget -c https://github.com/home-assistant-libs/chip-wheels/releases/download/2023.1.0/home_assistant_chip_repl-2023.1.0-py3-none-any.whl -O home_assistant_chip_repl-2023.1.0-py3-none-any.whl
#wget -c https://github.com/home-assistant-libs/chip-wheels/releases/download/2023.1.0/home_assistant_chip_clusters-2023.1.0-py3-none-any.whl -O home_assistant_chip_clusters-2023.1.0-py3-none-any.whl

# doesn't seem to work
# $PIPPY install -r requirements.txt -t lib --no-cache-dir --no-binary  :all: --prefix ""

#if [ "$PY11" = "yes" ]; then
#  python3.11 -m pip install home_assistant_chip_core-2023.1.0-cp37-abi3-manylinux_2_31_aarch64.whl -t lib  --prefix ""
#  python3.11 -m pip install home_assistant_chip_repl-2023.1.0-py3-none-any.whl -t lib  --prefix ""
#  python3.11 -m pip install home_assistant_chip_clusters-2023.1.0-py3-none-any.whl -t lib  --prefix ""
#  
#  python3.11 -m pip install python-matter-server[server] -t lib --prefix ""
#  python3.11 -m pip install aiorun -t lib --prefix ""
#else
#  pip3 install home_assistant_chip_core-2023.1.0-cp37-abi3-manylinux_2_31_aarch64.whl -t lib  --prefix ""
#  pip3 install home_assistant_chip_repl-2023.1.0-py3-none-any.whl -t lib  --prefix ""
#  pip3 install home_assistant_chip_clusters-2023.1.0-py3-none-any.whl -t lib  --prefix ""

#  pip3 install python-matter-server[server] -t lib --prefix ""
#  pip3 install aiorun -t lib --prefix ""
#fi

wget -c https://github.com/home-assistant-libs/chip-wheels/releases/download/2023.1.0/home_assistant_chip_clusters-2023.1.0-py3-none-any.whl -O home_assistant_chip_clusters-2023.1.0-py3-none-any.whl
wget -c https://github.com/home-assistant-libs/chip-wheels/releases/download/2023.1.0/home_assistant_chip_core-2023.1.0-cp37-abi3-manylinux_2_31_aarch64.whl -O home_assistant_chip_core-2023.1.0-cp37-abi3-manylinux_2_31_aarch64.whl
wget -c https://github.com/home-assistant-libs/chip-wheels/releases/download/2023.1.0/home_assistant_chip_repl-2023.1.0-py3-none-any.whl -O home_assistant_chip_repl-2023.1.0-py3-none-any.whl

pip3 install coloredlogs aiorun python-matter-server[server] requests click click_option_group \
    home_assistant_chip_clusters-2023.1.0-py3-none-any.whl \
    home_assistant_chip_core-2023.1.0-cp37-abi3-manylinux_2_31_aarch64.whl \
    home_assistant_chip_repl-2023.1.0-py3-none-any.whl \
    -t lib --prefix ""


#pip3 install -r requirements.txt -t lib --no-cache-dir --no-binary  :all: --prefix ""

if [ -f ./lib/aiorun.py ]; then
  echo "OK aiorun installed succesfully"
else
  echo "aiorun FAILED TO INSTALL"
fi

# Put package together
cp -r lib pkg LICENSE manifest.json *.py README.md  css images js views  package/
find package -type f -name '*.pyc' -delete
find package -type f -name '._*' -delete
find package -type d -empty -delete
rm -rf package/pkg/pycache

# Generate checksums
echo "generating checksums"
cd package
find . -type f \! -name SHA256SUMS -exec shasum --algorithm 256 {} \; >> SHA256SUMS
cd -

# Make the tarball
echo "creating archive"
TARFILE="matter-adapter-${version}${TARFILE_SUFFIX}.tgz"
tar czf ${TARFILE} package

echo "creating shasums"
shasum --algorithm 256 ${TARFILE} > ${TARFILE}.sha256sum
cat ${TARFILE}.sha256sum
#sha256sum ${TARFILE}
#rm -rf SHA256SUMS package
