#!/usr/bin/env python3
"""caso4_diagnose_alerts.py - desglosa las alertas de uno o varios eve.json por (sid, firma).

Uso:
    python caso4_diagnose_alerts.py cu4_benign/eve.json cu4_flash/eve.json cu4_synflood/eve.json

Sirve para saber si las alertas de un PCAP del Caso 4 vienen de TU regla (sid 1004001) o de
reglas ya existentes de otros casos (CU7/CU8/CU10), antes de concluir que el umbral está mal.
"""
import argparse
import collections
import json

MI_SID = 1004001  # ajusta si tu regla quedó con otro sid


def count_file(path):
    c = collections.Counter()
    total = 0
    for ln in open(path, encoding="utf-8", errors="replace"):
        try:
            j = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if j.get("event_type") != "alert":
            continue
        a = j["alert"]
        c[(a["signature_id"], a["signature"])] += 1
        total += 1
    return c, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="rutas a eve.json, una por PCAP")
    a = ap.parse_args()
    for f in a.files:
        c, total = count_file(f)
        print(f"\n== {f} ==  (total: {total} alertas)")
        if not c:
            print("  (sin alertas)")
            continue
        for (sid, msg), n in c.most_common():
            marca = "  <- TU REGLA" if sid == MI_SID else ""
            print(f"  sid {sid:>10}  {n:>5} alertas  {msg}{marca}")
        mias = sum(n for (sid, _msg), n in c.items() if sid == MI_SID)
        otras = total - mias
        print(f"  -> de tu regla (sid {MI_SID}): {mias}   |   de otras reglas: {otras}")


if __name__ == "__main__":
    main()
