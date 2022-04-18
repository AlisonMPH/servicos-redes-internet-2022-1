#!/usr/bin/python
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
import time
import os

BW = 1000


def run_router(router):
    name = router.name
    services = ["zebra", "ripd"]
    for srv in services:
        cmd = f"/usr/sbin/{srv} "
        cmd += f"-f /tmp/quagga/{srv}-{name}.conf -d -A 127.0.0.1 "
        cmd += f"-z /tmp/zebra-{name}.api -i /tmp/{srv}-{name}.pid "
        cmd += f"> /tmp/{srv}-{name}-router.log 2>&1"
        router.cmd(cmd)
        time.sleep(1)


def enableSwitch(switch):
    switch.cmd(f'ovs-ofctl add-flow {switch.name} "actions=output:NORMAL"')


def addRoute(host, src, dest):
    if host:
        host.cmd(f"ip route add {src} via {dest}")


def setIP(host, if_number=None, ip=None):
    if if_number and ip:
        if_number = if_number - 1
        host.cmd(f"ifconfig {host.name}-eth{if_number} {ip} up")


def topology(remote_controller):
    "Create a network."
    net = Mininet_wifi()

    info("*** Adding stations/hosts\n")

    h1A = net.addHost("h1A", ip="200.15.35.1/24")
    h2A = net.addHost("h2A", ip="200.15.35.2/24")
    r1A = net.addHost("r1A", ip="200.15.35.254/24")

    h1B = net.addHost("h1B", ip="198.98.99.65/27")
    r2B = net.addHost("r2B", ip="198.98.99.94/27")

    h1C = net.addHost("h1C", ip="200.57.59.1/24")
    h2C = net.addHost("h2C", ip="200.57.59.2/24")
    r3C = net.addHost("r3C", ip="200.57.59.254/24")

    h1D = net.addHost("h1D", ip="198.98.99.33/27")
    h2D = net.addHost("h2D", ip="198.98.99.34/27")
    r4D = net.addHost("r4D", ip="198.98.99.62/27")

    info("*** Adding Switches (core)\n")

    switch1 = net.addSwitch("switch1")
    switch2 = net.addSwitch("switch2")
    switch3 = net.addSwitch("switch3")
    switch4 = net.addSwitch("switch4")

    info("*** Creating links\n")

    net.addLink(h1A, switch1, bw=BW)
    net.addLink(h2A, switch1, bw=BW)
    net.addLink(r1A, switch1, bw=BW)

    net.addLink(h1B, switch2, bw=BW)
    net.addLink(r2B, switch2, bw=BW)

    net.addLink(h1C, switch3, bw=BW)
    net.addLink(h2C, switch3, bw=BW)
    net.addLink(r3C, switch3, bw=BW)

    net.addLink(h1D, switch4, bw=BW)
    net.addLink(h2D, switch4, bw=BW)
    net.addLink(r4D, switch4, bw=BW)

    net.addLink(r1A, r2B, bw=BW)
    net.addLink(r1A, r3C, bw=BW)
    net.addLink(r2B, r4D, bw=BW)
    net.addLink(r3C, r4D, bw=BW)

    info("*** Starting network\n")
    net.start()
    net.staticArp()

    info("*** Enabling switches\n")

    enableSwitch(switch1)
    enableSwitch(switch2)
    enableSwitch(switch3)
    enableSwitch(switch4)

    info("*** Setting addresses\n")

    addRoute(h1A, "default", "200.15.35.254")
    addRoute(h2A, "default", "200.15.35.254")
    addRoute(h1B, "default", "198.98.99.94")
    addRoute(h1C, "default", "200.57.59.254")
    addRoute(h2C, "default", "200.57.59.254")
    addRoute(h1D, "default", "198.98.99.62")
    addRoute(h2D, "default", "198.98.99.62")

    setIP(r1A, 2, ip="200.1.2.1/30")
    setIP(r2B, 2, ip="200.1.2.2/30")

    setIP(r1A, 3, ip="200.1.2.5/30")
    setIP(r3C, 2, ip="200.1.2.6/30")

    setIP(r2B, 3, ip="200.1.2.9/30")
    setIP(r4D, 2, ip="200.1.2.10/30")

    setIP(r3C, 3, ip="200.1.2.13/30")
    setIP(r4D, 3, ip="200.1.2.14/30")

    info("*** Setting routes\n")
    # Rede A e B
    addRoute(r1A, "198.98.99.64/27", "200.1.2.2")
    addRoute(r2B, "200.15.35.0/24", "200.1.2.1")
    # Rede A e C
    addRoute(r1A, "200.57.59.0/24", "200.1.2.6")
    addRoute(r3C, "200.15.35.0/24", "200.1.2.5")
    # Rede B e D
    addRoute(r2B, "198.98.99.32/27", "200.1.2.10")
    addRoute(r4D, "198.98.99.64/27", "200.1.2.9")
    # Rede C e D
    addRoute(r3C, "198.98.99.32/27", "200.1.2.14")
    addRoute(r4D, "200.57.59.0/24", "200.1.2.13")
    # Rede A e D
    addRoute(r1A, "198.98.99.32/27", "200.1.2.2")
    addRoute(r4D, "200.15.35.0/24", "200.1.2.9")
    # Rede B e C
    addRoute(r3C, "198.98.99.64/27", "200.1.2.5")
    addRoute(r2B, "200.57.59.0/24", "200.1.2.1")

    info("*** Running CLI\n")

    CLI(net)

    info("*** Stopping network\n")
    net.stop()
    os.system("killall -9 zebra ripd bgpd ospfd > /dev/null 2>&1")


def cleanup():
    os.system("rm -f /tmp/zebra-*.pid /tmp/ripd-*.pid /tmp/ospfd-*.pid")
    os.system("rm -f /tmp/bgpd-*.pid /tmp/*-router.log")
    os.system("rm -fr /tmp/zebra-*.api")
    os.system("mn -c >/dev/null 2>&1")
    os.system("killall -9 zebra ripd bgpd ospfd > /dev/null 2>&1")
    os.system("rm -fr /tmp/quagga")
    os.system("cp -rvf conf/ /tmp/quagga")
    os.system("chmod 777 /tmp/quagga -R")
    os.system("echo 'hostname zebra' > /etc/quagga/zebra.conf")
    os.system("chmod 777 /etc/quagga/zebra.conf")


if __name__ == "__main__":
    # cleanup()
    # os.system("systemctl start zebra.service")
    setLogLevel("info")
    remote_controller = False
    topology(remote_controller)
