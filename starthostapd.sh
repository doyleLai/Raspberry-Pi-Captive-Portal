#!/bin/bash

# Record the time when the script is run
echo $(date -u) "The script has run." >> starthostapd_log

# Check if the script is run as root
if [ $(id -u) -ne 0 ]
  then echo Please run this script as root or using sudo!
  exit
fi

# Create a virtual network interface for the access point
sudo iw dev wlan0 interface add ap0 type __ap

# Configure the IP address and netmask for the access point interface
sudo ip addr add 192.168.4.1/24 dev ap0

# Enable the access point interface
sudo ip link set ap0 up

# Create a hostapd configuration file with the SSID and password
sudo cat > /etc/hostapd/hostapd.conf << EOF
interface=ap0
ssid=Raspberry Pi AP
wpa_passphrase=raspberry
hw_mode=g
channel=7
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
EOF

# Start the hostapd service with the configuration file
sudo hostapd -B /etc/hostapd/hostapd.conf

#Configuring the DHCP server (dnsmasq) - https://github.com/TomHumphries/RaspberryPiHotspot

#redirect traffic
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 80 -j DNAT --to-destination 192.168.4.1:80
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 443 -j DNAT --to-destination 192.168.4.1:80
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
