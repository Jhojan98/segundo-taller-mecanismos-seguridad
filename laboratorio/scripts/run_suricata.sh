#!/bin/sh
# Ejecuta las reglas locales contra las PCAP y resume las alertas.
set -eu

BASE=/lab/suricata_final
rm -rf "$BASE"
for d in cu7_base cu7_sweep cu7_tunnel cu8_syn cu10_tls12_insecure cu10_tls12_secure; do
    mkdir -p "$BASE/$d"
done

run() {
    d=$1
    p=$2
    suricata -c /etc/suricata/suricata.yaml -r "$p" -S /suricata/local.rules \
        -l "$BASE/$d" --runmode single -k none > "$BASE/$d/run.log" 2>&1 || true
}

run cu7_base /captures/CU7_01_baseline_icmp.pcap
run cu7_sweep /captures/CU7_02_icmp_sweep.pcap
run cu7_tunnel /captures/CU7_03_icmp_tunnel.pcap
run cu8_syn /captures/CU8_01_syn_scan.pcap
run cu10_tls12_insecure /captures/CU10_07_https_tls12_insecure.pcap
run cu10_tls12_secure /captures/CU10_08_https_tls12_secure.pcap

echo "=== resumen de alertas ==="
python3 - <<'PY'
import glob
import json
import os
from collections import Counter

for d in sorted(glob.glob("/lab/suricata_final/*")):
    name = os.path.basename(d)
    alerts = []
    try:
        with open(os.path.join(d, "eve.json"), errors="replace") as fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("event_type") == "alert":
                    alerts.append(e["alert"]["signature"])
    except FileNotFoundError:
        continue
    print(f"{name}: {dict(Counter(alerts)) if alerts else 'sin alertas'}")
PY
