#!/bin/bash 

#-e
set -x # echo commands too

export DEBIAN_FRONTEND=noninteractive

echo ""
echo ""
echo "package.sh: PLATFORM:"
uname -a

pip install setuptools

echo "package.sh: Python version before:"
python3 --version
echo "package.sh: Python Setuptools version before:"
pip show setuptools


#lsb_release -a
#ldd --version
#echo "python before:"
#python3 --version
#pip3 --version
echo ""
echo ""
version=$(grep '"version"' manifest.json | cut -d: -f2 | cut -d\" -f2)

echo "."
echo ".."
echo "RUN"
#uname -a
echo "pwd:"
pwd
echo
echo "ls:"
ls
echo
echo "ls /:"
ls /
echo

sudo apt-get update -q

python3 -m pip install python-matter-server[server] -t lib --prefix "" --no-cache-dir

#python3 -m pip install home-assistant-chip-core --force-reinstall -t lib --prefix "" --no-cache-dir --upgrade
python3 -m pip install home-assistant-chip-core -t lib --prefix "" --no-cache-dir --upgrade

python3 -m pip install home_assistant_chip_clusters -t lib --prefix "" --no-cache-dir

#python3 -m pip install python-matter-server[server] -t lib --prefix "" --no-cache-dir --upgrade


python3 -m pip install \
    zeroconf \
    -t lib --prefix "" --no-cache-dir


python3 -m pip install \
    atomicwrites \
    -t lib --prefix "" --no-cache-dir



echo ""
echo ""
echo ""
echo ""
echo "LS lib after first round of pip:"
echo ""
ls lib
echo ""
echo ""
echo ""


echo
echo "PACKAGE.SH ALMOST THERE FOR PYTHON LIBS"


#python3 -m pip install coloredlogs aiorun requests click click_option_group -t lib --prefix "" --no-binary :all: --no-cache-dir
python3 -m pip install coloredlogs aiorun requests click click_option_group -t lib --prefix "" --no-cache-dir
    
    
    
    #home_assistant_chip_clusters \
    #home_assistant_chip_core \
    #home_assistant_chip_repl \
    #home_assistant_chip_clusters-2023.1.0-py3-none-any.whl \
    #home_assistant_chip_core-2023.1.0-cp37-abi3-manylinux_2_31_aarch64.whl \
    #home_assistant_chip_core-2023.1.0-py3-none-any.whl \
    #home_assistant_chip_repl-2023.1.0-py3-none-any.whl \
    
    

echo "LS lib after second round of pip:"
ls lib

#pip3 install -r requirements.txt -t lib --no-cache-dir --no-binary  :all: --prefix ""

if [ -f ./lib/aiorun.py ]; then
  echo "OK aiorun installed succesfully"
else
  echo "aiorun FAILED TO INSTALL?"
  ls ./lib/aiorun*
fi

if [ -z "${ADDON_ARCH}" ]; then
  TARFILE_SUFFIX=
else
  #PYTHON_VERSION="$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d. -f 1-2)"
  PYTHON_VERSION="3.13"
  TARFILE_SUFFIX="-${ADDON_ARCH}-v${PYTHON_VERSION}"
fi

mkdir -p package

# Put package together
cp -r lib pkg LICENSE manifest.json *.py README.md css images js views  package/
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

echo ""
echo "DONE! files:"
ls -lh

