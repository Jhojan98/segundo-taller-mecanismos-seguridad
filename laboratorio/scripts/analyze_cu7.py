#!/usr/bin/env python3
"""Análisis cuantitativo del Caso 7 (ICMP)."""
import csv
import json
import math
import subprocess
from collections import Counter

FILES = {
    "baseline": ("/captures/CU7_01_baseline_icmp.pcap", "Ping de diagnóstico"),
    "sweep": ("/captures/CU7_02_icmp_sweep.pcap", "Barrido ICMP"),
    "tunnel": ("/captures/CU7_03_icmp_tunnel.pcap", "Payload atípico / túnel simulado"),
}
FIELDS = ["frame.number", "frame.time_relative", "ip.src", "ip.dst", "icmp.type",
          "icmp.code", "icmp.seq", "frame.len", "data.len", "data.data"]


def parse_pcap(path):
    cmd = ["tshark", "-r", path, "-Y", "icmp", "-T", "fields"]
    for f in FIELDS:
        cmd += ["-e", f]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < len(FIELDS):
            parts += [""] * (len(FIELDS) - len(parts))
        rows.append(dict(zip(FIELDS, parts)))
    return rows


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def analyze(name, path, label):
    rows = parse_pcap(path)
    packets = []
    req_times = []
    req_lengths = []
    req_entropy = []
    req_printable = []
    req_b64 = []
    req_dst = set()
    types = Counter()
    for r in rows:
        raw = (r["data.data"] or "").replace(":", "").replace(",", "")
        try:
            payload = bytes.fromhex(raw)
        except ValueError:
            payload = b""
        typ = int(r["icmp.type"]) if r["icmp.type"] else -1
        types[typ] += 1
        packet = {
            "frame": int(r["frame.number"]),
            "time": float(r["frame.time_relative"]),
            "src": r["ip.src"],
            "dst": r["ip.dst"],
            "type": typ,
            "code": int(r["icmp.code"]) if r["icmp.code"] else -1,
            "seq": r["icmp.seq"],
            "frame_len": int(r["frame.len"]),
            "payload_len": len(payload),
            "entropy": round(entropy(payload), 3) if payload else 0.0,
        }
        packets.append(packet)
        if typ == 8:
            req_times.append(packet["time"])
            req_lengths.append(len(payload))
            req_entropy.append(packet["entropy"])
            if payload:
                printable = sum(1 for b in payload if 32 <= b < 127) / len(payload)
                b64chars = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
                b64 = sum(1 for b in payload if b in b64chars) / len(payload)
                req_printable.append(printable)
                req_b64.append(b64)
            req_dst.add(packet["dst"])
    intervals = [round(b - a, 3) for a, b in zip(req_times, req_times[1:])]
    unique_req = {(p["dst"], p["seq"]) for p in packets if p["type"] == 8}
    summary = {
        "archivo": path.split("/")[-1],
        "fase": label,
        "paquetes_totales": len(packets),
        "echo_request": types.get(8, 0),
        "echo_request_unicos": len(unique_req),
        "duplicados_echo_request": types.get(8, 0) - len(unique_req),
        "echo_reply": types.get(0, 0),
        "otros_tipos": {str(k): v for k, v in types.items() if k not in (0, 8)},
        "destinos_unicos_echo_request": len(req_dst),
        "longitud_payload_min": min(req_lengths) if req_lengths else 0,
        "longitud_payload_max": max(req_lengths) if req_lengths else 0,
        "longitud_payload_promedio": round(sum(req_lengths) / len(req_lengths), 1) if req_lengths else 0,
        "entropia_promedio_bits_byte": round(sum(req_entropy) / len(req_entropy), 3) if req_entropy else 0,
        "proporcion_imprimible": round(sum(req_printable) / len(req_printable), 3) if req_printable else 0,
        "proporcion_base64": round(sum(req_b64) / len(req_b64), 3) if req_b64 else 0,
        "intervalo_promedio_s": round(sum(intervals) / len(intervals), 3) if intervals else 0,
        "intervalo_min_s": min(intervals) if intervals else 0,
        "intervalo_max_s": max(intervals) if intervals else 0,
    }
    return summary, packets


def main():
    summaries = []
    all_packets = []
    for name, (path, label) in FILES.items():
        summary, packets = analyze(name, path, label)
        summaries.append(summary)
        for p in packets:
            p["fase"] = name
            all_packets.append(p)
    with open("/lab/cu7_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summaries, fh, indent=2, ensure_ascii=False)
    with open("/lab/cu7_packets.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(all_packets[0].keys()))
        writer.writeheader()
        writer.writerows(all_packets)
    print(json.dumps(summaries, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
