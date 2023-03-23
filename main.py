from mininet.link import Link, TCLink,Intf
from mininet.log import setLogLevel
from subprocess import Popen, PIPE
from mininet.clean import Cleanup
from mininet.net import Mininet
from datetime import datetime
from mininet.cli import CLI
from pathlib import Path

import numpy as np
import time
import os

def get_network():

    net = Mininet(link=TCLink)

    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    r1 = net.addHost('r1')

    net.addLink(r1, h1, cls=TCLink,
                    bw=100,
                    delay='10ms', 
                    loss=0)

    net.addLink(r1, h1, cls=TCLink,
                    bw=100,
                    delay='10ms', 
                    loss=0)

    net.addLink(r1, h2, cls=TCLink,
                    bw=1000,
                    delay='10ms', 
                    loss=0)
    
    net.build()

    r1.cmd("ifconfig r1-eth0 0")
    r1.cmd("ifconfig r1-eth1 0")
    r1.cmd("ifconfig r1-eth2 0")

    h1.cmd("ifconfig h1-eth0 0")
    h1.cmd("ifconfig h1-eth1 0")
    h2.cmd("ifconfig h2-eth0 0")

    r1.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")

    r1.cmd("ifconfig r1-eth0 10.0.0.1 netmask 255.255.255.0")
    r1.cmd("ifconfig r1-eth1 10.0.1.1 netmask 255.255.255.0")
    r1.cmd("ifconfig r1-eth2 10.0.2.1 netmask 255.255.255.0")
    h1.cmd("ifconfig h1-eth0 10.0.0.2 netmask 255.255.255.0")
    h1.cmd("ifconfig h1-eth1 10.0.1.2 netmask 255.255.255.0")
    h2.cmd("ifconfig h2-eth0 10.0.2.2 netmask 255.255.255.0")

    h1.cmd("ip rule add from 10.0.0.2 table 1")
    h1.cmd("ip rule add from 10.0.1.2 table 2")
    h1.cmd("ip route add 10.0.0.0/24 dev h1-eth0 scope link table 1")
    h1.cmd("ip route add default via 10.0.0.1 dev h1-eth0 table 1")
    h1.cmd("ip route add 10.0.1.0/24 dev h1-eth1 scope link table 2")
    h1.cmd("ip route add default via 10.0.1.1 dev h1-eth1 table 2")
    h1.cmd("ip route add default scope global nexthop via 10.0.0.1 dev h1-eth0")
    h2.cmd("ip rule add from 10.0.2.2 table 1")
    h2.cmd("ip route add 10.0.2.0/24 dev h2-eth0 scope link table 1")
    h2.cmd("ip route add default via 10.0.2.1 dev h2-eth0 table 1")
    h2.cmd("ip route add default scope global nexthop via 10.0.2.1 dev h2-eth0")

    return net, h1, h2

if '__main__' == __name__:

    # ----- Run single path -----
    print("--- Testing single path ---")

    # Disable mptcp
    os.system("sysctl -w net.mptcp.enabled=0")

    # Create mininet network
    net, h1, h2 = get_network()

    # Disable mptcp for each node
    h1.cmd("sysctl -w net.mptcp.enabled=0")
    h2.cmd("sysctl -w net.mptcp.enabled=0")

    # Start server
    h2.cmd("python3 server.py &")
    
    # Start and print client output
    print(h1.cmd("python3 client.py"))

    # ----- Run multipath-----
    print("--- Testing multipath ---")

    # Enable mptcp
    os.system("sysctl -w net.mptcp.enabled=1")

    # Create mininet network
    net, h1, h2 = get_network()

    # Enable MPTCP and set limits for h1 (client)
    h2.cmd("sysctl -w net.mptcp.enabled=1")
    h2.cmd("ip mptcp limits set subflows 4 add_addr_accepted 4")
    h2.cmd("ip mptcp endpoint add 10.0.2.2 dev h2-eth0 signal")

    h1.cmd("sysctl -w net.mptcp.enabled=1")
    h1.cmd("ip mptcp limits set subflows 4 add_addr_accepted 4")
    h1.cmd("ip mptcp endpoint add 10.0.0.2 dev h1-eth0 subflow fullmesh")
    h1.cmd("ip mptcp endpoint add 10.0.1.2 dev h1-eth1 subflow fullmesh")

    # Start server
    h2.cmd("python3 server.py &")
    
    # Start and print client output
    print(h1.cmd("python3 client.py"))
