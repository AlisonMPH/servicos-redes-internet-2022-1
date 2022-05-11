#!/usr/bin/python
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
import time
import os

BW=1000

def run_router(router):
    name = router.name
    services = ["zebra", "ospfd"]
    for srv in services:
        cmd = f"/usr/sbin/{srv} "
        cmd += f"-f /tmp/quagga/{srv}-{name}.conf -d -A 127.0.0.1 "
        cmd += f"-z /tmp/zebra-{name}.api -i /tmp/{srv}-{name}.pid "
        cmd += f"> /tmp/{srv}-{name}-router.log 2>&1"
        router.cmd(cmd)
        time.sleep(1)

def run_service(dhcp_server):
    name = dhcp_server.name
    services = ["dhcpd"]
    for srv in services:
        cmd = f"/usr/sbin/{srv} "
        cmd += f"-cf /tmp/{srv}/{srv}-{name}.conf -lf /tmp/{srv}/{srv}-{name}.leases"
        cmd += f"> /tmp/{srv}/{srv}-{name}-dhcp.log 2>&1"
        dhcp_server.cmd(f"echo > /tmp/{srv}/{srv}-{name}.leases")
        dhcp_server.cmd(cmd)
        time.sleep(1)

def run_dhcp_client(dhcp_client):
    name = dhcp_client.name
    services = ["dhclient"]
    for srv in services:
        cmd = f"{srv} -v -nw {name}-eth0"
        dhcp_client.cmd(cmd)
        time.sleep(1)

def enableSwitch(switch):
    switch.cmd(f"ovs-ofctl add-flow {switch.name} \"actions=output:NORMAL\"")

def addRoute(host, route):
    if host:
        host.cmd(f"ip route add {route}")

def setIP(host, iface=None, ip=None):
    if iface and ip:
        iface = iface - 1 
        host.cmd(f"ifconfig {host.name}-eth{iface} {ip} up")

def topology():
    "Create a network."
    net = Mininet_wifi()

    info("*** Adding stations/hosts\n")

    # Rede A
    h1 = net.addHost("h1", ip="0.0.0.0")
    h2 = net.addHost("h2", ip="0.0.0.0")
    h3 = net.addHost("h3", ip="0.0.0.0")
    h4 = net.addHost("h4", ip="0.0.0.0")
    h5 = net.addHost("h5", ip="0.0.0.0")
    h6 = net.addHost("h6", ip="0.0.0.0")
    h7 = net.addHost("h7", ip="0.0.0.0")
    
    # Roteadores
    dhcpsrv = net.addHost("dhcpsrv", ip="192.168.0.10/24")
    
    info("*** Adding Switches (core)\n")

    switch1 = net.addSwitch("switch1")
    
    info("*** Creating links\n")

    net.addLink(h1, switch1, bw=BW)
    net.addLink(h2, switch1, bw=BW)
    net.addLink(h3, switch1, bw=BW)
    net.addLink(h4, switch1, bw=BW)
    net.addLink(h5, switch1, bw=BW)
    net.addLink(h6, switch1, bw=BW)
    net.addLink(h7, switch1, bw=BW)
    net.addLink(dhcpsrv, switch1, bw=BW)

    info("*** Starting network\n")
    net.start()
    net.staticArp()

    info("*** Enabling switches\n")

    enableSwitch(switch1)
    
    info("*** Setting up dhcp server and dhcp-client\n")
    
    run_service(dhcpsrv)
    run_dhcp_client(h1)
    run_dhcp_client(h2)
    run_dhcp_client(h3)
    run_dhcp_client(h4)
    run_dhcp_client(h5)
    run_dhcp_client(h6)
    run_dhcp_client(h7)

    info("*** Running CLI\n")

    CLI(net)

    info("*** Stopping network\n")
    net.stop()
    os.system("killall -9 dhclient dhcpd zebra ripd bgpd ospfd > /dev/null 2>&1")


def cleanup():
    os.system("rm -f /tmp/zebra-*.pid /tmp/ripd-*.pid /tmp/ospfd-*.pid")
    os.system("rm -f /tmp/bgpd-*.pid /tmp/*-router.log")
    os.system("rm -fr /tmp/zebra-*.api")
    os.system("systemctl stop apparmor")
    os.system("systemctl disable apparmor")
    os.system("rm -f /tmp/dhcpd/dhcpd-*.conf /tmp/dhcpd/*-dhcp.log")
    os.system("rm -f /tmp/dhcpd/*.leases")
    os.system("mn -c >/dev/null 2>&1")
    os.system("killall -9 dhcpd zebra ripd bgpd ospfd > /dev/null 2>&1")
    os.system("rm -fr /tmp/quagga")
    os.system("rm -fr /tmp/dhcpd")
    os.system("cp -rvf conf/ /tmp/quagga")
    os.system("cp -rvf conf/ /tmp/dhcpd")
    os.system("chmod 777 /tmp/quagga -R")
    os.system("chmod 777 /tmp/dhcpd -R")
    os.system("echo 'hostname zebra' > /etc/quagga/zebra.conf")
    os.system("chmod 777 /etc/quagga/zebra.conf")

if __name__ == "__main__":
    cleanup()
    setLogLevel("info")
    topology()
