#!/bin/sh
# Caso 8: escaneo de puertos y fingerprinting de servicios sobre la víctima.
set -eu

VICTIM=172.28.50.20
CAP=/captures
OUT=/lab
IFACE=eth0
mkdir -p "$CAP" "$OUT"

stop_cap() {
    [ -n "${PID:-}" ] && kill "$PID" 2>/dev/null || true
    [ -n "${PID:-}" ] && wait "$PID" 2>/dev/null || true
    PID=
}
trap stop_cap EXIT

echo "[CU8] 1/3 escaneo TCP SYN de puertos 1-1024"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU8_01_syn_scan.pcap" "host $VICTIM and tcp" >/dev/null 2>&1 &
PID=$!
sleep 1
nmap -sS -Pn -n -p 1-1024 --min-rate 1500 --max-retries 1 "$VICTIM" \
    -oN "$OUT/case8_syn_scan.txt" > /dev/null 2>&1 || true
sleep 2
stop_cap

echo "[CU8] 2/3 fingerprinting de servicios abiertos"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU8_02_service_scan.pcap" "host $VICTIM and tcp" >/dev/null 2>&1 &
PID=$!
sleep 1
nmap -sT -sV -Pn -n -p 21,22,23,80,4444,8080 --version-all "$VICTIM" \
    -oN "$OUT/case8_service_scan.txt" > /dev/null 2>&1 || true
sleep 2
stop_cap

echo "[CU8] 3/3 escaneo UDP de servicios comunes"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU8_03_udp_scan.pcap" "host $VICTIM and (udp or icmp)" >/dev/null 2>&1 &
PID=$!
sleep 1
nmap -sU -Pn -n -p 53,123,161,500,5353 --max-retries 1 --host-timeout 40s "$VICTIM" \
    -oN "$OUT/case8_udp_scan.txt" > /dev/null 2>&1 || true
sleep 2
stop_cap

echo "[CU8] capturas listas:"
ls -l "$CAP"/CU8_*.pcap
