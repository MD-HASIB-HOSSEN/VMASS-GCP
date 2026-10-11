#!/bin/sh

PORT=${PORT:-8080}

sed -i "s/\"port\": 8080/\"port\": $PORT/g" /etc/xray/config.json

echo "Starting Xray VMess WS on Dynamic Port: $PORT"
/usr/bin/xray run -c /etc/xray/config.json