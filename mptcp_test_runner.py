from mininet.link import Link, TCLink,Intf
from mininet.log import setLogLevel
from subprocess import Popen, PIPE
from mininet.clean import Cleanup
from mininet.net import Mininet
from mininet.cli import CLI
from pathlib import Path

import numpy as np
import datetime
import time
import os

# ------ Test instance run settings ----

config = {}

config["mptcp"] = 1

config["system_variables"] = None

# Default 1 Mb
config["bytes_to_transfer"] = 100 * 1000 ** 2

config["sample_size"] = 2

config["client_path_a"] = {}
config["client_path_a"]["bandwidth"] = 100
config["client_path_a"]["delay"] = 10
config["client_path_a"]["packet_loss"] = 0
# Queue size for h1-eth0
config["client_path_a"]["queue_size"] = 1000

config["client_path_b"] = {}
config["client_path_b"]["bandwidth"] = 100
config["client_path_b"]["delay"] = 10
config["client_path_b"]["packet_loss"] = 0
# Queue size for h1-eth1
config["client_path_b"]["queue_size"] = 1000

config["server_path"] = {}
# Run networking/setup.sh to enable 2 Gbps throughput
config["server_path"]["bandwidth"] = 2000
config["server_path"]["delay"] = 0
config["server_path"]["packet_loss"] = 0
# Queue size for h2-eth0
config["server_path"]["queue_size"] = 1000

data = []

def get_system_variables(mode):

    system_variables = {}

    system_variables["net.mptcp.scheduler"] = "default"
    system_variables["net.mptcp.checksum_enabled"] = 0
    system_variables["net.ipv4.tcp_no_metrics_save"] = 1

    if mode == "tcp":

        system_variables["net.mptcp.enabled"] = 0
        system_variables["net.ipv4.tcp_congestion_control"] = "cubic"

    elif mode == "mptcp":

        system_variables["net.mptcp.enabled"] = 1
        system_variables["net.ipv4.tcp_congestion_control"] = "cubic"

    return system_variables


def file_write(filename, text):
    with open(filename, 'a') as f:
        f.write(text)

def sample_sum_from_config(samples):

    times = []

    for i in range(samples):

        net, h1, h2 = initMininet()

        h2.cmd("python3 networking/server.py &")

        time.sleep(0.3)

        res = h1.cmd("python3 networking/client.py " + str(int(config["bytes_to_transfer"])))
        print(res)
        data_value = float(res.split("Total time: ")[-1].split(" ")[0])

        net.stop()

        times.append(data_value)

    return sum(times)

# Samples a config using single path topology and single path TCP
def sample_tcp(config, samples):

    config["mptcp"] = 0

    sum_tcp = sample_sum_from_config(samples)

    return sum_tcp

# Samples a config using multi path topology and MPTCP
def sample_mptcp(config, samples):

    config["mptcp"] = 1

    sum_mptcp = sample_sum_from_config(samples)

    return sum_mptcp

def rgb_to_hex(r, g, b):

    return '{:02x}{:02x}{:02x}'.format(r, g, b)

def get_color(value, min_value, max_value):

    middle_value = 100

    if value < middle_value:

        value = 1 - ((middle_value - value) / (middle_value - min_value))

        r = 255
        g = int(255 * value)

    elif value > 100:

        value = 1 - ((value - middle_value) / (max_value - middle_value))

        r = int(255 * value)
        g = 255

    else:

        r = 255
        g = 255

    b = 0

    return rgb_to_hex(r, g, b)

# This function takes a two dimensional list and generates a html-page with a table for it
def generate_table(data):

    html_filename = 'index.html'

    min_value = min(min(row[3:]) for row in data[2:])
    max_value = max(max(row[3:]) for row in data[2:])

    html = ''
    html += '<html>' + '\n'
    html += '<head>' + '\n'
    html += '\t' + '<meta http-equiv="refresh" content="5">' + '\n'
    html += '</head>' + '\n'
    html += '<style>' + '\n'
    html += 'table, tr, th, td {' + '\n'
    html += '\t' + 'border:1px solid black;' + '\n'
    html += '\t' + 'border-collapse: collapse;' + '\n'
    html += '}' + '\n'
    html += 'td {' + '\n'
    html += '\t' + 'display: inline-block' + '\n'
    html += '}' + '\n'
    html += '</style>' + '\n'
    html += '<body>' + '\n'
    html += '\n'
    html += '<table style="width:100%">' + '\n'
    
    for row_idx, row in enumerate(data):
        html += '\t' + '<tr>' + '\n'
        for col_idx, el in enumerate(row):
            if row_idx > 1 and col_idx > 2:
                html += '\t\t' + '<th style="background-color:' + get_color(el, min_value, max_value) + ';">' + str(el) + '</th>' + '\n'
            else:
                html += '\t\t' + '<th>' + str(el) + '</th>' + '\n'
        html += '\t' + '<tr>' + '\n'

    html += '</body>' + '\n'
    html += '</html>' + '\n'

    try:
        os.remove(html_filename)
    except:
        pass

    file_write(html_filename, html)

