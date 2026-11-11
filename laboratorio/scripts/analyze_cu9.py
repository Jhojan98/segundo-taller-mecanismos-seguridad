#!/usr/bin/env python3
"""Caso 9 - Priorizacion y correlacion de alertas (multi-fuente) con puntaje explicable.

Pipeline: normalizar -> deduplicar (con trazabilidad) -> correlacionar por host/ventana ->
puntaje explicable -> alerta enriquecida -> prompt anonimizado para LLM -> registro de validacion humana.

  python caso9_triage.py --demo
  python caso9_triage.py --eve a/eve.json b/eve.json [--nginx access.log] [--zeek-conn conn.log.json] [--anomaly-hosts IP ...]

El script NO ejecuta bloqueos ni llama a ningun LLM: solo produce la alerta enriquecida y un prompt
anonimizado. Toda accion disruptiva queda sujeta a validacion humana.
"""
import argparse, csv, hashlib, json, os, re, secrets
from collections import defaultdict
from datetime import datetime, timezone

WINDOW_S = 120                      # ventanas fijas; eventos en fronteras no se mezclan
SEV_W = {1: 40, 2: 25, 3: 10}       # Suricata: 1 = alta
SOURCE_BONUS = 15                   # por cada fuente independiente adicional que converge
SIG_BONUS = 5                       # por cada firma distinta adicional
ANOMALY_BONUS = 20                  # si el detector del Caso 4 marca el host/ventana
CRITICAL = {"172.28.50.1": 1.3, "172.28.50.53": 1.3, "172.28.50.20": 1.2}  # activos criticos del lab


def ts(s):
    """Suricata escribe '2026-11-10T16:47:38.724704+0000' (sin ':' en el offset); fromisoformat falla en Python < 3.11."""
    s = str(s).strip()
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+0000"
    for f in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(s, f).astimezone(timezone.utc)
        except ValueError:
            pass
    parsed = datetime.fromisoformat(s)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp sin zona horaria: {s!r}")
    return parsed.astimezone(timezone.utc)


