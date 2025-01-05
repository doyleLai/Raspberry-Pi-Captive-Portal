# Set up a Raspberry Pi Captive Portal (Workable Example!)
This is a workable, as of Jan 2025, and simple example that needs minimal installation and hardware to set up a captive portal on a Raspberry Pi. I guarantee it works on the Pi Zero 2 board. I created this because there are many guidelines on the internet, but all of them are outdated and cannot work on the current Pi OS. Even the same topic on the Raspberry Pi official website does not work! I have gone through many guidelines and consolidated the up-to-date commands to guide you through how to create a Captive Portal on Raspberry Pi.


A Captive Portal is usually the landing page for logging in before connecting to the internet. In fact, there is no need to really connect the hotspot clients to the internet. With this technology, you can use it for many other purposes. For example, you can use the webpage for data entry. This guideline focuses on how to create the Captive Portal but how you use the Captive Portal is up to you. In this demo, I will set up the captive portal as a Wi-Fi configuration page for inputting the Wi-Fi password so that the Raspberry Pi can connect to a Wi-Fi network. This is useful when you need to deploy the board in an environment where the Wi-Fi credentials cannot be pre-installed. The code logic for accepting inputs and configuring the Wi-Fi is in the Flask app web server. You can modify the Flask app for another purpose.


This setup creates a virtual network interface on the network card. You can use the default interface to connect the Raspberry Pi to a Wi-Fi network. While on the same channel, you can use the virtual interface to create a hotspot to accept connections - no need for an extra Wi-Fi dongle!

## Configure virtual network interface


Create a virtual network interface ap0 for the access point
```
sudo iw dev wlan0 interface add ap0 type __ap
```
Configure the IP address and netmask for ap0
```
sudo ip addr add 192.168.4.1/24 dev ap0
```
Enable the interface
```
sudo ip link set ap0 up
```
## Configure hotspot (hostapd)
Update the apt and install hosapd
```
sudo apt update
```
```
sudo apt install hostapd
```
Create a hostapd configuration file with the SSID and password
```
sudo nano /etc/hostapd/hostapd.conf
```
Save the file with the following configurations. We are creating the hotspot service on the ap0 interface. You can edit the ssid and passphrase value to suit your need. The channel number does not really metter as the virtual interface will automaiclly use the same channel that the default interface is using.
```
interface=ap0
ssid=Raspberry Pi AP
wpa_passphrase=raspberry
hw_mode=g
channel=7
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
```

Start the hostapd service with the configuration file
```
sudo hostapd -B /etc/hostapd/hostapd.conf
```

## Configure a static IP (dhcpcd)
You need a static IP for the interface. This step is still needed altought your have set the ip address for the interface in the previous step.

Install dhcpcd
```
sudo apt install dhcpcd
```
Create a dhcpcd configuration file with the ip address for ap0
```
sudo nano /etc/dhcpcd.conf
```
Save the file with the following configurations. 
```
interface ap0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
```
Restart the dhcpcd service to make the configuration effective
```
sudo service dhcpcd restart
```
## Configure DHCP server (dnsmasq)
We need to create a DHCP server to assign IPs to clients who connect the hotspot.

Install dnsmasq
```
sudo apt install dnsmasq
```
We are creating a new configuration file. Backup the default one.
```
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
```
```
sudo nano /etc/dnsmasq.conf
```
Save the file with the following configurations. 
```
interface=ap0     
dhcp-range=192.168.4.2,192.168.4.255,255.255.255.0,15m
address=/#/192.168.4.1
```
Reload the configuration files for the dnsmasq service
```
sudo systemctl reload dnsmasq
```
## Redirect all traffic to 192.168.4.1:80
Not sure if you need to install iptables. If the command cannot be found, install it.

```
sudo apt install iptables
```
Redirect all incoming traffic on 80 to 192.168.4.1:80, where we will set up a web server on it.
```
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 80 -j DNAT --to-destination 192.168.4.1:80
```
Do the same for for 443
```
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 443 -j DNAT --to-destination 192.168.4.1:80
```
Make the setting effective
```
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
```

## Set up captive portal on 192.168.4.1:80 (Flask)
We will use python and Flask framwork to host the captive portal. 
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
