#!/usr/bin/env python3
"""Servicios de banner para el inventario de exposición del laboratorio.

No procesa datos de usuarios: solo entrega un banner fijo y cierra la
conexión, de modo que nmap pueda realizar fingerprinting de servicios.
"""
import socket
import threading

BANNERS = {
    21: b"220 Laboratorio FTP 1.0 listo\r\n",
    23: b"\xff\xfd\x18\xff\xfd\x20Laboratorio Telnet 0.9\r\n",
    4444: b"LAB-SVC/0.1 ready\r\n",
    8080: (
        b"HTTP/1.0 200 OK\r\n"
        b"Server: LabHTTP/0.9\r\n"
        b"Content-Type: text/plain\r\n"
        b"Content-Length: 26\r\n\r\n"
        b"Servicio HTTP de pruebas.\r\n"
    ),
}


def serve(port: int, banner: bytes) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", port))
        s.listen(32)
        while True:
            conn, _ = s.accept()
            try:
                conn.settimeout(2.0)
                try:
                    conn.recv(1024)
                except socket.timeout:
                    pass
                conn.sendall(banner)
            except OSError:
                pass
            finally:
                conn.close()


threads = [threading.Thread(target=serve, args=(p, b), daemon=True) for p, b in BANNERS.items()]
for t in threads:
    t.start()
for t in threads:
    t.join()
