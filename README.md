# Simple MPTCP

This repository provides installation scripts and essential documentation to set up a basic Mininet topology using MPTCPv**1**.

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
