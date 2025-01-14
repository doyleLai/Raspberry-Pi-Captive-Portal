# Set up a Raspberry Pi Captive Portal (Workable Example!)
This is a workable, as of Jan 2025, and simple example that needs minimal installation and hardware to set up a captive portal on a Raspberry Pi. I guarantee it works on the Pi Zero 2 board. I created this because there are many guidelines on the internet, but all of them are outdated and cannot work on the current Pi OS. Even the same topic on the Raspberry Pi official website does not work! I have gone through many guidelines and consolidated the up-to-date commands to guide you through how to create a Captive Portal on Raspberry Pi.

A Captive Portal is usually the landing page for logging in before connecting to the internet. In fact, there is no need to really connect the hotspot clients to the internet. With this technology, you can use it for many other purposes. For example, you can use the webpage for data entry. This guideline focuses on how to create the captive portal but how you use the it is up to you. In the steps here, the captive portal is a simple echo system that displays the text that the user has submitted.

>In the repository file, the captive portal is a Wi-Fi configuration page for inputting Wi-Fi password to let the Raspberry Pi connect to a Wi-Fi network. This is useful when you need to deploy the board in an environment where the Wi-Fi credentials cannot be pre-installed. You can modify the Flask app to suit your needs.

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
You need a static IP for the interface. This step is still needed altough your have set the ip address for the interface in the previous step.

Install dhcpcd
```
sudo apt install dhcpcd
```
Create a dhcpcd configuration file with the ip address for ap0
```
sudo nano /etc/dhcpcd.conf
```
Add the following configurations to the file. 
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
Open the dnsmasq configuration file
```
sudo nano /etc/dnsmasq.conf
```
Add the following configurations to the file. 
```
interface=ap0     
dhcp-range=192.168.4.2,192.168.4.255,255.255.255.0,15m
address=/#/192.168.4.1
```
Reload the dnsmasq service for the new configurations
```
sudo systemctl reload dnsmasq
```
Restart the dnsmasq service
```
sudo service dnsmasq restart
```
## Redirect all traffic to 192.168.4.1:80
Install iptables

```
sudo apt install iptables
```
Redirect all incoming traffic on port 80 to 192.168.4.1, where we will set up a web server on it.
```
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 80 -j DNAT --to-destination 192.168.4.1:80
```
Apply the same configuration for port 443
```
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 443 -j DNAT --to-destination 192.168.4.1:80
```
Make the setting effective
```
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
```

## Set up captive portal on 192.168.4.1:80 (Flask)
We will use Python and Flask framework to host the captive portal.

If you have not installed the Flask, run
```
sudo apt install python3-flask
```
```
from flask import Flask, request, redirect, render_template

app = Flask(__name__) 

@app.route('/data', methods=['POST'])
def data_post():
    if request.method == 'POST' and 'myData' in request.form:
        myData = request.form['myData']
        return f"Received {myData}"
    return "Error"

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    html = f"""
    <form action="/data" method="post">
    <input type="text" name="myData">
    <input type="submit">
    </form>
    """
    return html
  
if __name__ == "__main__":
    #app.debug = True
    app.run(host="0.0.0.0", port=80) 
```
Save the python code as captiveserver.py and run
```
sudo python3 captiveserver.py
```
Now, the setup is complete. You can test it by finding the hotspot on your device. The captive portal should pop up automatically. The captive portal will look like this.

![demo screenshots](/demo.png)

## Set up after reboot
After completing the previous steps, you should have installed the required packages and made the necessary configurations. Some configurations will not be retained after rebooting. Create a script to includes commands needed to recreate the captive portal. Whenever you have rebooted the board, just run it.
```
nano starthostapd.sh
```
```
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

#redirect traffic
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 80 -j DNAT --to-destination 192.168.4.1:80
sudo iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.4.0/24 --dport 443 -j DNAT --to-destination 192.168.4.1:80
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
```
Give the execute permission.
```
chmod +x starthostapd.sh
```
Run it
```
sudo ./starthostapd.sh
```
You also need to start the Flask app.
```
sudo python3 captiveserver.py
```

## Set up auto-run on startup
Create a script that that runs `./starthostapd.sh` and `python3 captiveserver.py`. We will create a service in systemd to let the OS runs this script on statup.
```
nano captiveportal_start.sh
```
```
#!/bin/bash
echo "Run starthostapd.sh $(date)" >> hostapd_log
./starthostapd.sh >> hostapd_log 2>&1
python3 captiveserver.py
```
Make sure the script can be executed.
```
chmod +x captiveportal_start.sh
```
Create a .service file in the systemd directory
```
sudo nano /lib/systemd/system/CaptivePortal.service
```
Save the file with the following content. Assume the script files are in your home directory. Replace \<username\> with your username. 
```
[Unit]
Description=Captive Portal Service
Requires=sys-subsystem-net-devices-wlan0.device
After=network.target
After=sys-subsystem-net-devices-wlan0.device

[Service]
WorkingDirectory=/home/<username>/
User=root
ExecStart=/home/<username>/captiveportal_start.sh

[Install]
WantedBy=multi-user.target
```
ExecStart set the command we want to run. In this example, it is the captiveportal_start.sh.

Reload the systemctl.
```
sudo systemctl daemon-reload
```
Enable our service so it will run on startup.
```
sudo systemctl enable CaptivePortal.service
```
Reboot the board to verifly the service. The hotspot and captive portal should run automatically after reboot.
```
sudo reboot
```
## References
I made reference to many online courses on Google Search, but I can't recall it. The primary references are the following.
1. https://sribasu.com/programming-tutorials/raspberry-pi-wifi-access-point-captive-portal-python.html
1. https://github.com/TomHumphries/RaspberryPiHotspot
1. https://github.com/AloysAugustin/captive_portal
1. https://wiki.archlinux.org/title/Software_access_point
