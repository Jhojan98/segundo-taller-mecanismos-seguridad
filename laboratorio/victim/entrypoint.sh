#!/bin/sh
set -eu

# Página web mínima servida por nginx en tcp/80.
mkdir -p /run/nginx /var/www/localhost/htdocs
printf '%s\n' '<h1>Servidor web de laboratorio</h1>' > /var/www/localhost/htdocs/index.html
nginx

# SSH real en tcp/22 (solo se valida el banner y la versión).
ssh-keygen -A >/dev/null 2>&1
/usr/sbin/sshd -D -e >/var/log/sshd.log 2>&1 &

# Servicios con banner propio en 21, 23, 4444 y 8080.
python3 /opt/banners.py >/var/log/banners.log 2>&1 &

wait
