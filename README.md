# Raspberry-Pi-Captive-Portal
This is a simple and workable example, as of the current date, that needs minimal installation and hardware to set up a captive portal on Raspberry Pi.

This setup assumes that your Pi connects to Wi-Fi and hosts a hotspot for the captive portal, and you configure the hotspot to use the **same channel** as the Wi-Fi connection so that you do not need an extra USB Wi-Fi dongle.

## Set up virtual network interface and hostapd (Python)
Edit the channel number to match the Wifi that Pi is connected to.
```
sudo apt-get update
```
```
sudo apt install hostapd
```
```
#Import the required modules
import os
import subprocess
import socket
import network

# Define the SSID and password for the access point
ssid = "Raspberry Pi AP"
password = "raspberry"

# Create a virtual network interface for the access point
os.system("sudo iw dev wlan0 interface add ap0 type __ap")

# Configure the IP address and netmask for the access point interface
os.system("sudo ip addr add 192.168.4.1/24 dev ap0")

# Enable the access point interface
os.system("sudo ip link set ap0 up")

# Create a hostapd configuration file with the SSID and password
with open("/etc/hostapd/hostapd.conf", "w") as f:
    f.write(f"""
interface=ap0
ssid={ssid}
wpa_passphrase={password}
hw_mode=g
channel=7
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP""")

# Start the hostapd service with the configuration file
os.system("sudo hostapd -B /etc/hostapd/hostapd.conf")
```
## Configure a static IP
```
sudo apt install dhcpcd
```
```
sudo nano /etc/dhcpcd.conf
```
```
interface ap0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```
```
sudo service dhcpcd restart
```
## Configure DHCP server (dnsmasq)

```
sudo apt install dnsmasq
```

```
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```
```
interface=ap0      # Use the require wireless interface - usually wlan0
dhcp-range=192.168.4.2,192.168.4.255,255.255.255.0,15m
address=/#/192.168.4.1 # Redirect all domains (the #) to the address 192.168.4.1 (the server on the (Pi)
```
```
sudo systemctl reload dnsmasq
```
## Redirect all traffic to 192.168.4.1:80
```
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 80 -j DNAT --to-destination 192.168.4.1:80
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 443 -j DNAT --to-destination 192.168.4.1:80
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
```

## Set up captive portal on 192.168.4.1:80 (Flask)
```
from flask import Flask, request, redirect, render_template
#import urllib
#import os

app = Flask(__name__)

# Pass the required route to the decorator.
@app.route("/hello")
def hello(hello):
    return "Hello, Welcome to GeeksForGeeks"

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    return render_template("captive.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=80) 

```

## References
1. https://sribasu.com/programming-tutorials/raspberry-pi-wifi-access-point-captive-portal-python.html
1. https://github.com/TomHumphries/RaspberryPiHotspot
1. https://github.com/AloysAugustin/captive_portal
