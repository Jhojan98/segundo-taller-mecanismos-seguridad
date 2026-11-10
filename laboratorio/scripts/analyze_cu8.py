#!/usr/bin/env python3
"""Análisis cuantitativo del Caso 8 (escaneo de puertos)."""
import csv
import json
import subprocess
from collections import Counter


def fields(path, display_filter, names):
    cmd = ["tshark", "-r", path, "-Y", display_filter, "-T", "fields"]
    for n in names:
        cmd += ["-e", n]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < len(names):
            parts += [""] * (len(names) - len(parts))
        rows.append(dict(zip(names, parts)))
    return rows


TCP_FIELDS = ["frame.number", "frame.time_relative", "ip.src", "ip.dst", "tcp.srcport",
              "tcp.dstport", "tcp.flags", "tcp.flags.syn", "tcp.flags.ack",
              "tcp.flags.reset", "frame.len", "tcp.len"]
UDP_FIELDS = ["frame.number", "frame.time_relative", "ip.src", "ip.dst", "udp.srcport",
              "udp.dstport", "icmp.type", "icmp.code", "frame.len"]


def analyze_syn():
    path = "/captures/CU8_01_syn_scan.pcap"
    rows = fields(path, "tcp", TCP_FIELDS)
    scanner, victim = "172.28.50.10", "172.28.50.20"
    syn, synack, rst = 0, 0, 0
    dst_ports = set()
    open_ports = set()
    times = []
    for r in rows:
        times.append(float(r["frame.time_relative"]))
        if r["ip.src"] == scanner and r["tcp.flags.syn"] == "True" and r["tcp.flags.ack"] == "False":
            syn += 1
            dst_ports.add(int(r["tcp.dstport"]))
        if r["ip.src"] == victim and r["tcp.flags.syn"] == "True" and r["tcp.flags.ack"] == "True":
            synack += 1
            open_ports.add(int(r["tcp.srcport"]))
        if r["ip.src"] == victim and r["tcp.flags.reset"] == "True":
            rst += 1
    duration = max(times) - min(times) if times else 0
    return {
        "archivo": "CU8_01_syn_scan.pcap",
        "paquetes_tcp": len(rows),
        "syn_enviados": syn,
        "synack_recibidos": synack,
        "rst_recibidos": rst,
        "puertos_destino_unicos": len(dst_ports),
        "puertos_abiertos": sorted(open_ports),
        "duracion_s": round(duration, 3),
        "paquetes_por_segundo": round(len(rows) / duration, 1) if duration else 0,
    }, rows


def analyze_service():
    path = "/captures/CU8_02_service_scan.pcap"
    rows = fields(path, "tcp", TCP_FIELDS)
    ports = set()
    total_bytes = 0
    for r in rows:
        if r["ip.src"] == "172.28.50.10":
            ports.add(int(r["tcp.dstport"]))
        total_bytes += int(r["frame.len"] or 0)
    return {
        "archivo": "CU8_02_service_scan.pcap",
        "paquetes_tcp": len(rows),
        "puertos_destino_unicos": len(ports),
        "bytes_totales": total_bytes,
        "puertos": sorted(ports),
    }


def analyze_udp():
    path = "/captures/CU8_03_udp_scan.pcap"
    rows = fields(path, "udp or icmp", UDP_FIELDS)
    udp_packets = 0
    unreachable = 0
    ports = set()
    for r in rows:
        if r["udp.dstport"]:
            udp_packets += 1
            ports.add(int(r["udp.dstport"]))
        if r["icmp.type"] == "3" and r["icmp.code"] == "3":
            unreachable += 1
    return {
        "archivo": "CU8_03_udp_scan.pcap",
        "paquetes_udp": udp_packets,
        "icmp_port_unreachable": unreachable,
        "puertos_destino_unicos": len(ports),
        "puertos": sorted(ports),
    }


def main():
    syn, rows = analyze_syn()
    service = analyze_service()
    udp = analyze_udp()
    summary = [syn, service, udp]
    with open("/lab/cu8_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    with open("/lab/cu8_syn_packets.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
