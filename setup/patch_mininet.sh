# First run setup.sh from this repository to setup environment:
# https://github.com/mrconter1/simple_mptcp

# Change max bandwidth for Mininet from 1 Gpbs to 2 Gpbs
MININET_LINK_PATH=$(python3 -c 'import os, mininet; print(os.path.dirname(os.path.abspath(mininet.__file__)) + "/link.py")')

# Patch Mininet to allow for 2 Gbps
sudo sed -i "s/bwParamMax = .*/bwParamMax = 2000/g" $MININET_LINK_PATH
