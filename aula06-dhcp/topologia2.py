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
        cmd += f"-pf /tmp/{srv}/{name}.pid -cf /tmp/{srv}/{srv}-{name}.conf -lf /tmp/{srv}/{srv}-{name}.leases"
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
    h1A = net.addHost("h1A", ip="0.0.0.0")
    h2A = net.addHost("h2A", ip="0.0.0.0")
    h3A = net.addHost("h3A", ip="0.0.0.0")
    h4A = net.addHost("h4A", ip="0.0.0.0")
    h5A = net.addHost("h5A", ip="0.0.0.0")

    # Rede B    
    h1B = net.addHost("h1B", ip="0.0.0.0")
    h2B = net.addHost("h2B", ip="0.0.0.0")
    h3B = net.addHost("h3B", ip="0.0.0.0")
    h4B = net.addHost("h4B", ip="0.0.0.0")
    h5B = net.addHost("h5B", ip="0.0.0.0")

    # Roteadores
    r1 = net.addHost("r1")
    r2 = net.addHost("r2")

    # Servidores DHCP
    dhcpA = net.addHost("dhcpA", ip="192.168.1.10/24")
    dhcpB = net.addHost("dhcpB", ip="10.20.200.10/24")

    info("*** Adding Switches (core)\n")

    switch1 = net.addSwitch("switch1")
    switch2 = net.addSwitch("switch2")
    
    info("*** Creating links\n")

    # Rede A
    net.addLink(h1A, switch1, bw=BW)
    net.addLink(h2A, switch1, bw=BW)
    net.addLink(h3A, switch1, bw=BW)
    net.addLink(h4A, switch1, bw=BW)
    net.addLink(h5A, switch1, bw=BW)
    net.addLink(r1, switch1, bw=BW)
    net.addLink(dhcpA, switch1, bw=BW)

    # Rede B
    net.addLink(h1B, switch2, bw=BW)
    net.addLink(h2B, switch2, bw=BW)
    net.addLink(h3B, switch2, bw=BW)
    net.addLink(h4B, switch2, bw=BW)
    net.addLink(h5B, switch2, bw=BW)
    net.addLink(r2, switch2, bw=BW)
    net.addLink(dhcpB, switch2, bw=BW)

    # r1 - r2
    net.addLink(r1, r2, bw=BW)

    info("*** Starting network\n")
    net.start()
    net.staticArp()

    info("*** Enabling switches\n")

    enableSwitch(switch1)
    enableSwitch(switch2)
    
    info("*** Setting up dhcp server and dhcp-client\n")
    
    run_service(dhcpA)
    run_service(dhcpB)
    run_dhcp_client(h1A)
    run_dhcp_client(h2A)
    run_dhcp_client(h3A)
    run_dhcp_client(h4A)
    run_dhcp_client(h5A)
    run_dhcp_client(h1B)
    run_dhcp_client(h2B)
    run_dhcp_client(h3B)
    run_dhcp_client(h4B)
    run_dhcp_client(h5B)

    info("*** Setting r1 and r2 IP addresses\n")

    setIP(r1, 1, "192.168.1.254/24")
    setIP(r1, 2, "199.198.1.1/30")

    setIP(r2, 1, "10.20.200.254/24")
    setIP(r2, 2, "199.198.1.2/30")

    addRoute(r1, "10.20.200.0/24 via 199.198.1.2")
    addRoute(r2, "192.168.1.0/24 via 199.198.1.1")

    addRoute(dhcpA, "default via 192.168.1.254")
    addRoute(dhcpB, "default via 10.20.200.254")

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
