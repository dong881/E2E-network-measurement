#! /bin/bash
# every time you reboot you need to run this command
sudo cpupower idle-set -D 0
sudo tuned-adm profile realtime
# sudo tuned-adm active
# sudo tuned-adm profile network-latency

# starting sctp
sudo modprobe sctp

# set maximum ring buffers
sudo ethtool -G ens1f1 rx 4096
sudo ethtool -G ens1f1 tx 4096

# Set the maximum MTU
sudo ifconfig ens1f1 mtu 9000

# load the Linux "Base Driver for Intel Ethernet AdaptiveVirtual Function"
sudo modprobe iavf

# set two devices
sudo sh -c 'echo 0 > /sys/class/net/ens1f1/device/sriov_numvfs'
sudo sh -c 'echo 2 > /sys/class/net/ens1f1/device/sriov_numvfs'

# create virtual functions on physical one with MAC addresses and VLAN
sudo ip link set ens1f1 vf 0 mac 00:11:22:33:44:66 vlan 3 qos 0 spoofchk off mtu 9000
sudo ip link set ens1f1 vf 1 mac 00:11:22:33:44:66 vlan 3 qos 0 spoofchk off mtu 9000
sleep 1

# These are the DPDK bindings for C/U-planes on vlan
# unbind
sudo /usr/local/bin/dpdk-devbind.py --unbind 70:0a.0
sudo /usr/local/bin/dpdk-devbind.py --unbind 70:0a.1

# reload "Virtual Function I/O" driver 
sudo modprobe vfio_pci

# bind
sudo /usr/local/bin/dpdk-devbind.py --bind vfio-pci 70:0a.0
sudo /usr/local/bin/dpdk-devbind.py --bind vfio-pci 70:0a.1

# Check DPDK binding
sudo /usr/local/bin/dpdk-devbind.py --status

# show the vf
sudo lspci | grep Virtual

# Check configuration
ip link show ens1f1

# show the setting
sudo ethtool -g ens1f1

# show the setting
sudo ifconfig ens1f1