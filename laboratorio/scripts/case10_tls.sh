#!/bin/sh
# Caso 10: XMPP con TLS débil y con TLS endurecido; mensaje real y MITM controlado.
set -eu

INSEC=172.28.50.30
SEC=172.28.50.31
CAP=/captures
OUT=/lab
IFACE=eth0
mkdir -p "$CAP" "$OUT"

stop_cap() {
    [ -n "${PID:-}" ] && kill "$PID" 2>/dev/null || true
    [ -n "${PID:-}" ] && wait "$PID" 2>/dev/null || true
    PID=
}
trap stop_cap EXIT

echo "[CU10] 1/7 STARTTLS XMPP contra el servidor con certificado vencido"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU10_01_xmpp_insecure.pcap" "host $INSEC and tcp port 5222" >/dev/null 2>&1 &
PID=$!
sleep 1
printf '' | timeout 12 openssl s_client -connect "$INSEC:5222" -starttls xmpp \
    -name lab.local -servername lab.local -showcerts \
    > "$OUT/case10_insecure_sclient.txt" 2>&1 || true
sleep 1
stop_cap

echo "[CU10] 2/7 STARTTLS XMPP contra el servidor endurecido"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU10_02_xmpp_secure.pcap" "host $SEC and tcp port 5222" >/dev/null 2>&1 &
PID=$!
sleep 1
printf '' | timeout 12 openssl s_client -connect "$SEC:5222" -starttls xmpp \
    -name lab.local -servername lab.local -CAfile /certs/ca.crt -verify_return_error -showcerts \
    > "$OUT/case10_secure_sclient.txt" 2>&1 || true
sleep 1
stop_cap

echo "[CU10] 3/7 mensaje XMPP real (cliente con validación deshabilitada)"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU10_03_xmpp_message.pcap" "host $INSEC and tcp port 5222" >/dev/null 2>&1 &
PID=$!
python3 /scripts/xmpp_session.py --role receiver --jid bob@lab.local --password bob123 \
    --server "$INSEC" --port 5222 --insecure --wait 14 > "$OUT/case10_receiver.txt" 2>&1 &
RPID=$!
sleep 4
python3 /scripts/xmpp_session.py --role sender --jid alice@lab.local --password alice123 \
    --recipient bob@lab.local --message "HOLA-BOB-MENSAJE-CONFIDENCIAL-2026" \
    --server "$INSEC" --port 5222 --insecure > "$OUT/case10_sender.txt" 2>&1 || true
wait "$RPID" || true
sleep 1
stop_cap

echo "[CU10] 4/7 comparación de versiones TLS (cliente OpenSSL)"
: > "$OUT/case10_tls_versions.txt"
for v in tls1 tls1_1 tls1_2 tls1_3; do
    {
        echo "===== INSECURE $v ====="
        if [ "$v" = "tls1" ] || [ "$v" = "tls1_1" ]; then
            printf '' | timeout 8 openssl s_client -connect "$INSEC:5222" -starttls xmpp \
                -name lab.local -servername lab.local -"$v" -cipher 'DEFAULT@SECLEVEL=0' 2>&1 | \
                grep -E 'Protocol|Cipher|Verification|alert|error|New,' | head -5
        else
            printf '' | timeout 8 openssl s_client -connect "$INSEC:5222" -starttls xmpp \
                -name lab.local -servername lab.local -"$v" 2>&1 | \
                grep -E 'Protocol|Cipher|Verification|alert|error|New,' | head -5
        fi
    } >> "$OUT/case10_tls_versions.txt" 2>&1 || true
    {
        echo "===== SECURE $v ====="
        if [ "$v" = "tls1" ] || [ "$v" = "tls1_1" ]; then
            printf '' | timeout 8 openssl s_client -connect "$SEC:5222" -starttls xmpp \
                -name lab.local -servername lab.local -"$v" -cipher 'DEFAULT@SECLEVEL=0' \
                -CAfile /certs/ca.crt 2>&1 | \
                grep -E 'Protocol|Cipher|Verification|alert|error|New,' | head -5
        else
            printf '' | timeout 8 openssl s_client -connect "$SEC:5222" -starttls xmpp \
                -name lab.local -servername lab.local -"$v" -CAfile /certs/ca.crt 2>&1 | \
                grep -E 'Protocol|Cipher|Verification|alert|error|New,' | head -5
        fi
    } >> "$OUT/case10_tls_versions.txt" 2>&1 || true
done

echo "[CU10] 5/7 intermediario controlado con certificado de atacante"
openssl s_server -accept 8443 -cert /certs/attacker.crt -key /certs/attacker.key -www \
    > /dev/null 2>&1 &
SPID=$!
sleep 1
set +e
printf 'GET / HTTP/1.0\r\n\r\n' | timeout 6 openssl s_client -connect 172.28.50.10:8443 \
    -servername lab.local > "$OUT/case10_mitm_sin_validacion.txt" 2>&1
RC1=$?
printf 'GET / HTTP/1.0\r\n\r\n' | timeout 6 openssl s_client -connect 172.28.50.10:8443 \
    -servername lab.local -CAfile /certs/ca.crt -verify_return_error \
    > "$OUT/case10_mitm_con_validacion.txt" 2>&1
RC2=$?
set -e
echo "exit_code_sin_validacion=$RC1" >> "$OUT/case10_mitm_sin_validacion.txt"
echo "exit_code_con_validacion=$RC2" >> "$OUT/case10_mitm_con_validacion.txt"
kill "$SPID" 2>/dev/null || true

echo "[CU10] 6/7 mensaje XMPP SIN STARTTLS (autenticación en claro)"
tcpdump -i "$IFACE" -n -s 0 -w "$CAP/CU10_05_xmpp_plaintext.pcap" "host $INSEC and tcp port 5222" >/dev/null 2>&1 &
PID=$!
sleep 1
python3 /scripts/xmpp_session.py --role sender --jid alice@lab.local --password alice123 \
    --recipient bob@lab.local --message "HOLA-BOB-SIN-TLS-2026" --server "$INSEC" \
    --port 5222 --no-starttls --sasl PLAIN > "$OUT/case10_plaintext_sender.txt" 2>&1 || true
sleep 1
stop_cap

echo "[CU10] 7/7 evidencias listas"
ls -l "$CAP"/CU10_*.pcap
