from flask import Flask, request, redirect, render_template
import subprocess

# Some helper functions to interact with the Linux system using command line.
########################################################################################
def getHostname() -> str:
    hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip("\n")
    return hostname

def getWifiNetworks(interface:str = "wlan0") -> list[str]:
    # scan wifi networks
    subprocess.run("sudo wpa_cli -i {interface} scan", shell=True)
    # get results
    scanResults = subprocess.run(f"sudo wpa_cli -i {interface} scan_results | sed '1d' | cut -f 5 | grep .", text=True, shell=True, capture_output = True).stdout.strip("\n")
    if scanResults:
        return scanResults.split('\n')
    return None

def getCurrentNetwork(interface:str = "wlan0") -> str:
    checkConnectedWifi = subprocess.run(f"wpa_cli -i {interface} status | grep -E \"^ssid\" | cut -d\'=\' -f2",text=True, shell=True, capture_output = True).stdout.strip("\n")
    print(checkConnectedWifi)
    if checkConnectedWifi:
        return checkConnectedWifi
    return None

def getCurrentIP(interface:str = "wlan0") -> str:
    ipAddress = subprocess.run(f"wpa_cli -i {interface} status | grep -E \"^ip_address=\" | cut -d\'=\' -f2",text=True, shell=True, capture_output = True).stdout.strip("\n")
    if ipAddress:
        return ipAddress
    return None

def setWifiNetwork(ssid:str, psk:str, interface:str = "wlan0") -> bool:
    # Save ssid and psk to wpa_supplicant.conf
    print(subprocess.run(["sudo", "wpa_cli", "set_network", "1", "ssid", f"\"{ssid}\""], capture_output=True).stdout.decode().strip("\n"))
    print(subprocess.run(["sudo", "wpa_cli", "set_network", "1", "psk", f"\"{psk}\""],  capture_output=True).stdout.decode().strip("\n"))
    print(subprocess.run(["sudo", "wpa_cli", "enable_network", "1"],  capture_output=True).stdout.decode().strip("\n"))
    print(subprocess.run(["sudo", "wpa_cli", "save_config"],  capture_output=True).stdout.decode().strip("\n"))
    print("done")

    # Reconnect to the wifi
    subprocess.Popen(f"sleep 3 && sudo wpa_cli -i {interface} reconfigure", shell=True)
    return True
########################################################################################
# End of helper functions

app = Flask(__name__) 

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/network', methods=['POST'])
def network_post():
    if request.method == 'POST' and 'ssid' in request.form and 'psk' in request.form:
        ssid= request.form['ssid']
        psk = request.form['psk']
        print(ssid)
        print(psk)
        # You may encode the psk so it wounld not be stored as plain text
        # > wpa_passphrase 'ssid' psk | grep -E "^.psk" | cut -d'=' -f2
        setWifiNetwork(ssid, psk)
        return render_template("result.html", result="OK")
    return render_template("result.html", result="Error")

# The list of available networks are loaded by ajax in the captive.html
# This route send back the list of available networks in json
@app.route('/network', methods=['GET'])
def network_get():
    networks = getWifiNetworks()
    if networks != None:
        print(networks)
        return {"ssids":networks}
    return "Error"

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    status = {
        "hostname": getHostname(),
        "connectedWifi" : {
            "ssid":getCurrentNetwork(),
            "ip_address":getCurrentIP()
        }
    }
    return render_template("captive.html", status=status)
  
if __name__ == "__main__":
    #app.debug = True
    app.run(host="0.0.0.0", port=80) 