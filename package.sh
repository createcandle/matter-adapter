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


# Prep new package
echo "creating package"
mkdir -p lib package

python3 -m pip install --upgrade pip

# Pull down Python dependencies
#pip3 install -r requirements.txt -t lib --no-binary -no-cache-dir  :all: --prefix ""

wget https://github.com/home-assistant-libs/chip-wheels/releases/download/2022.12.0/home_assistant_chip_core-2022.12.0-cp37-abi3-manylinux_2_31_aarch64.whl
pip3 install home_assistant_chip_core-2022.12.0-cp37-abi3-manylinux_2_31_aarch64.whl -t lib  --prefix ""
pip3 install python-matter-server[server] -t lib  --prefix ""

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
