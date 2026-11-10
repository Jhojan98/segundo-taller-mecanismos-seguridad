#!/bin/sh
# Caso 7: línea base ICMP, barrido de hosts y payloads atípicos (túnel simulado).
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

echo "[CU7] 1/3 línea base de ping legítimo"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU7_01_baseline_icmp.pcap" 'icmp' >/dev/null 2>&1 &
PID=$!
sleep 1
ping -c 4 -W 1 "$VICTIM" > "$OUT/case7_ping_baseline.txt" 2>&1 || true
sleep 1
stop_cap

echo "[CU7] 2/3 barrido ICMP a 172.28.50.1-40"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU7_02_icmp_sweep.pcap" 'icmp' >/dev/null 2>&1 &
PID=$!
sleep 1
python3 - <<'PY' > "$OUT/case7_sweep.txt" 2>&1
from scapy.all import Ether, IP, ICMP, sendp

# La trama se envía a la MAC de difusión para no depender del ARP de
# hosts inexistentes; el host destino responde de forma normal.
for i in range(1, 41):
    sendp(Ether(dst="ff:ff:ff:ff:ff:ff") / IP(dst=f"172.28.50.{i}") / ICMP(),
          iface="eth0", verbose=False)
print("40 echo requests enviados a 172.28.50.1-40")
PY
sleep 2
stop_cap

echo "[CU7] 3/3 payloads atípicos: túnel ICMP didáctico"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU7_03_icmp_tunnel.pcap" 'icmp' >/dev/null 2>&1 &
PID=$!
sleep 1
python3 - <<'PY' > "$OUT/case7_tunnel.txt" 2>&1
import base64
import random
import time

from scapy.all import IP, ICMP, Raw, send

# Contenido sintético y aleatorio (semilla fija): NO son datos reales.
rng = random.Random(2026)
for n in range(15):
    payload = base64.b64encode(bytes(rng.randrange(256) for _ in range(675)))
    send(IP(dst="172.28.50.20") / ICMP(type=8) / Raw(load=payload), verbose=False)
    print(f"echo {n + 1:02d}: payload={len(payload)} bytes")
    time.sleep(0.6)
PY
sleep 2
stop_cap

echo "[CU7] capturas listas:"
ls -l "$CAP"/CU7_*.pcap
