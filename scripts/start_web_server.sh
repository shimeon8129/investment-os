#!/bin/bash
TS_IP=$(ip addr show tailscale0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
if [ -z "$TS_IP" ]; then
    echo "[ERROR] tailscale0 interface not found or has no IP" >&2
    exit 1
fi
echo "[INFO] Starting HTTP server on $TS_IP:8080"
exec python3 -m http.server 8080 --bind "$TS_IP"
