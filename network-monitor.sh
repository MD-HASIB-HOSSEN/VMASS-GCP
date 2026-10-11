#!/bin/bash

SERVICE_NAME="${1:-hasib-vmess}"
REGION="${2:-us-central1}"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)' 2>/dev/null)

if [ -z "$SERVICE_URL" ]; then
    echo "Error: Could not find service '$SERVICE_NAME' in region '$REGION'."
    exit 1
fi

LOG_DIR="$HOME/network-logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/http-status-$(date +%Y%m%d).log"
INTERVAL=10

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}${CYAN}=========================================${RESET}"
echo -e "${BOLD}${CYAN}   VMESS HTTP MONITOR STARTED           ${RESET}"
echo -e "${BOLD}${CYAN}=========================================${RESET}"
echo -e "${CYAN}Target:${RESET} $SERVICE_URL"
echo -e "Press Ctrl+C to stop.\n"

trap 'echo -e "\n${BOLD}${YELLOW}Monitoring stopped.${RESET}"; exit 0' INT

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    RESULT=$(curl -o /dev/null -s -w "%{time_total}|%{http_code}" --max-time 5 "$SERVICE_URL")

    if [ -n "$RESULT" ]; then
        TIME=$(echo "$RESULT" | cut -d'|' -f1)
        CODE=$(echo "$RESULT" | cut -d'|' -f2)
        TIME_MS=$(echo "$TIME * 1000" | bc 2>/dev/null | cut -d'.' -f1)

        if [ "$CODE" = "200" ] || [ "$CODE" = "400" ]; then
            echo -e "$TIMESTAMP | ${GREEN}UP${RESET}   | HTTP $CODE | ${TIME_MS}ms"
            echo "$TIMESTAMP | UP | HTTP $CODE | ${TIME_MS}ms" >> "$LOG_FILE"
        else
             echo -e "$TIMESTAMP | ${RED}DOWN${RESET} | HTTP $CODE"
        fi
    else
        echo -e "$TIMESTAMP | ${RED}DOWN${RESET} | Timeout"
    fi

    sleep "$INTERVAL"
done