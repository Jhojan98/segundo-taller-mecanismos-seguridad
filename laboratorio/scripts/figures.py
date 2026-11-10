#!/usr/bin/env python3
"""Genera las figuras de evidencia de los casos 7, 8 y 10.

Lee los TSV/CSV/JSON/texto exportados por los scripts de análisis y produce
PNG listos para incluir en el informe LaTeX. No usa capturas de pantalla:
todas las figuras se reconstruyen a partir de la evidencia exportada.
"""

from __future__ import annotations

import csv
import json
import re
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "laboratorio" / "work"
OUT7 = ROOT / "imagenes" / "Evidencias CU-7"
OUT8 = ROOT / "imagenes" / "Evidencias CU-8"
OUT10 = ROOT / "imagenes" / "Evidencias CU-10"

for d in (OUT7, OUT8, OUT10):
    d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Estilo general
# ----------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "axes.edgecolor": "#5a5a5a",
    "axes.linewidth": 0.8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": 160,
    "savefig.dpi": 160,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.18,
})

INK = "#1f2a36"
MUTED = "#5c6773"
ACCENT = "#1f5f8b"
ALERT = "#b23a2e"
OK = "#2e7d4f"
GRID = "#d9dee4"
PANEL = "#f4f6f8"
MONO = "DejaVu Sans Mono"

PALETTE = {
    "baseline": "#4c78a8",
    "sweep": "#e08a2e",
    "tunnel": "#b23a2e",
}


def clean_title(title: str) -> str:
    """Quita el prefijo 'Figura N.N.'; LaTeX numera las figuras."""
    return re.sub(r"^Figura\s+\d+\.\d+\.\s*", "", title)


def save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"  -> {path.relative_to(ROOT)}")


def header(fig: plt.Figure, title: str, subtitle: str | None = None) -> None:
    h = fig.get_figheight()
    fig.text(0.01, 1 - 0.09 / h, clean_title(title), ha="left", va="top",
             fontsize=11, fontweight="bold", color=INK)
    if subtitle:
        fig.text(0.01, 1 - 0.40 / h, subtitle, ha="left", va="top",
                 fontsize=8.2, color=MUTED)


