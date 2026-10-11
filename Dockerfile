FROM alpine:3.19

RUN apk add --no-cache bash curl unzip ca-certificates tzdata python3 sqlite

ARG XRAY_VERSION=1.8.24
RUN curl -L -o /tmp/xray.zip \
    "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip" \
    && unzip /tmp/xray.zip -d /usr/bin/ \
    && chmod +x /usr/bin/xray \
    && rm /tmp/xray.zip

RUN mkdir -p /etc/xray /data
COPY config.json /etc/xray/config.json
COPY entrypoint.sh /entrypoint.sh
COPY server.py /app/server.py
COPY log-user.sh /app/log-user.sh

RUN chmod +x /entrypoint.sh /app/*.sh /app/*.py

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]