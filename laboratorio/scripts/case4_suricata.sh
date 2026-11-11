#!/bin/bash
# case4_suricata.sh: reprocesa las capturas del Caso 4 con las reglas locales.
# Salida en /lab/suricata_cu4 (NO en suricata_final: run_suricata.sh borra esa carpeta entera).
set -eu
BASE=/lab/suricata_cu4
for item in cu4_benign:CU4_01_benign cu4_flash:CU4_02_flash_crowd cu4_synflood:CU4_03_synflood_attack; do
  d="$BASE/${item%%:*}"; p="/captures/${item##*:}.pcap"
  [ -f "$p" ] || { echo "falta $p"; continue; }
  rm -rf "$d"; mkdir -p "$d"
  suricata -c /etc/suricata/suricata.yaml -r "$p" -S /suricata/local.rules -l "$d" --runmode single -k none > "$d/run.log" 2>&1 || true
  echo -n "${item%%:*}: alertas = "; grep -c '"event_type":"alert"' "$d/eve.json" || true
done