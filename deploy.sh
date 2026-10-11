#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

clear
echo -e "${CYAN}${BOLD}"
echo "  ██╗  ██╗  █████╗  ███████╗ ██╗ ██████╗ "
echo "  ██║  ██║ ██╔══██╗ ██╔════╝ ██║ ██╔══██╗"
echo "  ███████║ ███████║ ███████╗ ██║ ██████╔╝"
echo "  ██╔══██║ ██╔══██║ ╚════██║ ██║ ██╔══██╗"
echo "  ██║  ██║ ██║  ██║ ███████║ ██║ ██████╔╝"
echo "  ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚══════╝ ╚═╝ ╚═════╝ "
echo -e "${RESET}"
echo -e "${GREEN} AUTO DEPLOY STARTED${RESET}"
echo ""

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
  echo -e "${RED}[!] No project selected.${RESET}"
  read -p "Enter your project ID: " PROJECT_ID
  gcloud config set project "$PROJECT_ID"
fi

echo -e "${GREEN}[✓] Project: $PROJECT_ID${RESET}"

echo ""
echo -e "${CYAN}API VERIFICATION${RESET}"
echo "--------------------------------"

enable_api() {
  API=$1
  echo -e "${YELLOW}[*] Enabling $API ...${RESET}"
  gcloud services enable "$API" --project="$PROJECT_ID" >/dev/null 2>&1 || true
  echo -e "${GREEN}[✓] $API enabled/requested${RESET}"
}

enable_api run.googleapis.com
enable_api cloudbuild.googleapis.com
enable_api artifactregistry.googleapis.com
enable_api containerregistry.googleapis.com
enable_api compute.googleapis.com

echo ""
echo -e "${CYAN}REGION SELECTION${RESET}"
echo "--------------------------------"

if [[ "$PROJECT_ID" == qwiklabs-* ]]; then
  REGION="us-central1"
  echo -e "${GREEN}[✓] Qwiklabs environment detected.${RESET}"
  echo -e "${GREEN}[✓] Region locked to: $REGION${RESET}"
else
  read -p "Enter region [default: us-central1]: " REGION
  REGION=${REGION:-us-central1}
fi

echo ""
read -p "Enter service name [default: hasib-vmess]: " SERVICE_NAME
SERVICE_NAME=${SERVICE_NAME:-hasib-vmess}

echo -e "${GREEN}[✓] Service name: $SERVICE_NAME${RESET}"

echo ""
echo -e "${CYAN}CPU AND MEMORY SELECTION${RESET}"
echo "--------------------------------"
echo "[1] 1 vCPU, 1Gi RAM"
echo "[2] 1 vCPU, 2Gi RAM"
echo "[3] 2 vCPU, 2Gi RAM"
echo "[4] 2 vCPU, 4Gi RAM"
echo "[5] 4 vCPU, 8Gi RAM"
echo "[6] 4 vCPU, 16Gi RAM"
read -p "Select configuration [1-6] [default: 4]: " CHOICE
CHOICE=${CHOICE:-4}

case $CHOICE in
  1) CPU=1; MEMORY="1Gi" ;;
  2) CPU=1; MEMORY="2Gi" ;;
  3) CPU=2; MEMORY="2Gi" ;;
  4) CPU=2; MEMORY="4Gi" ;;
  5) CPU=4; MEMORY="8Gi" ;;
  6) CPU=4; MEMORY="16Gi" ;;
  *) CPU=2; MEMORY="4Gi" ;;
esac

echo -e "${GREEN}[✓] CPU: $CPU, Memory: $MEMORY${RESET}"

echo ""
echo -e "${CYAN}BUILDING IMAGE${RESET}"
echo "--------------------------------"

IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

gcloud builds submit --tag "$IMAGE" --project="$PROJECT_ID" .

echo ""
echo -e "${CYAN}DEPLOYING TO CLOUD RUN${RESET}"
echo "--------------------------------"

gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --cpu "$CPU" \
  --memory "$MEMORY" \
  --timeout 3600 \
  --min-instances 0 \
  --max-instances 1 \
  --project "$PROJECT_ID"

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format='value(status.url)')

HOST=$(echo "$SERVICE_URL" | sed 's|https://||')

UUID="HASIBHOSSEN"
WS_PATH="/@bouchor"
ENCODED_PATH="%40bouchor"
SNI="firebase-settings.crashlytics.com"

VMESS_JSON=$(cat <<EOF
{"v":"2","ps":"${SERVICE_NAME}","add":"${HOST}","port":"443","id":"${UUID}","aid":"0","scy":"auto","net":"ws","type":"none","host":"${HOST}","path":"${ENCODED_PATH}","tls":"tls","sni":"${SNI}"}
EOF
)
VMESS_LINK="vmess://$(echo -n "$VMESS_JSON" | base64 -w0)"

echo ""
echo -e "${GREEN}${BOLD}DEPLOYMENT SUCCESSFUL${RESET}"
echo "================================"
echo "Service:   $SERVICE_NAME"
echo "Address:   www.gstatic.com"
echo "SNI:       $SNI"
echo "Host:      $HOST"
echo "Port:      443"
echo "UUID:      $UUID"
echo "AlterID:   0"
echo "WS Path:   $WS_PATH"
echo "Transport: WebSocket (ws)"
echo "Security:  TLS"
echo "Region:    $REGION"
echo "CPU:       $CPU"
echo "Memory:    $MEMORY"
echo "Timeout:   3600s"
echo "================================"
echo ""
echo "Import URI:"
echo "$VMESS_LINK"
echo ""

echo "$VMESS_LINK" > /tmp/vmess-url.txt
echo -e "${GREEN}[✓] URI saved to: /tmp/vmess-url.txt${RESET}"

echo ""
echo -e "${CYAN}OUTPUT OPTIONS${RESET}"
echo "--------------------------------"
echo "[1] Show VMess URI"
echo "[2] Start background monitor"
echo "[3] Both"
echo "[4] Exit"
read -p "Select option [1-4]: " OPTION

if [ "$OPTION" = "1" ]; then
  cat /tmp/vmess-url.txt
elif [ "$OPTION" = "2" ]; then
  chmod +x network-monitor.sh 2>/dev/null || true
  nohup ./network-monitor.sh "$SERVICE_NAME" "$REGION" >/tmp/network-monitor.log 2>&1 &
  echo -e "${GREEN}[✓] Monitor started${RESET}"
elif [ "$OPTION" = "3" ]; then
  cat /tmp/vmess-url.txt
  chmod +x network-monitor.sh 2>/dev/null || true
  nohup ./network-monitor.sh "$SERVICE_NAME" "$REGION" >/tmp/network-monitor.log 2>&1 &
  echo -e "${GREEN}[✓] Monitor started${RESET}"
else
  echo "Exit."
fi

echo ""
echo -e "${GREEN}${BOLD}DEPLOYMENT COMPLETE${RESET}"