def terminal(path: Path, title: str, subtitle: str, lines: list[str],
             filename: Path, max_chars: int = 106, fontsize: float = 7.4,
             accent: str = ACCENT) -> None:
    """Dibuja un panel tipo terminal con texto monoespaciado."""
    wrapped: list[str] = []
    for line in lines:
        line = line.replace("\t", "    ")
        if len(line) <= max_chars:
            wrapped.append(line)
        else:
            wrapped.extend(textwrap.wrap(line, max_chars,
                                         subsequent_indent="    ",
                                         break_long_words=True,
                                         break_on_hyphens=False))
    line_h = 0.155
    height = max(2.4, line_h * len(wrapped) + 1.05)
    fig = plt.figure(figsize=(9.6, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    top = 1 - 0.62 / height          # borde inferior de la barra de título
    bottom = 0.34 / height           # encima del pie
    panel_h = top - bottom

    # barra de título
    bar = FancyBboxPatch((0.008, top + 0.06 / height), 0.984, 0.46 / height,
                         boxstyle="round,pad=0.003,rounding_size=0.004",
                         linewidth=0, facecolor=accent, transform=ax.transAxes)
    ax.add_patch(bar)
    ax.text(0.018, top + 0.29 / height, clean_title(title), ha="left", va="center",
            fontsize=8.2, fontweight="bold", color="white")
    ax.text(0.982, top + 0.29 / height, "evidencia de laboratorio", ha="right",
            va="center", fontsize=6.8, color="#e8eef5")

    panel = FancyBboxPatch((0.008, bottom), 0.984, panel_h,
                           boxstyle="round,pad=0.003,rounding_size=0.004",
                           linewidth=0.8, edgecolor="#c6cdd5",
                           facecolor=PANEL, transform=ax.transAxes)
    ax.add_patch(panel)

    y = top - 0.11 / height
    step = line_h / height
    for line in wrapped:
        color = INK
        stripped = line.strip()
        if stripped.startswith(("!", "ERROR", "verify error", "SSL routines")):
            color = ALERT
        elif stripped.startswith(("Verification: OK", "Verify return code: 0",
                                  "SUCCESS", "DONE")):
            color = OK
        ax.text(0.018, y, line, ha="left", va="top", fontsize=fontsize,
                family=MONO, color=color)
        y -= step
    fig.text(0.012, 0.10 / height, subtitle, ha="left", va="bottom",
             fontsize=7.0, color=MUTED, style="italic")
    save(fig, filename)


def table_png(filename: Path, title: str, subtitle: str,
              headers: list[str], rows: list[list[str]],
              col_widths: list[float], fontsize: float = 8.0,
              row_height: float = 0.34) -> None:
    fig_w = 9.4
    fig_h = max(2.2, 0.42 * (len(rows) + 2) + 0.9)
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    header(fig, title, subtitle)

    table = ax.table(cellText=rows, colLabels=headers,
                     colWidths=col_widths, loc="center",
                     cellLoc="left", colLoc="left",
                     bbox=[0.01, 0.04, 0.98, 0.74])
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("#c6cdd5")
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_facecolor("#e7edf3")
            cell.set_text_props(fontweight="bold", color=INK)
        else:
            cell.set_facecolor("white" if r % 2 else "#f7f9fb")
            if c == 0:
                cell.set_text_props(family=MONO)
    save(fig, filename)


# ----------------------------------------------------------------------------
# Utilidades de datos
# ----------------------------------------------------------------------------
def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    heads = text[0].split("\\")
    out = []
    for line in text[1:]:
        parts = line.split("\\")
        out.append(dict(zip(heads, parts)))
    return out


def sha_map() -> dict[str, str]:
    out = {}
    for line in (ROOT / "laboratorio" / "evidencias_sha256.txt").read_text().splitlines():
        if "*" in line:
            h, name = line.split("*", 1)
            out[name.strip()] = h.strip()
    return out


HASHES = sha_map()
SIZES = {}
for p in (ROOT / "laboratorio" / "captures").glob("*.pcap"):
    SIZES[p.name] = p.stat().st_size


def hash_rows(names: list[str]) -> list[list[str]]:
    rows = []
    for name in names:
        h = HASHES[name]
        size = SIZES.get(name, 0)
        rows.append([name, f"{size:,} B".replace(",", "."), h[:32] + "\n" + h[32:]])
    return rows


# ----------------------------------------------------------------------------
# Topología
# ----------------------------------------------------------------------------
def topology(filename: Path, title: str, subtitle: str, focus: str = "all") -> None:
    fig, ax = plt.subplots(figsize=(9.4, 4.7))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 58)
    ax.axis("off")
    header(fig, title, subtitle)

    zone = FancyBboxPatch((3, 4), 94, 44,
                          boxstyle="round,pad=0.6,rounding_size=2",
                          linewidth=1.3, linestyle="--", edgecolor="#8a95a1",
                          facecolor="#f7f9fb")
    ax.add_patch(zone)
    ax.text(50, 50.4, "Red de laboratorio aislada 172.28.50.0/24  ·  docker network internal: true",
            ha="center", va="center", fontsize=8.6, color=MUTED, fontweight="bold")

    def box(x, y, w, h, title_txt, addr, lines, color):
        p = FancyBboxPatch((x, y), w, h,
                           boxstyle="round,pad=0.35,rounding_size=1.2",
                           linewidth=1.4, edgecolor=color, facecolor="white")
        ax.add_patch(p)
        ax.text(x + w / 2, y + h - 2.1, title_txt, ha="center", va="center",
                fontsize=9.2, fontweight="bold", color=color)
        ax.text(x + w / 2, y + h - 4.6, addr, ha="center", va="center",
                fontsize=8.4, family=MONO, color=INK)
        for i, ln in enumerate(lines):
            ax.text(x + w / 2, y + h - 7.6 - i * 2.5, ln, ha="center", va="center",
                    fontsize=7.4, color=MUTED)

    if focus == "all":
        box(8, 24, 24, 17, "Analista", "172.28.50.10",
            ["tcpdump · tshark", "nmap · suricata", "scripts Python"], ACCENT)
        box(39, 24, 24, 17, "Víctima", "172.28.50.20",
            ["FTP 21 · SSH 22", "Telnet 23 · HTTP 80", "4444 · 8080"], ALERT)
        box(70, 30, 24, 15, "XMPP inseguro", "172.28.50.30",
            ["Prosody 5222", "cert. vencido CN=localhost"], "#8a5a00")
        box(70, 9, 24, 15, "XMPP endurecido", "172.28.50.31",
            ["Prosody 5222", "CA propia · CN=lab.local"], OK)

        ax.annotate("", xy=(39, 34), xytext=(32, 34),
                    arrowprops=dict(arrowstyle="-|>", color=ALERT, lw=1.6))
        ax.text(35.5, 36.4, "ICMP / SYN / UDP", ha="center", fontsize=7.2, color=ALERT)
        ax.annotate("", xy=(70, 37.5), xytext=(63, 37.5),
                    arrowprops=dict(arrowstyle="-|>", color="#8a5a00", lw=1.6))
        ax.text(64.3, 40.1, "XMPP / HTTPS", ha="left", fontsize=7.2, color="#8a5a00")
        ax.annotate("", xy=(70, 16.5), xytext=(63, 16.5),
                    arrowprops=dict(arrowstyle="-|>", color=OK, lw=1.6))
        ax.text(64.3, 19.1, "XMPP / HTTPS", ha="left", fontsize=7.2, color=OK)
    else:
        box(5, 24, 27, 18, "Cliente / analista", "172.28.50.10",
            ["slixmpp · OpenSSL", "tshark · suricata"], ACCENT)
        box(40, 30, 26, 15, "XMPP inseguro", "172.28.50.30",
            ["cert. vencido 2022", "auth en claro · MAM"], "#8a5a00")
        box(40, 9, 26, 15, "XMPP endurecido", "172.28.50.31",
            ["CA propia · TLS 1.2+", "sin registro abierto"], OK)
        box(74, 19.5, 21, 15, "Atacante MITM", "172.28.50.10:4443",
            ["cert. autofirmado", "intercepta TLS"], ALERT)

        ax.annotate("", xy=(40, 37.5), xytext=(32, 37.5),
                    arrowprops=dict(arrowstyle="<|-|>", color="#8a5a00", lw=1.6))
        ax.text(36, 39.9, "STARTTLS", ha="center", fontsize=7.2, color="#8a5a00")
        ax.annotate("", xy=(40, 16.5), xytext=(32, 16.5),
                    arrowprops=dict(arrowstyle="<|-|>", color=OK, lw=1.6))
        ax.text(36, 18.9, "STARTTLS", ha="center", fontsize=7.2, color=OK)
        ax.text(84.5, 17.0, "intercepta el canal del cliente",
                ha="center", va="top", fontsize=6.8, color=ALERT)
    save(fig, filename)


# ----------------------------------------------------------------------------
# CASO 7
# ----------------------------------------------------------------------------
def case7() -> None:
    print("Caso 7 - ICMP")
    summary = read_json(WORK / "cu7_summary.json")
    by_file = {s["archivo"]: s for s in summary}

    topology(OUT7 / "01_topologia_lab.png",
             "Figura 7.1. Topología del laboratorio aislado",
             "Roles, direcciones y servicios usados en las capturas del Caso 7.")

    table_png(OUT7 / "02_hashes_sha256.png",
              "Figura 7.2. Integridad de las capturas del Caso 7",
              "Huellas SHA-256 calculadas antes del análisis (sha256sum sobre las copias originales).",
              ["Archivo", "Tamaño", "SHA-256"],
              hash_rows(["CU7_01_baseline_icmp.pcap",
                         "CU7_02_icmp_sweep.pcap",
                         "CU7_03_icmp_tunnel.pcap"]),
              [0.24, 0.11, 0.65], fontsize=7.4)

    # --- lista de paquetes del barrido ---
    sweep = read_tsv(WORK / "cu7_sweep_packets.tsv")
    rows = []
    for p in sweep[:26]:
        info = p.get("_ws.col.info", "")
        info = info.replace("Echo (ping) request", "Echo request").replace(
            "Echo (ping) reply", "Echo reply")
        rows.append([p["frame.number"], f'{float(p["frame.time_relative"]):.6f}',
                     p["ip.src"], p["ip.dst"], p["icmp.type"],
                     p["frame.len"], info])
    terminal(OUT7 / "03_paquetes_barrido.png",
             "Figura 7.3. Lista de paquetes del barrido ICMP (extracto)",
             "Captura CU7_02_icmp_sweep.pcap; se muestran las primeras 26 tramas de 84. Cada destino aparece duplicado por la réplica del puente virtual.",
             ["frame  time_rel     origen          destino         tipo  len  información"] +
             ["- " * 52] + [f'{r[0]:>5}  {r[1]:<11}  {r[2]:<15} {r[3]:<15} {r[4]:>4}  {r[5]:>4}  {r[6][:44]}' for r in rows],
             OUT7 / "03_paquetes_barrido.png", max_chars=112, fontsize=7.0)

    # --- lista de paquetes del túnel ---
    tunnel = read_tsv(WORK / "cu7_tunnel_packets.tsv")
    rows = []
    for p in tunnel[:12]:
        data = p.get("data.data", "")
        short = data[:56] + "…" if len(data) > 56 else data
        rows.append([p["frame.number"], f'{float(p["frame.time_relative"]):.6f}',
                     p["ip.src"], p["ip.dst"], p["icmp.type"],
                     p["frame.len"], short])
    terminal(OUT7 / "04_paquetes_tunel.png",
             "Figura 7.4. Lista de paquetes del túnel ICMP simulado (extracto)",
             "Captura CU7_03_icmp_tunnel.pcap; payload de 900 bytes codificado en base64 (el volcado se truncó a 56 caracteres).",
             ["frame  time_rel     origen          destino         tipo  len  payload (hex, truncado)"] +
             ["- " * 52] + [f'{r[0]:>5}  {r[1]:<11}  {r[2]:<15} {r[3]:<15} {r[4]:>4}  {r[5]:>4}  {r[6]}' for r in rows],
             OUT7 / "04_paquetes_tunel.png", max_chars=128, fontsize=6.5)

    # --- línea de tiempo ---
    packets = list(csv.DictReader((WORK / "cu7_packets.csv").open(encoding="utf-8")))
    fig, axes = plt.subplots(1, 3, figsize=(9.4, 3.4), sharey=False)
    meta = [
        ("baseline", "Línea base", "4 echo requests · 0,88 s"),
        ("sweep", "Barrido", "40 destinos · 0,016 s"),
        ("tunnel", "Túnel", "15 requests · 0,62 s"),
    ]
    for ax, (phase, label, note) in zip(axes, meta):
        sub = [p for p in packets if p["fase"] == phase and p["type"] == "8"]
        times = sorted({round(float(p["time"]), 6) for p in sub})
        ax.eventplot(times, colors=PALETTE[phase], lineoffsets=0, linewidths=1.6)
        ax.set_title(label, color=PALETTE[phase])
        ax.set_xlabel("tiempo relativo (s)")
        ax.set_yticks([])
        ax.set_ylim(-1, 1)
        ax.grid(axis="x", color=GRID, lw=0.7)
        ax.set_axisbelow(True)
        ax.text(0.02, 0.86, note, transform=ax.transAxes,
                fontsize=7.4, color=MUTED)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
    header(fig, "Figura 7.5. Distribución temporal de los echo request",
           "Cada marca corresponde a un paquete ICMP tipo 8. El barrido concentra 40 destinos en menos de 0,7 s.")
    fig.subplots_adjust(left=0.06, right=0.99, top=0.75, bottom=0.19, wspace=0.22)
    save(fig, OUT7 / "05_linea_tiempo.png")

    # --- longitud y entropía ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.4))
    labels = ["Línea base", "Barrido", "Túnel"]
    keys = ["CU7_01_baseline_icmp.pcap", "CU7_02_icmp_sweep.pcap",
            "CU7_03_icmp_tunnel.pcap"]
    lens = [by_file[k]["longitud_payload_promedio"] for k in keys]
    ents = [by_file[k]["entropia_promedio_bits_byte"] for k in keys]
    colors = [PALETTE["baseline"], PALETTE["sweep"], PALETTE["tunnel"]]
    bars = ax1.bar(labels, lens, color=colors, width=0.55)
    ax1.set_ylabel("payload promedio (bytes)")
    ax1.set_title("Longitud del payload")
    ax1.grid(axis="y", color=GRID, lw=0.7)
    ax1.set_axisbelow(True)
    for b, v in zip(bars, lens):
        ax1.text(b.get_x() + b.get_width() / 2, v + 18, f"{v:.0f} B",
                 ha="center", fontsize=8, fontweight="bold", color=INK)
    ax1.set_ylim(0, max(lens) * 1.28)

    bars = ax2.bar(labels, ents, color=colors, width=0.55)
    ax2.set_ylabel("entropía (bits/byte)")
    ax2.set_title("Entropía del payload")
    ax2.set_ylim(0, 8)
    ax2.axhline(7.2, color=ALERT, lw=1, ls="--")
    ax2.text(2.45, 6.55, "umbral 7,2 bits/byte", ha="right", fontsize=6.6,
             color=ALERT)
    ax2.grid(axis="y", color=GRID, lw=0.7)
    ax2.set_axisbelow(True)
    for b, v in zip(bars, ents):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.12, f"{v:.2f}",
                 ha="center", fontsize=8, fontweight="bold", color=INK)
    header(fig, "Figura 7.6. Longitud y entropía del payload ICMP",
           "El barrido usa payload vacío; el túnel usa 900 B con alta proporción de caracteres imprimibles.")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.74, bottom=0.19, wspace=0.30)
    save(fig, OUT7 / "06_longitud_entropia.png")

    # --- alertas Suricata ---
    fast = ((WORK / "suricata" / "cu7_sweep" / "fast.log").read_text(encoding="utf-8").splitlines()
            + (WORK / "suricata" / "cu7_tunnel" / "fast.log").read_text(encoding="utf-8").splitlines())
    lines = []
    for ln in fast:
        parts = ln.split()
        ts = parts[0].split("-", 1)[-1]
        parts2 = ln.split("[**]")
        msg = parts2[1].strip() if len(parts2) >= 3 else ln
        if msg.startswith("["):
            msg = msg.split("]", 1)[-1].strip()
        rest = ln.rsplit("{ICMP}", 1)[-1].strip()
        lines.append(f"{ts}  {msg[:52]:<52}  {rest}")
    terminal(OUT7 / "07_suricata_alertas.png",
             "Figura 7.7. Alertas de Suricata 7.0.7 para el Caso 7",
             "Salida de fast.log al reprocesar las capturas: 4 alertas de barrido (SID 1007002) y 5 de payload grande (SID 1007001); la línea base no genera alertas.",
             ["timestamp (UTC)          mensaje                                               flujo"] +
             ["- " * 52] + lines,
             OUT7 / "07_suricata_alertas.png", max_chars=120, fontsize=7.0, accent=ALERT)