# This function generates a range of values
# It interleaves to generated sequences
# One range which is the power of ten => 1, 10, 100, 1000 etc
# The other one is linear values in between each power of ten => 1, 2.5, 5, 7.5, 10 
# Example:
#   (0.1, 1000, 3) => [0.1, 0.4, 0.7, 1.0, 1.0, 4.0, 7.0, 10.0, 40.0, 70.0, 100.0, 400.0, 700.0, 1000.0]
def generate_interval(start_value, stop_value, number_of_intermediate_steps):

    interval = []
    val = start_value
    # Add power of ten values
    while val < stop_value:

        linear_val = val

        if val <= stop_value:
            interval.append(val)
        val *= 10

        linear_stop = val

        linear_step_length = (linear_stop - linear_val) / (number_of_intermediate_steps + 1)

        linear_stop -= linear_step_length
        while linear_val < linear_stop:
            
            linear_val += linear_step_length
            if val <= stop_value:
                interval.append(round(linear_val, 3))

    interval.append(stop_value)

    return interval

def estimated_min_execution_time(transfer_sizes, primary_bws, primary_delays, secondary_bws, secondary_delays):

    environment_setup_teardown_time = 0.4
    total_time_in_seconds = 0

    for transfer_size in transfer_sizes:
        for primary_bw in primary_bws:
            for primary_delay in primary_delays:

                min_theoretical_transfer_time_primary = (transfer_size * 8) / primary_bw
                total_time_in_seconds += min_theoretical_transfer_time_primary
                total_time_in_seconds += environment_setup_teardown_time

                for secondary_bw in secondary_bws:
                    for secondary_delay in secondary_delays:
                        
                        min_theoretical_transfer_time_secondary = (transfer_size * 8) / (primary_bw + secondary_bw)
                        total_time_in_seconds += min_theoretical_transfer_time_secondary
                        total_time_in_seconds += environment_setup_teardown_time

    # Add sample factor
    total_time_in_seconds *= config["sample_size"]

    return total_time_in_seconds

def estimated_worst_case_execution_time(estimated_min_time):

    # adjustment_factor = actual_meaured_execution_time / theoretical_minimum_execution_time
    adjustment_factor = 2
    return estimated_min_time * adjustment_factor

def run_experiments():

    config["sample_size"] = 1

    # ----- Experiment range -----
    # Preferred: generate_interval(0.01, 100, 3)
    transfer_sizes = generate_interval(0.01, 100, 0)

    # Preferred: generate_interval(0.01, 1000, 3)
    primary_bws = generate_interval(0.1, 1000, 0)
    # Preferred: generate_interval(1, 1000, 3)
    primary_delays = generate_interval(1, 100, 0)

    # Preferred: generate_interval(0.01, 1000, 3)
    secondary_bws = generate_interval(0.1, 1000, 0)
    # Preferred: generate_interval(1, 1000, 3)
    secondary_delays = generate_interval(1, 100, 0)

    estimated_best_case = estimated_min_execution_time(transfer_sizes, primary_bws, primary_delays, secondary_bws, secondary_delays)
    estimated_min_time_in_hours = round(estimated_best_case / (60 * 60), 3)
    print("Estimated best case execution time: " + str(estimated_min_time_in_hours) + " hours")

    estimated_worst_case = estimated_worst_case_execution_time(estimated_best_case)
    estimated_max_time_in_hours = round(estimated_worst_case / (60 * 60), 3)
    print("Estimated worst case execution time: " + str(estimated_max_time_in_hours) + " hours")

    count = 0
    total = len(transfer_sizes) * len(primary_bws) * len(primary_delays) * len(secondary_bws) * len(secondary_delays)

    data = []
    data.append([])
    data.append([])

    data[0].append('n=' + str(config["sample_size"]))
    for i in range(2):
        data[0].append('')

    data[1].append("File size (Mb)")
    data[1].append("Mbps")
    data[1].append("Delay (ms)")

    for secondary_bw in secondary_bws:
        for secondary_delay in secondary_delays:
            data[0].append(str(secondary_bw) + ' Mbps')
            data[1].append(str(secondary_delay) + ' ms')

    for transfer_size in transfer_sizes:
        for primary_bw in primary_bws:
            for primary_delay in primary_delays:

                data.append([])

                config["bytes_to_transfer"] = int(transfer_size * 1000 ** 2)

                config["client_path_a"]["bandwidth"] = primary_bw
                config["client_path_a"]["delay"] = primary_delay

                sum_tcp = sample_tcp(config, config["sample_size"])

                data[-1].append(transfer_size)
                data[-1].append(primary_bw)
                data[-1].append(primary_delay)

                for secondary_bw in secondary_bws:
                    for secondary_delay in secondary_delays:

                        config["client_path_b"]["bandwidth"] = secondary_bw
                        config["client_path_b"]["delay"] = secondary_delay

                        sum_mptcp = sample_mptcp(config, config["sample_size"])

                        print("-------------------------------")

                        print("Run", count, "out of", total)

                        print()

                        print("Sample size:\t\t\t\t",       config["sample_size"])

                        print()

                        print("Primary bw:\t\t\t\t",        primary_bw,           "\tMbps")
                        print("Primary delay:\t\t\t\t",     primary_delay,        "\tms")

                        print("Secondary bw:\t\t\t\t",      secondary_bw,         "\tMbps")
                        print("Secondary delay:\t\t\t",     secondary_delay,      "\tms")

                        print()

                        total_transfer_size = transfer_size * config["sample_size"]
                        print("Transfer file size:\t\t\t", round(transfer_size, 2),  "\tMb")

                        print()
                        
                        print("Average transfer time\t(TCP):\t\t",   round(sum_tcp / config["sample_size"], 2),              "\tseconds")
                        tcp_throughput = (total_transfer_size * 8) / sum_tcp
                        print("Average Throughput\t(TCP):\t\t",          round(tcp_throughput, 2),       "\tMbps")

                        print()

                        print("Average transfer time\t(MPTCP):\t", round(sum_mptcp / config["sample_size"], 2),            "\tseconds")
                        mptcp_throughput = (total_transfer_size * 8) / sum_mptcp
                        print("Average Throughput\t(MPTCP):\t",      round(mptcp_throughput, 2),     "\tMbps")

                        print()

                        procentage_diff = round(100 * (mptcp_throughput / tcp_throughput), 1)

                        print("Improvement:\t\t\t\t",           procentage_diff, "\t%")

                        print("-------------------------------")

                        data[-1].append(procentage_diff)

                        generate_table(data)

                        count += 1

    return None

