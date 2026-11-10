#!/usr/bin/env python3
"""Extrae evidencia legible de las capturas del Caso 10.

- En la captura sin TLS busca el cuerpo del mensaje y la autenticación SASL.
- En la captura con TLS comprueba que el mensaje y la contraseña no aparecen.
- Resume el handshake TLS (versión, SNI, cipher suite).
"""
import binascii
import re
import subprocess
import sys


def tcp_payload_text(pcap: str) -> str:
    out = subprocess.run(
        ["tshark", "-r", pcap, "-Y", "tcp.len>0", "-T", "fields", "-e", "tcp.payload"],
        capture_output=True, text=True, check=False,
    ).stdout
    data = b""
    for line in out.splitlines():
        line = line.strip().replace(":", "")
        if line:
            try:
                data += binascii.unhexlify(line)
            except binascii.Error:
                pass
    return data.decode("utf-8", "replace")


def count_matches(pcap: str, needle: str) -> int:
    out = subprocess.run(
        ["tshark", "-r", pcap, "-Y", f'tcp contains "{needle}"'],
        capture_output=True, text=True, check=False,
    ).stdout
    return len([l for l in out.splitlines() if l.strip()])


def main() -> int:
    if len(sys.argv) != 3:
        print("uso: analyze_cu10.py <plaintext.pcap> <tls.pcap>")
        return 2
    plain_pcap, tls_pcap = sys.argv[1], sys.argv[2]

    text = tcp_payload_text(plain_pcap)
    marker = "HOLA-BOB-SIN-TLS-2026"
    print("=== Captura SIN TLS ===")
    print(f"Contiene el cuerpo {marker!r}: {marker in text}")
    for m in re.finditer(r'<auth[^>]*mechanism="([^"]+)"[^>]*>([^<]+)</auth>', text):
        import base64
        decoded = base64.b64decode(m.group(2)).decode("utf-8", "replace")
        print(f"SASL {m.group(1)} (base64): {m.group(2)}")
        print(f"SASL decodificado: {decoded!r}")
    for m in re.finditer(r"<body>([^<]+)</body>", text):
        print(f"Cuerpo del mensaje en claro: {m.group(1)}")

    print("\n=== Captura CON TLS ===")
    for needle in (marker.replace("SIN-TLS", "MENSAJE-CONFIDENCIAL"), "alice123"):
        print(f"Coincidencias de {needle!r}: {count_matches(tls_pcap, needle)}")

    print("\n=== Handshake TLS (captura con TLS) ===")
    out = subprocess.run(
        ["tshark", "-r", tls_pcap, "-Y", "tls.handshake",
         "-T", "fields", "-e", "frame.number", "-e", "tls.handshake.type",
         "-e", "tls.handshake.extensions_server_name", "-e", "tls.handshake.ciphersuite"],
        capture_output=True, text=True, check=False,
    ).stdout
    for line in out.splitlines()[:20]:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
