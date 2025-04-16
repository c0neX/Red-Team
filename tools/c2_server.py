from flask import Flask, request, jsonify
import datetime

app = Flask(_name_)

# Predefined commands for specific hosts (could be dynamic from DB/file)
commands = {
    "lab-box-1": "whoami",
    "lab-box-2": "ipconfig",
    "ubuntu-test": "uname -a"
}

@app.route('/beacon', methods=['POST'])
def beacon():
    data = request.json
    hostname = data.get("hostname")
    local_ip = data.get("local_ip")
    platform = data.get("platform")

    now = datetime.datetime.now().isoformat()
    print(f"[{now}] Beacon received:")
    print(f"  Hostname: {hostname}")
    print(f"  IP: {local_ip}")
    print(f"  Platform: {platform}")

    command = commands.get(hostname, "")  # Empty string = no command
    return jsonify({"command": command})

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=8080)
