#!/usr/bin/env sh
# Genera la CA local y el certificado válido para lab.local.
# El certificado "inseguro" se extrae de la imagen de Prosody (vencido).
set -eu
cd "$(dirname "$0")"

CERTDIR="certs"
mkdir -p "$CERTDIR"

echo "[1/6] CA local"
openssl genrsa -out "$CERTDIR/ca.key" 4096
openssl req -x509 -new -nodes -key "$CERTDIR/ca.key" -sha256 -days 3650 \
    -out "$CERTDIR/ca.crt" \
    -subj "/C=CO/O=Laboratorio Academico/CN=Laboratorio CA"

echo "[2/6] Clave y CSR del servidor seguro"
openssl genrsa -out "$CERTDIR/secure.key" 2048
openssl req -new -key "$CERTDIR/secure.key" -out "$CERTDIR/secure.csr" \
    -subj "/C=CO/O=Laboratorio Academico/CN=lab.local"

echo "[3/6] Certificado firmado por la CA"
openssl x509 -req -in "$CERTDIR/secure.csr" -CA "$CERTDIR/ca.crt" \
    -CAkey "$CERTDIR/ca.key" -CAcreateserial -out "$CERTDIR/secure.crt" \
    -days 825 -sha256 -extfile server.ext

echo "[4/6] Certificado autofirmado de atacante (para prueba de intermediario)"
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$CERTDIR/attacker.key" \
    -out "$CERTDIR/attacker.crt" -days 30 -sha256 \
    -subj "/C=CO/O=Atacante Laboratorio/CN=lab.local" \
    -addext "subjectAltName=DNS:lab.local"

echo "[5/6] Extracción del certificado vencido de la imagen Prosody"
cid=$(docker create prosody/prosody:latest)
docker cp "$cid:/etc/prosody/certs/localhost.crt" "$CERTDIR/insecure.crt"
docker cp "$cid:/etc/prosody/certs/localhost.key" "$CERTDIR/insecure.key"
docker rm "$cid" >/dev/null

echo "[6/6] Permisos y verificación"
chmod 644 "$CERTDIR"/*.crt
chmod 640 "$CERTDIR"/*.key
openssl x509 -in "$CERTDIR/insecure.crt" -noout -subject -issuer -dates
openssl x509 -in "$CERTDIR/secure.crt" -noout -subject -issuer -dates
echo "Listo."