# ------------------------------------------------------------- 1. normalizacion
def from_suricata(path):
    ev = []
    invalid_json = 0
    with open(path, encoding="utf-8") as fh:
        lines = enumerate(fh)
        for i, ln in lines:
            try:
                j = json.loads(ln)
            except json.JSONDecodeError:
                invalid_json += 1
                continue
            if j.get("event_type") != "alert":
                continue
            a = j["alert"]
            try:
                event_ts = ts(j["timestamp"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"timestamp Suricata inválido en {path!r}, línea {i + 1}: "
                    f"{j.get('timestamp')!r}"
                ) from exc
            ev.append(dict(event_id=f"suricata:{os.path.basename(path)}:{i}",
                           source="suricata", ts=event_ts,
                           src=j["src_ip"], dst=j["dest_ip"], sig_id=a["signature_id"],
                           sig=a["signature"], severity=int(a.get("severity", 3)),
                           ref=f"flow_id={j.get('flow_id')}"))
    if invalid_json:
        print(f"advertencia: {path!r}: {invalid_json} líneas JSON inválidas ignoradas")
    return ev


def from_zeek_conn(path, min_rst_ratio=0.0):
    """conn.log en JSON (policy LogAscii::use_json=T). Solo conexiones con estado de rechazo/reset."""
    ev = []
    for i, ln in enumerate(open(path, encoding="utf-8")):
        j = json.loads(ln)
        if j.get("conn_state") in ("REJ", "RSTO", "RSTR", "S0"):
            ev.append(dict(event_id=f"zeek:{os.path.basename(path)}:{j['uid']}", source="zeek",
                           ts=datetime.fromtimestamp(j["ts"], tz=timezone.utc),
                           src=j["id.orig_h"], dst=j["id.resp_h"], sig_id=f"conn_{j['conn_state']}",
                           sig=f"Zeek conn_state={j['conn_state']}", severity=3, ref=f"uid={j['uid']}"))
    return ev


NGINX_RE = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+)[^"]*" (\d{3}) ')


def from_nginx(path, burst=100):
    """access.log (formato combined). Emite UN evento por (cliente, ventana) con >= `burst` peticiones.
    Sirve para contrastar: un SYN flood NO deja rastro aqui (el handshake no se completa); una rafaga
    legitima si."""
    cnt, first = defaultdict(int), {}
    for i, ln in enumerate(open(path, encoding="utf-8", errors="replace")):
        m = NGINX_RE.match(ln)
        if not m:
            continue
        t_ = datetime.strptime(m.group(2), "%d/%b/%Y:%H:%M:%S %z").astimezone(timezone.utc)
        k = (m.group(1), int(t_.timestamp() // WINDOW_S))
        cnt[k] += 1
        first.setdefault(k, (t_, i))
    ev = []
    for (ip, w), n in cnt.items():
        if n >= burst:
            ev.append(dict(event_id=f"nginx:{os.path.basename(path)}:{ip}:{w}", source="webserver", ts=first[(ip, w)][0], src=ip,
                           dst="172.28.50.20", sig_id="http_burst", sig=f"{n} peticiones HTTP en {WINDOW_S}s",
                           severity=3, ref=f"access.log linea {first[(ip, w)][1]}"))
    return ev


def demo_events():
    """Telemetria SINTETICA: un incidente multi-fuente sobre .20 y ruido benigno sobre .53 y .10."""
    base = datetime(2026, 11, 10, 15, 0, 0, tzinfo=timezone.utc)
    E, n = [], 0

    def add(off, source, src, dst, sid, sig, sev):
        nonlocal n
        n += 1
        E.append(dict(event_id=f"{source}:{n}", source=source, ts=datetime.fromtimestamp(
            base.timestamp() + off, tz=timezone.utc), src=src, dst=dst, sig_id=sid, sig=sig, severity=sev, ref=f"syn{n}"))

    for k in range(12):   # incidente
        add(k * 3, "suricata", "10.9.9.9", "172.28.50.20", 2100001, "LAB SYN flood hacia web", 2)
    for k in range(5):
        add(10 + k * 5, "suricata", "10.9.9.9", "172.28.50.20", 2100002, "LAB escaneo de puertos", 2)
    for k in range(8):
        add(15 + k * 4, "zeek", "10.9.9.9", "172.28.50.20", "conn_S0", "Zeek conn_state=S0", 3)
    add(30, "windows", "172.28.50.20", "172.28.50.20", "sysmon_3", "Proceso inusual con conexion saliente", 2)
    for k in range(3):    # ruido: monitoreo autorizado
        add(k * 40, "suricata", "172.28.50.10", "172.28.50.53", 2100003, "LAB consulta DNS larga", 3)
    return E


# ------------------------------------------------------------- 2. deduplicacion
def dedup(events):
    """Agrupa por (fuente,src,dst,sig_id,ventana) y conserva todos los IDs."""
    g = {}
    for e in sorted(events, key=lambda x: x["ts"]):
        w = int(e["ts"].timestamp() // WINDOW_S)
        k = (e["source"], e["src"], e["dst"], e["sig_id"], w)
        if k not in g:
            g[k] = dict(e, first_seen=e["ts"], last_seen=e["ts"], count=0,
                        evidence_ids=[], refs=[], max_severity=e["severity"], window=w)
        g[k]["count"] += 1
        g[k]["last_seen"] = e["ts"]
        g[k]["evidence_ids"].append(e["event_id"])
        g[k]["refs"].append(e["ref"])
        g[k]["max_severity"] = max(g[k]["max_severity"], e["severity"])
    return list(g.values())


# ------------------------------------------------------------- 3-4. correlacion y puntaje
def correlate(groups, anomaly_hosts=frozenset()):
    by = defaultdict(list)
    for g in groups:
        by[(g["dst"], g["window"])].append(g)
    alerts = []
    for (host, w), items in by.items():
        sources = {i["source"] for i in items}
        sigs = {i["sig_id"] for i in items}
        base = max(SEV_W.get(i["max_severity"], 5) for i in items)
        vol = min(20, sum(i["count"] for i in items) // 5)       # tope: el volumen solo no domina
        parts = {"severidad_maxima": base,
                 "convergencia_fuentes": SOURCE_BONUS * (len(sources) - 1),
                 "firmas_distintas": SIG_BONUS * (len(sigs) - 1),
                 "volumen": vol,
                 "anomalia_ML": ANOMALY_BONUS if (host, w) in anomaly_hosts or host in anomaly_hosts else 0}
        mult = CRITICAL.get(host, 1.0)
        score = round(min(100, sum(parts.values()) * mult), 1)
        prio = "ALTA" if score >= 70 else "MEDIA" if score >= 40 else "BAJA"
        alerts.append(dict(host=host, window_start=datetime.fromtimestamp(w * WINDOW_S, tz=timezone.utc).isoformat(),
                           score=score, prioridad=prio, desglose=parts, multiplicador_criticidad=mult,
                           fuentes=sorted(sources), firmas=sorted(map(str, sigs)),
                           eventos=sum(i["count"] for i in items),
                            evidencia={f"{i['source']}:{i['sig_id']}": i["evidence_ids"] for i in items},
                           accion_sugerida="REVISION HUMANA; no bloquear automaticamente"))
    return sorted(alerts, key=lambda a: -a["score"])


# ------------------------------------------------------------- 5. anonimizacion + prompt LLM
SALT = secrets.token_hex(8)   # sal por ejecución; no se versiona


def pseudo(ip):
    prefix = "LAB_" if ip.startswith("172.28.50.") else "EXT_"
    return prefix + hashlib.sha256((SALT + ip).encode()).hexdigest()[:16]


def llm_prompt(a):
    safe = {k: a[k] for k in ("score", "prioridad", "desglose", "fuentes", "eventos")}
    safe["host"] = pseudo(a["host"])
    safe["firmas"] = [
        "SIG_" + hashlib.sha256((SALT + str(sig)).encode()).hexdigest()[:12]
        for sig in a["firmas"]
    ]
    return ("Eres un asistente de triage SOC. Resume en 5 lineas y sugiere pasos de INVESTIGACION (no de "
            "bloqueo). Si algo no esta en los datos, di 'no determinable'. Datos anonimizados:\n"
            + json.dumps(safe, ensure_ascii=False, indent=2))


# ------------------------------------------------------------- 6. validacion humana
def write_validation_log(alerts, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["host", "ventana", "score", "prioridad", "analista", "decision",
                    "evidencia_verificada", "falso_positivo", "reversible", "notas"])
        for a in alerts:
            w.writerow([a["host"], a["window_start"], a["score"], a["prioridad"], "", "", "", "", "", ""])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--eve", nargs="*", help="uno o varios eve.json de Suricata")
    ap.add_argument("--zeek-conn"); ap.add_argument("--nginx", help="access.log del servidor web (combined)")
    ap.add_argument("--http-burst", type=int, default=100, help="peticiones/ventana para marcar rafaga HTTP")
    ap.add_argument("--anomaly-hosts", nargs="*", default=[],
                    help="hosts marcados por el detector del Caso 4; se aplican a todas sus ventanas")
    ap.add_argument("--out", default="salida_caso9")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    ev = demo_events() if a.demo else [e for p in (a.eve or []) for e in from_suricata(p)]
    if a.zeek_conn:
        ev += from_zeek_conn(a.zeek_conn)
    if a.nginx:
        ev += from_nginx(a.nginx, a.http_burst)
    if not ev:
        ap.error("usa --demo o al menos --eve/--nginx")
    groups = dedup(ev)
    alerts = correlate(groups, frozenset(a.anomaly_hosts))
    print(f"eventos crudos: {len(ev)} -> grupos tras deduplicar: {len(groups)} -> alertas por host/ventana: {len(alerts)}")
    for al in alerts:
        print(f"[{al['prioridad']:5}] {al['score']:5} {al['host']:15} fuentes={al['fuentes']} desglose={al['desglose']}")
    json.dump(alerts, open(f"{a.out}/alertas_enriquecidas.json", "w"), indent=2, ensure_ascii=False)
    open(f"{a.out}/prompt_llm_ejemplo.txt", "w", encoding="utf-8").write(llm_prompt(alerts[0]))
    write_validation_log(alerts, f"{a.out}/registro_validacion_humana.csv")


if __name__ == "__main__":
    main()
