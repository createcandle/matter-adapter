#!/bin/bash

# THIS DOES NOT INSTALL THE ADDON, IT INSTALLS MATTER "RAW". USED TO TEST.
# BASED ON: https://community.arm.com/arm-community-blogs/b/internet-of-things-blog/posts/build-a-matter-home-automation-service-using-raspberry-pi-arm-virtual-hardware-and-python
# IT USES A LOT OF SPACE, SO CANNOT BE RUN ON A CANDLE CONTROLLER, OR YOU WILL RUN OUT OF SPACE

sudo apt-get update

sudo apt-get install -y git gcc g++ python3 pkg-config libssl-dev libdbus-1-dev libglib2.0-dev libavahi-client-dev ninja-build python3-venv python3-dev python3-pip unzip libgirepository1.0-dev libcairo2-dev libreadline-dev

sudo apt-get install -y clang protobuf-compiler llvm

pip install --upgrade pip


# maybe not necessary
export PATH=$PATH:/usr/bin/clang-11:/usr/bin/clang++-11 


rm rust_installer.sh

curl https://sh.rustup.rs -sSf -o rust_installer.sh
sudo chmod +x rust_installer.sh
#echo "1 " | ./rust_installer.sh
yes 1 | ./rust_installer.sh

source "$HOME/.cargo/env"

if [ ! -f /bin/gn ]; then

    git clone https://gn.googlesource.com/gn
    cd gn
    python build/gen.py
    ninja -C out
    sudo cp out/gn /bin/gn
    cd ~
else
    echo "GN was already installed"
    
fi


rm -rf connectedhomeip

git clone https://github.com/project-chip/connectedhomeip.git

cd connectedhomeip

./scripts/checkout_submodules.py --shallow --platform linux

./scripts/build/gn_bootstrap.sh

source scripts/activate.sh

# builds the test client
./scripts/build_python.sh -d true -i separate

echo
echo "DONE"
echo
