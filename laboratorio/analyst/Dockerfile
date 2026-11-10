FROM alpine:3.20

# Herramientas de captura, escaneo, análisis y validación TLS.
RUN apk add --no-cache \
    bash \
    nmap \
    nmap-scripts \
    tcpdump \
    tshark \
    python3 \
    py3-pip \
    openssl \
    bind-tools \
    iputils \
    curl \
    jq \
    suricata \
    tzdata

# Scapy para generación controlada de tráfico ICMP sintético y
# slixmpp para una sesión XMPP real de laboratorio.
RUN pip install --no-cache-dir --break-system-packages scapy==2.6.1 slixmpp==1.8.5

WORKDIR /lab
CMD ["sleep", "infinity"]