# ----------------------------------------------------------------------------
# CASO 8
# ----------------------------------------------------------------------------
def case8() -> None:
    print("Caso 8 - Escaneo de puertos")
    summary = read_json(WORK / "cu8_summary.json")

    table_png(OUT8 / "01_hashes_sha256.png",
              "Figura 8.1. Integridad de las capturas del Caso 8",
              "Huellas SHA-256 calculadas antes del análisis (sha256sum sobre las copias originales).",
              ["Archivo", "Tamaño", "SHA-256"],
              hash_rows(["CU8_01_syn_scan.pcap",
                         "CU8_02_service_scan.pcap",
                         "CU8_03_udp_scan.pcap"]),
              [0.24, 0.11, 0.65], fontsize=7.4)

    syn_txt = (WORK / "case8_syn_scan.txt").read_text(encoding="utf-8").splitlines()
    terminal(OUT8 / "02_nmap_syn.png",
             "Figura 8.2. Resultado del escaneo SYN (nmap -sS)",
             "Nmap 7.95 sobre 172.28.50.20, puertos 1-1024, --min-rate 1500. Cuatro puertos abiertos y 1020 cerrados.",
             syn_txt, OUT8 / "02_nmap_syn.png", max_chars=118, fontsize=7.0)

    svc = (WORK / "case8_service_scan.txt").read_text(encoding="utf-8").splitlines()
    keep = []
    for ln in svc:
        if ln.startswith(("==============", "SF:", "SF-")):
            continue
        keep.append(ln)
    terminal(OUT8 / "03_nmap_servicios.png",
             "Figura 8.3. Fingerprinting de servicios (nmap -sT -sV)",
             "Versiones detectadas en los seis puertos abiertos. Los fingerprints extensos se omitieron para mantener la legibilidad.",
             keep, OUT8 / "03_nmap_servicios.png", max_chars=118, fontsize=7.0)

    # --- puertos acumulados + tasa ---
    rows = list(csv.DictReader((WORK / "cu8_syn_packets.csv").open(encoding="utf-8")))
    syn = [r for r in rows if r["tcp.flags.syn"] == "True" and r["tcp.flags.ack"] == "False"]
    times = np.array([float(r["frame.time_relative"]) for r in syn])
    ports = [int(r["tcp.dstport"]) for r in syn]
    order = np.argsort(times)
    times, ports = times[order], [ports[i] for i in order]
    unique, seen, first_t = [], set(), []
    for t, p in zip(times, ports):
        if p not in seen:
            seen.add(p)
            unique.append(p)
            first_t.append(t * 1000)
    cum = np.arange(1, len(unique) + 1)
    duration = max(times) if len(times) else 1

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.6))
    ax1.step(first_t, cum, where="post", color=ACCENT, lw=1.8)
    ax1.set_xlabel("tiempo (ms)")
    ax1.set_ylabel("puertos destino únicos acumulados")
    ax1.set_title("Cobertura del barrido")
    ax1.grid(color=GRID, lw=0.7)
    ax1.set_axisbelow(True)
    ax1.set_ylim(0, 1100)
    ax1.set_xlim(0, duration * 1000)
    ax1.text(0.97, 0.08, f"{len(unique)} puertos en {duration*1000:.0f} ms",
             transform=ax1.transAxes, fontsize=8, color=MUTED, ha="right")

    bins = np.arange(0, duration + 0.004, 0.004)
    counts, edges = np.histogram(times, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2 * 1000
    ax2.bar(centers, counts / 0.004, width=3.2, color=ALERT, alpha=0.85)
    ax2.set_xlabel("tiempo (ms)")
    ax2.set_ylabel("paquetes por segundo")
    ax2.set_title("Tasa instantánea de SYN")
    ax2.grid(axis="y", color=GRID, lw=0.7)
    ax2.set_axisbelow(True)
    ax2.text(0.03, 0.92, f"promedio ≈ {len(syn)/duration:,.0f} SYN/s".replace(",", "."),
             transform=ax2.transAxes, fontsize=8, color=MUTED)
    header(fig, "Figura 8.4. Cobertura y tasa del escaneo SYN",
           "1024 puertos destino en 59 ms. La tasa media es ≈17 400 SYN/s (≈34 800 paquetes TCP/s contando respuestas).")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.74, bottom=0.19, wspace=0.28)
    save(fig, OUT8 / "04_puertos_acumulados.png")

    # --- conteo de banderas ---
    s = summary[0]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.4),
                                   gridspec_kw={"width_ratios": [1.25, 1]})
    names = ["SYN", "SYN-ACK", "RST"]
    vals = [s["syn_enviados"], s["synack_recibidos"], s["rst_recibidos"]]
    cols = [ACCENT, OK, ALERT]
    bars = ax1.bar(names, vals, color=cols, width=0.55)
    ax1.set_ylabel("paquetes")
    ax1.set_title("Banderas TCP observadas")
    ax1.grid(axis="y", color=GRID, lw=0.7)
    ax1.set_axisbelow(True)
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 18, f"{v:,}".replace(",", "."),
                 ha="center", fontsize=8, fontweight="bold", color=INK)
    ax1.set_ylim(0, 1150)

    abiertos = len(s["puertos_abiertos"])
    cerrados = s["puertos_destino_unicos"] - abiertos
    ax2.pie([abiertos, cerrados], labels=["abiertos", "cerrados"],
            colors=[OK, "#c9ced6"], autopct=lambda p: f"{p:.1f}%",
            startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax2.set_title("1024 puertos TCP")
    header(fig, "Figura 8.5. Balance de respuestas del escaneo SYN",
           "1024 SYN enviados: 4 respuestas SYN-ACK (puertos abiertos) y 1020 RST (puertos cerrados).")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.74, bottom=0.19, wspace=0.28)
    save(fig, OUT8 / "05_conteo_flags.png")

    # --- alertas Suricata ---
    fast = (WORK / "suricata" / "cu8_syn" / "fast.log").read_text(encoding="utf-8").splitlines()
    syn_alerts = [l for l in fast if "1008001" in l]
    rst_alerts = [l for l in fast if "1008002" in l]
    lines = []
    for ln in syn_alerts[:18] + ["", "— respuestas RST (regla 1008002) —", ""] + rst_alerts[:18]:
        if not ln:
            lines.append("")
            continue
        if ln.startswith("—"):
            lines.append(ln)
            continue
        parts = ln.split()
        ts = parts[0].split("-", 1)[-1]
        parts2 = ln.split("[**]")
        msg = parts2[1].strip() if len(parts2) >= 3 else ln
        if msg.startswith("["):
            msg = msg.split("]", 1)[-1].strip()
        rest = ln.rsplit("{TCP}", 1)[-1].strip()
        lines.append(f"{ts}  {msg[:46]:<46}  {rest}")
    terminal(OUT8 / "06_suricata_alertas.png",
             "Figura 8.6. Alertas de Suricata para el escaneo SYN (extracto)",
             "34 coincidencias de la regla 1008001 y 34 de la 1008002; se muestran las primeras 18 de cada una. Umbral: 30 eventos por origen en 10 s.",
             ["timestamp (UTC)          mensaje                                         flujo"] +
             ["- " * 52] + lines,
             OUT8 / "06_suricata_alertas.png", max_chars=116, fontsize=6.8, accent=ALERT)


