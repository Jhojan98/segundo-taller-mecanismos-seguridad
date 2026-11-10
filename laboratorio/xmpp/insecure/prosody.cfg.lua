-- Prosody: configuración DELIBERADAMENTE DÉBIL para el laboratorio.
-- Escenario: certificado vencido/autofirmado, autenticación en claro
-- permitida y puerto HTTP de administración expuesto a toda la red.
daemonize = false
pidfile = "/var/run/prosody/prosody.pid"

admins = { "admin@lab.local" }

modules_enabled = {
    "roster";
    "saslauth";
    "tls";
    "dialback";
    "disco";
    "ping";
    "version";
    "register";
    "admin_adhoc";
    "bosh";
    "http_files";
    "mam";
    "carbons";
}

allow_registration = true
authentication = "internal_plain"

-- Debilidades intencionales del escenario:
c2s_require_encryption = false
allow_unencrypted_plain_auth = true
s2s_require_encryption = false

-- Puertos a nivel de servidor (no dentro del VirtualHost).
c2s_ports = { 5222 }
s2s_ports = { 5269 }

-- Interfaz HTTP/HTTPS escuchando en todas las interfaces.
http_ports = { 5280 }
http_interfaces = { "*" }
https_ports = { 5281 }
https_interfaces = { "*" }

-- Certificado del listener HTTPS global.
ssl = {
    key = "/certs/insecure.key";
    certificate = "/certs/insecure.crt";
    protocol = "tlsv1+";
    ciphers = "DEFAULT:@SECLEVEL=0";
    options = { "no_sslv2", "no_sslv3" };
}

VirtualHost "lab.local"

ssl = {
    key = "/certs/insecure.key";
    certificate = "/certs/insecure.crt";
    protocol = "tlsv1+";
    ciphers = "DEFAULT:@SECLEVEL=0";
    options = { "no_sslv2", "no_sslv3" };
}
