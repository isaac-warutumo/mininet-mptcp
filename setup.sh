#!/bin/bash

# Exit script if any command fails
set -e

# This setup assumes you are running:
# Ubuntu 22.10 (Kinetic Kudo)
# https://releases.ubuntu.com/kinetic/

# Make sure user is running this script as sudo
if [[ $UID != 0 ]]; then
	echo "Please run this script with sudo:"
	echo "sudo $0 $*"
	exit 1
fi

echo "Updating package lists..."
apt-get update

echo "Installing tools (Mininet >= 2.3.0)..."
apt-get install -y vim python3-pip mininet xterm

echo "Install build deps..."
apt-get install -y libncurses-dev gawk flex bison openssl libssl-dev dkms libelf-dev libudev-dev libpci-dev libiberty-dev autoconf llvm dwarves zstd

echo "Install test environment dependencies..."
pip3 install matplotlib mininet numpy

echo "Moving up one folder..."
cd ..

echo "Installing latest version of iproute2 (>= 6.2.0)..."
git clone https://github.com/shemminger/iproute2
cd iproute2
make install

echo "Moving up one folder..."
cd ..

echo "Cloning latest source code for MPTCPv1 (>= ace20054cd12bf71a678f4ac305e0d76ce495a39)..."
git clone --depth=1 https://github.com/multipath-tcp/mptcp_net-next

echo "Copying existing kernel .config for modification..."
cd mptcp_net-next
cp -v /boot/config-$(uname -r) .config

echo "Disabling certification related flags to avoid build errors..."
scripts/config --disable SYSTEM_REVOCATION_KEYS
scripts/config --disable SYSTEM_TRUSTED_KEYS

echo "Take existing kernel cfg and update it with new cfg options..."
make olddefconfig 

echo "Build kernel..."
make -j$(nproc)

echo "Install kernel..."
make modules_install
make install

GRUB_PATH="/etc/default/grub"

echo "Enable GRUB menu..."
sed -i "s/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=5/g" $GRUB_PATH
sed -i "s/GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=menu/g" $GRUB_PATH

echo "Make GRUB remember the last booted kernel..."
GRUB_PARAMETER="GRUB_SAVEDEFAULT=true"
if ! grep -q "^$GRUB_PARAMETER" "$GRUB_PATH"; then
	echo "$GRUB_PARAMETER" >> $GRUB_PATH
fi

echo "Make GRUB use the last booted kernel as the default for the next boot..."
sed -i "s/GRUB_DEFAULT=.*/GRUB_DEFAULT=saved/g" $GRUB_PATH

echo "Updating GRUB configuration..."
update-grub

echo "Kernel installation complete!"
echo "Please reboot your system for the changes to take effect..."
