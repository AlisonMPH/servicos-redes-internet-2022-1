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

    h1A = net.addHost("h1A", ip="192.0.2.1/24")
    h1B = net.addHost("h1B", ip="192.0.3.1/24")
    h1C = net.addHost("h1C", ip="192.0.4.1/24")

    r1 = net.addHost("r1", ip="192.0.2.254/24")
    r2 = net.addHost("r2", ip="192.0.3.254/24")
    r3 = net.addHost("r3", ip="192.0.4.254/24")

    info("*** Adding Switches (core)\n")

    switch1 = net.addSwitch("switch1")
    switch2 = net.addSwitch("switch2")
    switch3 = net.addSwitch("switch3")

    info("*** Creating links\n")

    net.addLink(h1A, switch1, bw=BW)
    net.addLink(r1, switch1, bw=BW)

    net.addLink(h1B, switch2, bw=BW)
    net.addLink(r2, switch2, bw=BW)

    net.addLink(h1C, switch3, bw=BW)
    net.addLink(r3, switch3, bw=BW)

    net.addLink(r1, r2, bw=BW)
    net.addLink(r1, r3, bw=BW)
    net.addLink(r2, r3, bw=BW)

    info("*** Starting network\n")
    net.start()
    net.staticArp()

    info("*** Enabling switches\n")

    enableSwitch(switch1)
    enableSwitch(switch2)
    enableSwitch(switch3)

    info("*** Setting addresses and routes")

    addRoute(h1A, "default", "192.0.2.254")
    addRoute(h1B, "default", "192.0.3.254")
    addRoute(h1C, "default", "192.0.4.254")

    setIP(r1, "2", ip="10.10.100.1/24")
    setIP(r1, "3", ip="10.10.102.1/24")
    setIP(r2, "2", ip="10.10.100.2/24")
    setIP(r2, "3", ip="10.10.101.1/24")

    setIP(r3, "2", ip="10.10.102.2/24")
    setIP(r3, "3", ip="10.10.101.2/24")

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
