# Simple MPTCP

This repository contains installation scripts and essential documentation for setting up a basic Mininet topology that utilizes MPTCPv**1**, built directly from the source code.

## Topology

![image](https://user-images.githubusercontent.com/32551374/227388100-756203d9-67b2-47a8-91f7-a6e349ce5fd5.png)

## Setup Instructions

Follow these steps to set up the Simple MPTCP environment:

1. Clone the repository:
```bash
git clone https://github.com/mrconter1/simple_mptcp/
```

2. Navigate to the `simple_mptcp` directory and run the setup script. You can also follow the script manually if preferred:
```bash
cd simple_mptcp
sudo bash setup.sh
```

3. Reboot your computer after the successful execution of the script.

4. Verify that MPTCP has been installed correctly by executing `main.py`:
```bash
sudo python3 main.py
```

After completing these steps, you should have a functional Mininet topology with MPTCPv**1** support.