def initMininet():

    net = Mininet(link=TCLink)

    if config["mptcp"] == 0:
        
        config["system_variables"] = get_system_variables("tcp")

    elif config["mptcp"] == 1:

        config["system_variables"] = get_system_variables("mptcp")

    # Set all system variables
    for key, value in config["system_variables"].items():
        p = Popen("sysctl -w %s=%s" % (key, value), shell=True, stdout=PIPE, stderr=PIPE)

    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    r1 = net.addHost('r1')

    net.addLink(r1, h1, cls=TCLink,
                    bw=config["client_path_a"]["bandwidth"], 
                    delay=str(config["client_path_a"]["delay"])+'ms', 
                    loss=config["client_path_a"]["packet_loss"])

    net.addLink(r1, h1, cls=TCLink,
                    bw=config["client_path_b"]["bandwidth"], 
                    delay=str(config["client_path_b"]["delay"])+'ms', 
                    loss=config["client_path_b"]["packet_loss"])

    net.addLink(r1, h2, cls=TCLink,
                    bw=config["server_path"]["bandwidth"], 
                    delay=str(config["server_path"]["delay"])+'ms', 
                    loss=config["server_path"]["packet_loss"])
    
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

    # Set queue sizes for interfaces
    h1.cmd("sudo tc qdisc replace dev h1-eth0 root pfifo limit " + str(config["client_path_a"]["queue_size"]))
    h1.cmd("sudo tc qdisc replace dev h1-eth1 root pfifo limit " + str(config["client_path_b"]["queue_size"]))
    h2.cmd("sudo tc qdisc replace dev h2-eth0 root pfifo limit " + str(config["server_path"]["queue_size"]))

    # Disable second interface on server
    h2.cmd("ip link set h2-eth1 down")

    if config["mptcp"] == 1:

        # Enable MPTCP on h2 (server)
        h2.cmd("sysctl -w net.mptcp.enabled=1")
        h2.cmd("ip mptcp limits set subflows 4 add_addr_accepted 4")
        h2.cmd("ip mptcp endpoint add 10.0.2.2 dev h2-eth0 signal")

        # Enable MPTCP on h1 (client) 
        h1.cmd("sysctl -w net.mptcp.enabled=1")
        h1.cmd("ip mptcp limits set subflows 4 add_addr_accepted 4")
        h1.cmd("ip mptcp endpoint add 10.0.0.2 dev h1-eth0 fullmesh subflow")
        h1.cmd("ip mptcp endpoint add 10.0.1.2 dev h1-eth1 fullmesh subflow")

    else:

        # Disable MPTCP on both server and client
        h2.cmd("sysctl -w net.mptcp.enabled=0")
        h1.cmd("sysctl -w net.mptcp.enabled=0")

        # Disable second interface on client
        h1.cmd("ip link set h1-eth1 down")

    return net, h1, h2

if '__main__' == __name__:

    ct = datetime.datetime.now()
    print("Start time: ", ct)

    run_experiments()

    ct = datetime.datetime.now()
    print("Stop time: ", ct)
