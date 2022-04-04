#!/usr/bin/python
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
import time
import os

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
    

def addRouter(net=None, name=None, ip=None):
    if net and name and ip:
        return net.addHost(name, ip=ip)
    else:
        return None

def addRoute(router, route):
    if route:
        router.cmd(f"ip route add {route}")

def addSwitch(net=None, name=None):
    if net and name:
        switch = net.addSwitch(name)
        switch.cmd(f"ovs-ofctl add-flow {switch.name} \"actions=output:NORMAL\"")
        return switch
    else:
        return None

def setIP(router, iface, ip):
    if iface and ip:
        router.cmd(f"ifconfig {iface} {ip} up")

def topology(remote_controller):
    "Create a network."
    net = Mininet_wifi()

    info("*** Adding stations/hosts\n")

    h1A = net.addHost("h1A", ip="192.0.2.1/24")
    h1B = net.addHost("h1B", ip="192.0.3.1/24")
    h1C = net.addHost("h1C", ip="192.0.4.1/24")

    r1 = addRouter(net=net, name="r1", ip="192.0.2.254/24")
    r2 = addRouter(net=net, name="r2", ip="192.0.3.254/24")
    r3 = addRouter(net=net, name="r3", ip="192.0.4.254/24")

    info("*** Adding Switches (core)\n")

    switch1 = addSwitch(net=net, name="switch1")
    switch2 = addSwitch(net=net, name="switch2")
    switch3 = addSwitch(net=net, name="switch3")

    info("*** Creating links\n")

    net.addLink(h1A, switch1, bw=1000)
    net.addLink(r1, switch1, bw=1000)

    net.addLink(h1B, switch2, bw=1000)
    net.addLink(r2, switch2, bw=1000)

    net.addLink(h1C, switch3, bw=1000)
    net.addLink(r3, switch3, bw=1000)

    net.addLink(r1, r2, bw=1000)
    net.addLink(r1, r3, bw=1000)
    net.addLink(r2, r3, bw=1000)

    info("*** Starting network\n")
    net.start()
    net.staticArp()

    # info("*** Applying switches configurations\n")

    # switch1.cmd("ovs-ofctl add-flow {} \"actions=output:NORMAL\"".format(switch1.name))
    # switch2.cmd("ovs-ofctl add-flow {} \"actions=output:NORMAL\"".format(switch2.name))
    # switch3.cmd("ovs-ofctl add-flow {} \"actions=output:NORMAL\"".format(switch3.name))
    
    addRoute(router=h1A, route="default via 192.0.2.254")
    addRoute(router=h1B, route="default via 192.0.3.254")
    addRoute(router=h1C, route="default via 192.0.4.254")

    setIP(router=r1, iface="r1-eth1", ip="10.10.102.1/24")
    setIP(router=r2, iface="r2-eth1", ip="10.10.100.2/24")
    setIP(router=r2, iface="r2-eth2", ip="10.10.101.1/24")

    setIP(router=r3, iface="r3-eth1", ip="10.10.102.2/24")
    setIP(router=r3, iface="r3-eth2", ip="10.10.101.2/24")

    # run_router(r1)

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
    cleanup()
    # os.system("systemctl start zebra.service")
    setLogLevel("info")
    remote_controller = False
    topology(remote_controller)
