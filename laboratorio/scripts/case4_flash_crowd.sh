#!/bin/bash
# case4_flash_crowd.sh: ráfaga LEGÍTIMA (prueba de carga benigna autorizada) contra el servidor del laboratorio.
# Sirve para estudiar los falsos positivos por cambios legítimos de carga.
set -eu
T=172.28.50.20
for r in 1 2 3; do
  for i in $(seq 1 150); do curl -s -o /dev/null --max-time 3 "http://$T/" & done
  wait
  sleep 15
done