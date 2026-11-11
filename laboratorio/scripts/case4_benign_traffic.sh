#!/bin/bash
# case4_benign_traffic.sh <segundos>: línea base BENIGNA (HTTP con ritmo variable) hacia el servidor del laboratorio.
set -eu
DUR=${1:-900}
T=172.28.50.20
END=$(( $(date +%s) + DUR ))
while [ "$(date +%s)" -lt "$END" ]; do
  N=$(( RANDOM % 8 + 1 ))
  for i in $(seq 1 "$N"); do curl -s -o /dev/null --max-time 3 "http://$T/" & done
  wait
  sleep "0.$(( RANDOM % 9 + 1 ))"
done