# ----------------------------------------------------------------------------
# CASO 10
# ----------------------------------------------------------------------------
def case10() -> None:
    print("Caso 10 - XMPP y TLS")
    topology(OUT10 / "01_topologia_lab.png",
             "Figura 10.1. Topología del laboratorio XMPP y TLS",
             "Cliente, servidor inseguro (certificado vencido) y servidor endurecido (CA propia).",
             focus="xmpp")

    table_png(OUT10 / "02_hashes_sha256.png",
              "Figura 10.2. Integridad de las capturas del Caso 10",
              "Huellas SHA-256 de las siete capturas utilizadas en el análisis.",
              ["Archivo", "Tamaño", "SHA-256"],
              hash_rows(["CU10_01_xmpp_insecure.pcap",
                         "CU10_02_xmpp_secure.pcap",
                         "CU10_03_xmpp_message.pcap",
                         "CU10_05_xmpp_plaintext.pcap",
                         "CU10_06_https_insecure.pcap",
                         "CU10_07_https_tls12_insecure.pcap",
                         "CU10_08_https_tls12_secure.pcap"]),
              [0.30, 0.10, 0.60], fontsize=6.8)

    # --- handshake STARTTLS ---
    rows1 = read_tsv(WORK / "cu10_insecure_tls_packets.tsv")
    rows2 = read_tsv(WORK / "cu10_secure_tls_packets.tsv")
    lines = ["INSECURO 172.28.50.30 (certificado vencido)",
             "frame  time_rel     origen          destino         protocolo  información",
             "- " * 52]
    for r in rows1:
        lines.append(f'{r["frame.number"]:>5}  {float(r["frame.time_relative"]):<11.6f}  '
                     f'{r["ip.src"]:<15} {r["ip.dst"]:<15} {"TLS":<10}  {r["_ws.col.info"][:44]}')
    lines += ["", "ENDURECIDO 172.28.50.31 (CA propia)",
              "frame  time_rel     origen          destino         protocolo  información",
              "- " * 52]
    for r in rows2:
        lines.append(f'{r["frame.number"]:>5}  {float(r["frame.time_relative"]):<11.6f}  '
                     f'{r["ip.src"]:<15} {r["ip.dst"]:<15} {"TLS":<10}  {r["_ws.col.info"][:44]}')
    lines += ["", "Secuencia XMPP previa al TLS (captura insegura):",
              "  4  0.007062  172.28.50.10 -> 172.28.50.30  STREAM > lab.local",
              "  6  0.007607  172.28.50.30 -> 172.28.50.10  STREAM < lab.local",
              "  8  0.007755  172.28.50.10 -> 172.28.50.30  STARTTLS",
              "  9  0.008110  172.28.50.30 -> 172.28.50.10  PROCEED"]
    terminal(OUT10 / "03_starttls_handshake.png",
             "Figura 10.3. Negociación STARTTLS en ambos servidores",
             "Ambos servidores negocian TLS 1.3 tras STARTTLS/PROCEED. La diferencia no está en la versión, sino en el certificado y en la validación del cliente.",
             lines, OUT10 / "03_starttls_handshake.png", max_chars=124, fontsize=6.8)

    # --- certificado vencido ---
    inc = (WORK / "case10_insecure_sclient.txt").read_text(encoding="utf-8").splitlines()
    keep = [ln for ln in inc if not ln.startswith(("MIID", "MIIE", "MIIB", "MII", "AAA", "AAO"))]
    sel = []
    for ln in keep:
        if any(k in ln for k in ("Connecting", "CONNECTED", "depth=", "verify error",
                                 "notAfter", "subject=", "issuer=", "Verification",
                                 "Verify return code", "New, TLS", "Protocol", "Cipher is",
                                 "Server Temp Key")):
            sel.append(ln)
        elif ln.startswith((" 0 s:", "   i:", "   a:", "   v:")):
            sel.append(ln)
    terminal(OUT10 / "04_certificado_vencido.png",
             "Figura 10.4. Certificado del servidor XMPP inseguro",
             "openssl s_client contra 172.28.50.30: CN=localhost, autofirmado, vigencia 2021-05-13 a 2022-05-13 (vencido).",
             sel, OUT10 / "04_certificado_vencido.png", max_chars=110, fontsize=7.0, accent="#8a5a00")

    # --- certificado válido ---
    sec = (WORK / "case10_secure_sclient.txt").read_text(encoding="utf-8").splitlines()
    keep = [ln for ln in sec if not ln.startswith(("MII", "AAA", "AAO"))]
    sel = []
    for ln in keep:
        if any(k in ln for k in ("Connecting", "CONNECTED", "depth=", "verify error",
                                 "subject=", "issuer=", "Verification", "Verify return code",
                                 "New, TLS", "Protocol", "Cipher is", "Server Temp Key")):
            sel.append(ln)
        elif ln.startswith((" 0 s:", "   i:", "   a:", "   v:")):
            sel.append(ln)
    terminal(OUT10 / "05_certificado_valido.png",
             "Figura 10.5. Certificado del servidor XMPP endurecido",
             "openssl s_client contra 172.28.50.31 con -CAfile: cadena completa, CN=lab.local, Verify return code 0 (ok).",
             sel, OUT10 / "05_certificado_valido.png", max_chars=110, fontsize=7.0, accent=OK)

    # --- cifrado vs claro ---
    lines = [
        "CAPTURA CON TLS  (CU10_03_xmpp_message.pcap)",
        "  búsqueda de 'HOLA-BOB-MENSAJE-CONFIDENCIAL-2026' ....... 0 coincidencias",
        "  búsqueda de 'alice123' ................................. 0 coincidencias",
        "  los registros TLS solo exponen SNI=lab.local y bytes cifrados",
        "",
        "CAPTURA SIN TLS  (CU10_05_xmpp_plaintext.pcap)",
        "  búsqueda de 'HOLA-BOB-SIN-TLS-2026' .................... 1 coincidencia",
        "  18  0.011725  172.28.50.10 -> 172.28.50.30  MESSAGE > bob@lab.local",
        "  cuerpo legible: HOLA-BOB-SIN-TLS-2026",
    ]
    terminal(OUT10 / "06_cifrado_vs_claro.png",
             "Figura 10.6. Contraste entre sesión cifrada y sesión en claro",
             "La misma conversación XMPP: con TLS el contenido no se recupera de la PCAP; sin TLS el cuerpo del mensaje es texto plano.",
             lines, OUT10 / "06_cifrado_vs_claro.png", max_chars=100, fontsize=8.0)

    # --- credenciales en claro ---
    lines = [
        "Trama 8  ·  XMPP AUTH  ·  172.28.50.10 -> 172.28.50.30",
        "",
        "<auth xmlns='urn:ietf:params:xml:ns:xmpp-sasl' mechanism='PLAIN'>",
        "  AGFsaWNlAGFsaWNlMTIz",
        "</auth>",
        "",
        "Base64 decodificado:",
        "  \\x00 alice \\x00 alice123",
        "  ^usuario      ^contraseña",
        "",
        "El mecanismo SASL PLAIN envía usuario y contraseña en claro.",
        "En una captura pasiva la credencial es recuperable sin romper ningún cifrado.",
    ]
    terminal(OUT10 / "07_credenciales_claras.png",
             "Figura 10.7. Credenciales SASL PLAIN expuestas sin TLS",
             "Captura CU10_05_xmpp_plaintext.pcap. Sin STARTTLS, la autenticación viaja en Base64 (codificación, no cifrado).",
             lines, OUT10 / "07_credenciales_claras.png", max_chars=100, fontsize=7.8, accent=ALERT)

    # --- MAM ---
    mam = (WORK / "case10_mam_evidence.txt").read_text(encoding="utf-8").splitlines()
    lines = ["Archivo /var/lib/prosody/lab%2elocal/archive/alice.list",
             ""] + mam[:24]
    terminal(OUT10 / "08_mam_servidor.png",
             "Figura 10.8. Mensaje en claro en el archivo MAM del servidor",
             "Prosody archiva el cuerpo del mensaje sin cifrado adicional: el operador del servidor puede leer todo el historial.",
             lines, OUT10 / "08_mam_servidor.png", max_chars=96, fontsize=7.2, accent="#8a5a00")

    # --- validación MITM ---
    table_png(OUT10 / "09_mitm_validacion.png",
              "Figura 10.9. Validación de certificado frente a un MITM",
              "OpenSSL conectado al intermediario 172.28.50.10:4443 con certificado autofirmado CN=lab.local.",
              ["Escenario", "Comando", "Resultado", "Handshake"],
              [["Sin validar", "s_client -connect 172.28.50.10:4443",
                "exit 0 · Verify return code 18", "Completa"],
               ["Validando", "s_client -CAfile ca.crt -verify_return_error",
                "exit 1 · certificate verify failed", "Aborta"]],
              [0.16, 0.46, 0.27, 0.11], fontsize=8.0)

    # --- alerta Suricata TLS ---
    fast = (WORK / "suricata" / "cu10_tls12_insecure" / "fast.log").read_text(encoding="utf-8").splitlines()
    lines = fast + [
        "",
        "Regla aplicada (suricata/local.rules):",
        'alert tls any any -> any any (msg:"CU10 certificado autofirmado CN=localhost";',
        '  tls.cert_subject; content:"CN=localhost"; sid:1001002; rev:1;)',
        "",
        "Nota: TLS 1.3 cifra el certificado; la alerta se valida con una captura TLS 1.2",
        "(CU10_07). En TLS 1.3 el IDS pasivo solo observa el SNI.",
    ]
    terminal(OUT10 / "10_suricata_tls.png",
             "Figura 10.10. Alerta de Suricata por certificado autofirmado",
             "Reprocesamiento de CU10_07_https_tls12_insecure.pcap. La captura TLS 1.2 equivalente con certificado válido no genera alertas.",
             lines, OUT10 / "10_suricata_tls.png", max_chars=104, fontsize=7.4, accent=ALERT)

    # --- versiones TLS ---
    table_png(OUT10 / "11_versiones_tls.png",
              "Figura 10.11. Versiones TLS aceptadas por cada servidor",
              "Pruebas con openssl s_client restringiendo la versión (-tls1, -tls1_1, -tls1_2, -tls1_3).",
              ["Versión", "Servidor inseguro", "Servidor endurecido", "Observación"],
              [["TLS 1.0", "Rechazada", "Rechazada", "alert protocol version (70)"],
               ["TLS 1.1", "Rechazada", "Rechazada", "alert protocol version (70)"],
               ["TLS 1.2", "Aceptada", "Aceptada", "certificado vencido / válido"],
               ["TLS 1.3", "Aceptada", "Aceptada", "certificado vencido / válido"]],
              [0.16, 0.23, 0.24, 0.37], fontsize=8.4)


def main() -> None:
    case7()
    case8()
    case10()
    print("Figuras generadas.")


if __name__ == "__main__":
    main()
