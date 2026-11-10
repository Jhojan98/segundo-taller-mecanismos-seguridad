-- Prosody: configuración ENDURECIDA para el laboratorio.
-- Certificado firmado por una CA local, TLS 1.2+ y administración
-- restringida a loopback.
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
    "admin_adhoc";
    "bosh";
    "http_files";
}

allow_registration = false
authentication = "internal_plain"

c2s_require_encryption = true
allow_unencrypted_plain_auth = false
s2s_require_encryption = true

-- Puertos a nivel de servidor (no dentro del VirtualHost).
c2s_ports = { 5222 }
s2s_ports = { 5269 }

-- Interfaz HTTP/HTTPS solo en loopback (no accesible desde la LAN).
http_ports = { 5280 }
http_interfaces = { "127.0.0.1" }
https_ports = { 5281 }
https_interfaces = { "127.0.0.1" }

-- Certificado del listener HTTPS global.
ssl = {
    key = "/certs/secure.key";
    certificate = "/certs/secure.crt";
    protocol = "tlsv1_2+";
    ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM";
    options = { "no_sslv2", "no_sslv3", "no_tlsv1", "no_tlsv1_1" };
}

VirtualHost "lab.local"

ssl = {
    key = "/certs/secure.key";
    certificate = "/certs/secure.crt";
    protocol = "tlsv1_2+";
    ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM";
    options = { "no_sslv2", "no_sslv3", "no_tlsv1", "no_tlsv1_1" };
}
