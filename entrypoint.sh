#!/bin/sh
sed -i "s/8080/$PORT/g" /etc/xray/config.json

echo "Starting Xray on Dynamic Port: $PORT"
/usr/bin/xray run -c /etc/xray/config.json