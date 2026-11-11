# AGENTS.md

Context guide for AI agents working in this repository. It summarizes what the official workshop guide asks for, the requirements of each case, how the LaTeX report is organized, and the rules to follow when editing it.

**Language:** this guide is written in English, but the report, the `.tex` files, and the compiled PDF remain in Spanish. Do not translate the LaTeX content unless explicitly requested.

## 1. Project overview

- **Name:** Segundo Taller de Mecanismos de Seguridad (Second Workshop on Security Mechanisms).
- **Institution:** Universidad Distrital Francisco José de Caldas, Faculty of Engineering, Systems Engineering.
- **Official guide:** `SEGUNDO TALLER MECANISMOS DE SEGURIDAD OCTUBRE 26_2026_VERSION FIAL_V2.pdf`, dated October 26, 2026, with a due date of November 14, 2026. The PDF is not versioned: `.gitignore` excludes `SEGUNDO TALLER*.pdf`.
- **Deliverable:** a technical report in LaTeX (Part I: analysis of ten cases; Part II: design of an authorized tracking solution) plus evidence, captures, hashes, and, where applicable, the reproducible lab.
- **Team on the title page:** Juan David Orduz Sastoque (20221020096), Jhojan Aragon Ramirez (20221020060), Yader Ibraldo Quiroga Torres (20222020034), and Arlo Nicolas Ocampo Gallego (20221020104).
- **Instructor:** the guide mentions Octavio José Salcedo Parra. The LaTeX title page omits the instructor line by team decision (see `README.md`).

> **Note on fidelity to the PDF.** The PDF header keeps the line "Fundamentos de redes de comunicaciones" and the instructor's name, even though the workshop is titled "Mecanismos de Seguridad." The LaTeX template uses `\course{Mecanismos de Seguridad}` and omits the instructor. If literal matching with the guide is required, review `main.tex` before changing the title page.

### Ethical and legal scope

The workshop is an academic exercise. It does not ask anyone to breach, attack, or hack real systems, networks, or people. All analysis is performed on didactic or synthetic PCAPs, controlled telemetry, or authorized benign tests in an isolated VLAN or virtual network. Part II is valid only with informed consent, academic purpose, and anonymized data; tracking people without authorization is out of scope.

## 2. What the official guide asks for

The guide has two parts and a set of cross-cutting rules.

### Part I. Case analysis

Analyze ten security scenarios in an IEEE 802.3 Ethernet LAN carrying IPv4/IPv6 and TCP/IP services. For each case, the team must:

1. Observe and describe behavior with evidence (Wireshark, `netstat`, logs, IDS/SIEM).
2. Justify the indicators found and distinguish symptom, indicator, hypothesis, and confirmed evidence.
3. Propose preventive, detective, corrective, and recovery controls.
4. Attach legible evidence with a SHA-256 hash and alternative benign explanations.
5. Answer the analysis questions without deleting them.

Attack activities are replaced by PCAP analysis, synthetic telemetry, or authorized benign tests.

### Part II. Programming

Design an app, program, or bot that can register a phone number, request or receive the location of the associated device, and display it on a map, in real time or at intervals. The guide proposes three approaches:

| Service | Location source | Feasibility and limits |
|---|---|---|
| WhatsApp | Manually shared location | Limited and indirect; there is no real-time tracking without user action. |
| Telegram | Bot and user-sent location | The bot can request it with buttons, but cannot track automatically. |
| Phone directly | Device GPS | Requires an installed app, location permissions, and express consent. |

The solution must operate with consent, anonymized data, and an academic purpose. Unofficial APIs, reverse engineering, interception, and covert tracking are not allowed.

## 3. Mandatory lab rules

- Use only equipment or virtual machines controlled by the team, in an isolated VLAN or virtual network.
- Generate benign test traffic or use didactic/synthetic PCAPs. Run DoS, exfiltration, or spoofing tests only in isolated, authorized environments.
- Synchronize clocks and record date, time, IP, port, tool, and version.
- Anonymize personal data and credentials; do not capture traffic from users outside the lab.
- Keep an original copy of every piece of evidence, compute its SHA-256, and analyze a working copy.
- Do not send traffic to the Internet, production institutional networks, or third-party addresses.

## 4. Topology and tools

Topology suggested by the guide (equivalent private addresses are allowed):

| Element | Address / role | Recommendation |
|---|---|---|
| IEEE 802.3 Ethernet switch | Lab VLAN | No connection to the production network. |
| Analyst machine | 192.168.50.10/24 | Wireshark and log access. |
| Web/test server | 192.168.50.20/24 | Lab HTTP or HTTPS with a test certificate. |
| Lab DNS server | 192.168.50.53/24 | Resolve test names only. |
| Messaging server (optional) | 192.168.50.30/24 | XMPP in an isolated environment. |
| Lab gateway | 192.168.50.1/24 | No forwarding to the Internet; filtering enabled. |

The repository's actual deployment uses `172.28.50.0/24` on an isolated Docker bridge network with `internal: true` (see section 10).

Suggested tools: Wireshark/TShark, `netstat` and PowerShell, Event Viewer, Windows Defender Firewall, Zeek and/or Suricata, Wazuh or an equivalent SIEM, Python, and scikit-learn. The report declares the versions used in the tools table: Wireshark 4.2.5, `tcpdump` 4.99.4, Nmap 7.95, Suricata 7.0.7, OpenSSL 3.3.7, Prosody 0.11.9, Python 3.12.13/Scapy 2.6.1, and Docker 29.8.0/Compose v5.5.1.

## 5. Part I: case-by-case requirements

Each case must cover observation, analysis, indicators, alternative hypotheses, controls, and evidence. The files live in `secciones/03-casos/`.

### Case 1. TCP SYN Flood: unavailability and connection exhaustion

- **Situation:** a lab web server responds slowly or stops accepting new connections.
- **Procedure:** review TCP establishment and count SYN, SYN/ACK, and ACK per time window; inspect `netstat -ano` and map PID/service; compare the rate against a baseline; review server and firewall logs.
- **Indicators:** SYN spikes without a completed handshake, growing pending connections, many sources, or an unusual temporal pattern. A single indicator does not confirm an attack.
- **Mitigation:** update the system and service, limit exposure, enable SYN protection, apply rate limits, and escalate to the administrator; verify that legitimate clients are not blocked.
- **Evidence:** SYN/ACK timeline graph, connection table, proposed rule/alert, and before/after comparison.
- **Questions:** what resources does the server hold during the handshake? What false positives can legitimate peaks produce?
- **In the repo:** developed in `01-syn-flood.tex` (analyst: Juan David Orduz). It uses `200722_tcp_anon.pcapng` and images from `imagenes/Evidencias CU-1/`. The conclusion is that the capture shows no evidence of a SYN Flood.

### Case 2. DNS tunneling: possible covert exfiltration over UDP/53

- **Situation:** repetitive DNS queries or unusually long domain names.
- **Procedure:** filter `udp.port == 53` and `dns`; examine label length and entropy, frequency, volume per client, and queried domains; correlate with the authorized resolver and DNS logs; use only test domains or training PCAPs.
- **Indicators:** long or high-entropy subdomains, high frequency, atypical response sizes, and unusual destinations; rule out telemetry or CDN traffic.
- **Mitigation:** force authorized resolvers, log queries, filter DNS, and apply egress policies; investigate the source host before blocking.
- **Evidence:** filtered captures, host/domain table, hypothesis, and log verification.
- **Questions:** why does connectionless UDP not make all DNS malicious? Which attributes distinguish an anomaly?
- **In the repo:** developed in `02-dns-tunneling.tex` (analyst: lab team). It uses `CU2_01`–`CU2_03` PCAPs from `laboratorio/captures/`, images from `imagenes/Evidencias CU-2/`, and Suricata rules 1002001–1002003. The lab resolver (`laboratorio/reflector/`) answers DNS, NTP and SSDP. The capture is a didactic Base32 tunnel with 121-character qnames plus a legitimate high-rate burst as a false-positive control.

### Case 3. Exposure of HTTP, FTP, and legacy services

- **Situation:** the server exposes unnecessary or weakly configured services.
- **Procedure:** inventory services and ports using the system inventory and an authorized, limited-scope check; review authentication logs and events; document version, operational need, and owner; verify encryption and least privilege.
- **Indicators:** unnecessarily exposed services, unsupported software, failed authentication attempts, cleartext protocols, and default configurations.
- **Mitigation:** disable unneeded services, prefer SFTP/SSH/HTTPS, apply MFA, patch software, and use least-privilege accounts.
- **Evidence:** service inventory, relevant events, risk/criticality matrix, and remediation plan.
- **Questions:** how is an open port prioritized? What is the difference between exposure, vulnerability, and exploitation?
- **In the repo:** developed in `03-servicios-heredados.tex` (finding C3-H01, no analyst recorded). It uses images from `imagenes/Evidencias CU-3/`; there is no PCAP or hash.

### Case 4. Anomaly detection with AI/ML on TCP/IP traffic

- **Situation:** propose an intelligent defense that detects deviations from normal traffic.
- **Procedure:** build a dataset from didactic PCAPs or benign lab traffic with aggregate features (connections/minute, bytes per flow, duration, TCP flags, request/response ratio); split training and evaluation by time or session to avoid leakage; compare a statistical baseline with an anomaly detector; document precision, false positives, and limits; anonymize and protect the training data.
- **Indicators:** sustained deviation from the baseline; a high anomaly score that must be investigated alongside network evidence and logs.
- **Mitigation:** human review, model drift monitoring, no blocking based solely on the model, and protection of training data.
- **Evidence:** reproducible notebook or script, feature definitions, metrics, confusion matrix if labels exist, and anonymized examples.
- **Questions:** how do class imbalance and legitimate load changes affect the model? Which metric is most useful?
- **In the repo:** template only in `04-anomalias-ml.tex`; the feature table is empty.

### Case 5. TCP: unexpected resets and signs of injection or desynchronization

- **Situation:** TCP sessions terminate abruptly or restart repeatedly.
- **Procedure:** filter `tcp.flags.reset == 1`; correlate timestamps, endpoints, and sessions; check whether RSTs match legitimate closures, service restarts, firewall behavior, or loss of connectivity; correlate with Zeek/Suricata and application logs.
- **Indicators:** out-of-context RSTs, unusual frequency, truncated sessions, or inconsistencies that require correlation. Do not infer MITM from an RST alone.
- **Mitigation:** properly validated TLS, segmentation, endpoint updates, IDS detection, and review of routes/intermediate devices.
- **Evidence:** affected flow table, log excerpts, timestamps, and SHA-256 of the PCAP.
- **Questions:** what benign causes produce RSTs? What additional evidence would strengthen the manipulation hypothesis?
- **In the repo:** developed in `05-tcp-resets.tex` (finding H-CU5-01, no analyst recorded). It uses the same PCAP as Case 1 and concludes that there are zero RSTs. It contains Markdown artifacts (`**...**`) and `[cite: N]` that should be fixed if the file is edited.

### Case 6. UDP: DNS, NTP, or SSDP reflection/amplification

- **Situation:** the server or gateway records an unusual volume of UDP responses, possibly disproportionate to the requests.
- **Procedure:** examine volume by protocol, source, destination, and time window; distinguish expected traffic from unsolicited responses; review the configuration of owned services to confirm they are not open reflectors; do not generate amplification traffic—use training PCAPs or simulated counters.
- **Indicators:** large response volume, request/response asymmetry, unexpected ports, and destinations unrelated to observed requests.
- **Mitigation:** disable unnecessary services, restrict DNS recursion, apply rate limiting and anti-spoofing filtering on managed infrastructure.
- **Evidence:** packets/bytes per second graphs, service inventory, and recommended controls.
- **Questions:** how is a legitimate burst distinguished from reflection? Which controls belong to the server and which to the network provider?
- **In the repo:** developed in `06-udp-reflexion.tex` (analyst: lab team). It uses `CU6_01`–`CU6_05` PCAPs, images from `imagenes/Evidencias CU-6/`, and Suricata rules 1006001–1006003. The reflector at `172.28.50.53` serves DNS/53, NTP/123 (monlist emulation) and SSDP/1900; `case6_udp.sh` generates the spoofed traffic and `split_cu6.py` cuts the continuous reflector capture per phase. Measured factors: DNS 34.7×, NTP 5.1×, SSDP 10.4× (link bytes).

### Case 7. ICMP: scanning, atypical payloads, and a possible tunnel

- **Situation:** an ICMP rate higher than usual, or packets with repetitive sizes/patterns.
- **Procedure:** filter `icmp` and group by source/destination IP, type, code, length, and time; establish a legitimate ping baseline; use synthetic or didactic PCAPs for payloads; do not transmit sensitive information over ICMP.
- **Indicators:** echo request/reply bursts, unusual lengths, repetitive periodicity, or volume not explained by diagnostics.
- **Mitigation:** allow only the ICMP types needed for operation, apply proportional limits, and monitor without indiscriminately blocking messages the network requires.
- **Evidence:** dashboard by IP, applied filter, size/frequency table, and proposed rule.
- **Questions:** what legitimate functions does ICMP serve? What would be the impact of blocking it completely?
- **In the repo:** developed in `07-icmp.tex` (analyst: Yader Ibraldo Quiroga Torres). It uses the Docker lab, PCAPs `CU7_01` through `CU7_03`, images from `Evidencias CU-7`, and Suricata rules 1007001/1007002.

### Case 8. Port scanning and service fingerprinting

- **Situation:** logs show sequential attempts against several ports or unusual services.
- **Procedure:** analyze firewall/IDS logs and an authorized PCAP; count unique destinations and ports per source and period; correlate Zeek/Suricata; build an exposure list for owned services without scanning foreign networks.
- **Indicators:** connections to many ports in a short time, repeated attempts against nonexistent services, and unusual banner/version queries.
- **Mitigation:** reduce the exposed surface, filter by need, update services, alert on repeated patterns, and apply temporary blocking with review.
- **Evidence:** indicator list, exposed ports/services, detection rule, and hardening plan.
- **Questions:** what are the limitations of attributing a scan to a single IP? How are false positives from authorized monitoring reduced?
- **In the repo:** developed in `08-escaneo-puertos.tex` (analyst: Yader Ibraldo Quiroga Torres). It uses PCAPs `CU8_01` through `CU8_03`, images from `Evidencias CU-8`, and Suricata rules 1008001/1008002.

### Case 9. Alert prioritization and correlation with AI and SIEM

- **Situation:** the monitoring center receives multiple alerts that must be grouped and prioritized.
- **Procedure:** normalize firewall, server, Zeek/Suricata, and OS events; deduplicate without losing traceability; define aggregate features per host/time window and test an anomaly detector with controlled data; use an LLM only to summarize anonymized alerts and suggest triage, verifying every recommendation against evidence.
- **Indicators:** alerts correlated by host/time, explainable risk scores, and converging signals across multiple sources.
- **Mitigation:** human review before disruptive actions, log access control, bias/drift evaluation, decision logging, and rollback.
- **Evidence:** pipeline diagram, enriched alert example, priority criteria, and human validation record.
- **Questions:** how do you explain an alert to an analyst? What risk does automating blocks based only on a score create?
- **In the repo:** template only in `09-siem-alertas.tex`; the source table is empty.

### Case 10. XMPP messaging: interception and TLS errors

- **Situation:** investigate whether communication between XMPP clients and the server is properly protected.
- **Procedure:** review TLS configuration, certificates, names, validity, and trust chain on a lab server (Openfire/ejabberd); capture connection metadata and verify that encrypted session content is not readable; review server logs for negotiation errors, invalid certificates, or unexpected connections.
- **Indicators:** expired or untrusted certificates, insecure negotiation, exposed administrative services, and connection patterns that do not match expected use.
- **Mitigation:** require robust TLS and certificate validation, limit administrative interfaces, update the server, and apply E2EE when the threat model requires it.
- **Evidence:** TLS checklist, anonymized events, configuration evidence, and remediation plan.
- **Questions:** what does TLS protect and what does it not protect? How does transport encryption differ from end-to-end encryption?
- **In the repo:** developed in `10-xmpp-tls.tex` (analyst: Yader Ibraldo Quiroga Torres). It uses Prosody in Docker, PCAPs `CU10_01` through `CU10_08`, images from `Evidencias CU-10`, and Suricata rules 1001002/1001003.

### Status of the ten cases

| Case | File | Status | Main evidence in the repo |
|---|---|---|---|
| 1 | `secciones/03-casos/01-syn-flood.tex` | Developed | `200722_tcp_anon.pcapng`, `imagenes/Evidencias CU-1/` |
| 2 | `secciones/03-casos/02-dns-tunneling.tex` | Developed | `CU2_*` PCAPs, `Evidencias CU-2`, Suricata rules 1002001–1002003 |
| 3 | `secciones/03-casos/03-servicios-heredados.tex` | Developed | `imagenes/Evidencias CU-3/`; no PCAP or hashes |
| 4 | `secciones/03-casos/04-anomalias-ml.tex` | Template | Empty feature table |
| 5 | `secciones/03-casos/05-tcp-resets.tex` | Developed | `200722_tcp_anon.pcapng`, `imagenes/Evidencias CU-5/` |
| 6 | `secciones/03-casos/06-udp-reflexion.tex` | Developed | `CU6_*` PCAPs, `Evidencias CU-6`, Suricata rules 1006001–1006003 |
| 7 | `secciones/03-casos/07-icmp.tex` | Developed | `CU7_*` PCAPs, `Evidencias CU-7`, Suricata rules |
| 8 | `secciones/03-casos/08-escaneo-puertos.tex` | Developed | `CU8_*` PCAPs, `Evidencias CU-8`, Suricata rules |
| 9 | `secciones/03-casos/09-siem-alertas.tex` | Template | Empty source table |
| 10 | `secciones/03-casos/10-xmpp-tls.tex` | Developed | `CU10_*` PCAPs, `Evidencias CU-10`, Suricata rules |

Cases 1, 2, 6, 7, 8, and 10 record an analyst (the new cases use "lab team"); Cases 3 and 5 do not. Completing Cases 4 and 9 is the main gap in Part I.

## 6. Minimum finding record format

Every finding must be recorded with these fields, both in the case form and in the consolidated table:

| Field | What to record |
|---|---|
| Identifier | Case, evidence number, and analyst name. |
| Date/time | Timestamp and time zone; known synchronization. |
| Source/destination | IP, MAC when relevant, ports, and protocol; anonymize if needed. |
| Observation | Directly observed fact, without premature conclusions. |
| Hypothesis | Possible explanation and benign alternatives considered. |
| Validation | PCAP or log consulted, filter, inspection commands, and result. |
| Severity | Impact, probability, and justification. |
| Action | Proposed measure, owner, false-positive risk, and verification. |
| Integrity | File name, size, and SHA-256 hash of the original evidence. |

Evidence rule: an anomaly is not proof of an attack. Before assigning severity, confirm with at least two independent sources (for example, a PCAP and a server log) and document benign explanations that could not be ruled out. If evidence is insufficient, state it as a limitation.

## 7. Part I deliverables and quality criteria

Deliverables:

- Team technical report with an executive summary and lab scope.
- Ten case forms with indicators, analysis, alternative hypotheses, and defensive measures.
- Legible screenshots and didactic/synthetic PCAPs where applicable, with SHA-256.
- Proposed and justified detection rules; enabling automatic blocks in production is not required.
- Conclusions about evidence limits and improvement opportunities.
- Evidence appendix with file name, size, date, and hash.
- Work distribution table and a verification list signed by all four team members.

Quality criteria: reproducibility (stated filter, command, or script), traceability (claim → evidence → timestamp), legible captures, anonymization, integrity of the original evidence, and a critical stance toward false positives and unconfirmed hypotheses.

## 8. Part II: authorized tracking application

### 8.1 Functional requirements

| Code | Requirement | Description | Priority |
|---|---|---|---|
| RF-01 | Phone-number registration | Register and link devices through the phone number. | High |
| RF-02 | Location request and capture | Allow the target user to send their current or automatic location. | High |
| RF-03 | Periodic update | Capture the device location at a defined interval (for example, every 10 minutes). | Medium |
| RF-04 | Map visualization | Display the location on Google Maps, OpenStreetMap, or another integrated map. | High |
| RF-05 | Alerts (optional) | Alert when the device enters or leaves a geographic area (geofencing). | Low |
| RF-06 | Location history | Store and query past locations by date and time. | High |
| RF-07 | Secure access | Authenticate the user and authorize access to their own or shared locations. | High |

### 8.2 Technical requirements

| Component | Technical requirement | Suggested technology |
|---|---|---|
| Mobile app | GPS capture and periodic coordinate upload; location permissions; SMS or verification-code linking. | Native Android/iOS, Flutter, or React Native. |
| Telegram bot (optional) | Manual request via buttons; the user starts the chat and authorizes; no automatic tracking. | Telegram Bot API. |
| Backend | REST API to register users and receive locations, with versioning and OpenAPI documentation. | Python, Node.js, PHP, or similar. |
| Database | Persist users, devices, locations, and consents. | PostgreSQL, MongoDB, or Firebase. |
| Authentication | Registration and access by phone number and token, with expiration and revocation. | JWT, OAuth 2.0, or secure sessions. |
| Map | Visualization and reverse geocoding; history and access control. | Google Maps, Mapbox, or Leaflet.js. |

Optional features from the guide: custom geofencing, battery saving through scheduled activation, multiple linked devices, a web/administrative panel, and movement or route statistics.

### 8.3 Security and privacy requirements

The LaTeX template adds these requirements to the guide:

| Code | Requirement | Proposed implementation |
|---|---|---|
| RS-01 | Encryption in transit | TLS 1.2 or higher for the API and bot. |
| RS-02 | Credential protection | Argon2, bcrypt, or scrypt; never cleartext. |
| RS-03 | Sessions and tokens | Expiration, rotation, revocation, and secure storage. |
| RS-04 | Access control | Each user can only query their own or authorized locations. |
| RS-05 | Rate limiting | Limits per user, device, and IP. |
| RS-06 | Input validation | Validate and normalize phone numbers, coordinates, dates, and parameters. |
| RS-07 | Encryption at rest | Encrypt the database and backups; manage keys outside the code. |
| RS-08 | Auditing | Log access, queries, consent changes, and security errors. |
| RS-09 | Consent | Explicit record with date, scope, purpose, and revocation. |
| RS-10 | Minimization and retention | Collect only what is necessary and define retention and deletion periods. |

### 8.4 Ethics, law, and out of scope

- Location is personal data; in Colombia, Law 1581 of 2012 applies and prior, express, informed authorization is required.
- Principles: informed consent, limited purpose, minimization, security, retention and deletion, transparency, and non-discrimination.
- Prohibited: tracking without consent, intercepting communications, using unofficial APIs, sharing locations with unauthorized third parties, surveilling/harassing/discriminating, and delegating blocking or sanctions to an AI model.
- The solution must request the location, not take it by force. The user must know who receives the data, why, for how long, and how to revoke consent.

### 8.5 Part II deliverables

- Functional source code with commit history.
- README with requirements, installation, configuration, execution, and tests.
- Architecture diagram and data model.
- REST API documentation (OpenAPI or equivalent).
- Demonstration with synthetic or lab data.
- Test plan and results for happy-path and error cases.
- Privacy policy, informed consent, and revocation mechanism.
- Risk analysis, limitations, and future work.

### 8.6 Current state in this repository

Part II is documented in LaTeX, but **there is no application code** in the current tree. The architecture diagram is a placeholder (`fig:arquitectura`), and several requirements, data-model, and risk tables are partially empty. Do not present Part II as implemented if only the design exists.

## 9. The LaTeX project

### 9.1 What it is

`main.tex` produces an academic report in Spanish using the APA 7 class (`apa7`), with an institutional title page, table of contents, Part I with ten case forms, Part II with the solution design, conclusions, APA 7 bibliography, and appendices. The compiled PDF is `main.pdf`.

The template is not a literal transcription of the guide: it reproduces its structure and requirements and adds APA 7 formatting, ethics notes, security requirement tables, and evidence spaces. When the guide and the template differ in wording, the guide's requirement prevails.

The title page already contains the four names and codes, the course, and the Faculty of Engineering. It does not include an instructor line. The due date is November 14, 2026.

### 9.2 Class, packages, and formatting

- Class: `\documentclass[stu, 12pt, letterpaper, donotrepeattitle, floatsintext]{apa7}`.
- Language: Spanish `babel` (`spanish,es-noquoting`), `csquotes`.
- Typography: `newtxtext`, `newtxmath`, `microtype`.
- Tables: `array`, `booktabs`, `longtable`, `makecell`, `tabularx`, `colortbl`.
- Figures and boxes: `graphicx` with `\graphicspath{{imagenes/}}`, `float`, `pdflscape`, `tcolorbox`.
- Bibliography: `biblatex` with `style=apa`, `backend=biber`, `biblatex-apa`, and `\DeclareLanguageMapping{spanish}{spanish-apa}`.
- Numbering: `\setcounter{secnumdepth}{2}` (sections and subsections numbered; case files use `\subsection`).
- Robust justification: `\emergencystretch=3em`, `\tolerance=9999`, and a `para/begin` hook so long `\texttt` strings do not overflow.

### 9.3 Custom environments and macros

| Element | Use |
|---|---|
| `\begin{situacion}...\end{situacion}` | Gray box titled "Situación" (Situation); opens each case form. |
| `\begin{nota}{Title}...\end{nota}` | Blue box for warnings, ethical scope, or rules. |
| `\registrohallazgo{Caso N}` | Generates the empty nine-field finding record table. |
| `\checkbox` | Empty checkbox for verification lists. |
| `Y` column | Left-aligned `X` column from `tabularx`; used in almost every table. |

### 9.4 File structure

```text
main.tex                         Preamble, title page, metadata, and document assembly
referencias.bib                  BibLaTeX sources (APA 7)
latexmkrc                        Windows compilation and locked-PDF protection
README.md                        Template description and usage
imagenes/Logo_UD.png             Institutional logo
imagenes/Evidencias CU-N/        Captures for each case
secciones/
  01-introduccion.tex            Introduction, scope, ethics note, and team data
  02-marco-parte1.tex            Presentation, objectives, topology, rules, and tools
  03-casos/                      Ten independent case forms
    01-syn-flood.tex
    02-dns-tunneling.tex
    03-servicios-heredados.tex
    04-anomalias-ml.tex
    05-tcp-resets.tex
    06-udp-reflexion.tex
    07-icmp.tex
    08-escaneo-puertos.tex
    09-siem-alertas.tex
    10-xmpp-tls.tex
  04-registro-hallazgos.tex      Minimum format and consolidated findings
  05-entregables-parte1.tex      Deliverables and quality criteria
  06-parte2-descripcion.tex      Solution description and scope
  07-parte2-requisitos.tex       Functional, technical, and security requirements
  08-parte2-arquitectura.tex     Architecture, data model, and work plan
  09-parte2-etica.tex            Ethics, legality, and privacy
  10-conclusiones.tex            Conclusions, limitations, and future work
  11-anexos.tex                  Evidence, verification list, and glossary
laboratorio/                     Docker, captures, scripts, Suricata rules, and work
Capturas PCAP/                   Original and working copies of the PCAPs
```

### 9.5 How the document is assembled

`main.tex` uses `\input` in this order:

1. `secciones/01-introduccion`
2. "Parte I. Análisis de casos" heading
3. `secciones/02-marco-parte1`
4. Cases 1 through 10, in order
5. `secciones/04-registro-hallazgos`
6. `secciones/05-entregables-parte1`
7. "Parte II. Programación" heading
8. `secciones/06-parte2-descripcion`, `07`, `08`, `09`
9. `secciones/10-conclusiones`
10. `\printbibliography`
11. `secciones/11-anexos`

To add or reorder content, edit the corresponding `\input` in `main.tex`. Do not duplicate sections inside other files.

### 9.6 Case-form conventions

A complete case form follows this pattern:

```latex
\subsection{Caso N. Title}
\label{caso:key}

\begin{situacion}
Situation, objective, and theoretical background.
\end{situacion}

\paragraph{Procedimiento.} ...
\paragraph{Resultados obtenidos.} ...
\paragraph{Análisis de resultados.} ...
\paragraph{Indicadores de detección.} ...
\paragraph{Regla de detección propuesta.} ...
\paragraph{Mitigación y defensa.} ...
\paragraph{Preguntas de análisis.} ...
\paragraph{Conclusiones.} ...

% Finding record: manual or \registrohallazgo{Caso N}
```

Style rules:

- Write in formal academic Spanish, in the third person or impersonal voice.
- Do not delete the analysis questions; answer them with evidence.
- Distinguish observation, hypothesis, validation, and limitation.
- Use `\texttt{}` for commands, filters, paths, and file names; use `\path{}` for paths inside tables.
- Escape `_`, `%`, `&`, `#`, `$`, `{`, `}`, and `~` in LaTeX.
- Figures: `\begin{figure}[H]` or `[htbp]`, `\includegraphics[width=0.85\textwidth]{imagenes/Evidencias CU-N/NN_name.png}`, `\caption{}`, and `\label{fig:...}`.
- Tables: `booktabs` (`\toprule`, `\midrule`, `\bottomrule`), `tabularx` with the `Y` column, `\footnotesize`, and `\renewcommand{\arraystretch}{1.2}`. Do not mix `\hline` and vertical rules in new content.
- Labels: `fig:`, `tab:`, `caso:`. Reference with `\ref{}`.
- Citations: `\parencite{key}` or `\textcite{key}`; add the entry to `referencias.bib`.
- Do not write Markdown inside LaTeX (`**text**`, `[cite: N]`, etc.).

### 9.7 Bibliography

`referencias.bib` already contains the keys in use: `nist80094`, `nist800123`, `nist80061`, `rfc792`, `rfc1035`, `rfc6120`, `rfc8446`, `owasp2021`, `wireshark`, `sklearn`, `nmap`, `suricata`, `openssl`, `prosody`, and `ley1581`. For a new source, add the BibLaTeX entry and cite it; do not invent keys or URLs.

### 9.8 Compilation

Requirements: TeX Live 2026 or equivalent with `apa7`, `biblatex-apa`, `biber`, `newtx`, `tcolorbox`, `booktabs`, `tabularx`, and `enumitem`. It also compiles on Overleaf with pdfLaTeX and Biber.

```bash
latexmk -pdf main.tex
```

Manual compilation:

```bash
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

`latexmkrc` moves `main.pdf` aside before each pass to avoid the "I can't write on file main.pdf" error when a viewer keeps it open on Windows. Do not edit `main.pdf` by hand: regenerate it.

### 9.9 Current state and technical debt

- Cases 4 and 9 are still templates; their finding record forms are empty.
- The team table in `01-introduccion.tex` is empty, although the title page already has names and codes.
- `10-conclusiones.tex` contains `[Redacte...]` placeholders and the synthesis table is empty.
- Appendix A records hashes for `CU2_*`, `CU6_*`, `CU7_*`, `CU8_*`, and `CU10_*`; hashes for the evidence of Cases 1, 3, and 5 are missing. Case 3 states that hashes were not supplied.
- The consolidated findings table (`04-registro-hallazgos.tex`) only has rows for Cases 2 and 6; the rest are pending.
- The `situacion` box is now `breakable` in `main.tex`; long situations no longer overflow the page.
- The Part II architecture figure is a placeholder box; several requirements, data-model, and risk tables have empty cells.
- Case 5 contains `**...**` and `[cite: N]` (stray Markdown) that print literally.
- In Case 7, the sentence "Las dos reglas de la Tabla~\ref{tab:icmp}" points to the traffic distribution table, not the rules; fix the reference if the file is edited.
- `main.pdf` is versioned as a compiled copy; after content changes, recompile and verify that there are no broken references or `??`.

## 10. Reproducible lab

`laboratorio/docker-compose.yml` defines the `labnet` network (`172.28.50.0/24`, `internal: true`) and five services:

| Service | Container | IP | Role |
|---|---|---|---|
| `victim` | `lab-victim` | 172.28.50.20 | FTP, SSH, Telnet, HTTP, and test services; passive capture target for Case 6. |
| `reflector` | `lab-reflector` | 172.28.50.53 | DNS/53, NTP/123 (monlist emulation), SSDP/1900, and a continuous tcpdump capture for Case 6. |
| `xmpp-insecure` | `lab-xmpp-insecure` | 172.28.50.30 | Prosody with an expired/self-signed certificate and weak configuration. |
| `xmpp-secure` | `lab-xmpp-secure` | 172.28.50.31 | Prosody with a local CA, robust TLS, and restricted administration. |
| `analyst` | `lab-analyst` | 172.28.50.10 | TShark, Nmap, Scapy, Suricata, OpenSSL, and scripts. |

Common commands:

```bash
cd laboratorio
docker compose up -d --build
docker compose exec analyst sh /scripts/case2_dns.sh
docker compose exec analyst python3 /scripts/analyze_cu2.py
docker compose exec analyst sh /scripts/case6_udp.sh
docker compose exec analyst python3 /scripts/split_cu6.py
docker compose exec analyst python3 /scripts/analyze_cu6.py
docker compose exec analyst sh /scripts/case7_icmp.sh
docker compose exec analyst sh /scripts/case8_scan.sh
docker compose exec analyst sh /scripts/case10_tls.sh
docker compose exec analyst sh /scripts/run_suricata.sh
docker compose exec analyst python3 /scripts/export_cases.py
```

Case 6 also needs a passive capture on the victim around `case6_udp.sh`: `docker compose exec -d victim tcpdump -i eth0 -U -w /captures/CU6_05_victim_inbound.pcap udp` before the script and `pkill -INT tcpdump` afterwards. The reflector keeps a continuous capture that `split_cu6.py` cuts per phase using the timestamps in `/lab/cu6_phases.json`.

The full step-by-step reproduction guide for Cases 2 and 6 is `laboratorio/README-CU2-CU6.md`.

Certificates are generated with `laboratorio/xmpp/generar-certs.sh` (requires Docker and OpenSSL). Captures are stored in `laboratorio/captures/`, results in `laboratorio/work/`, and the integrity manifest in `laboratorio/evidencias_sha256.txt`. Suricata rules are in `laboratorio/suricata/local.rules` and cover Cases 2, 6, 7, 8, and 10.

Do not run these scripts outside the isolated network or against addresses that do not belong to the lab.

## 11. Conventions for agents

1. **Source of truth:** the PDF guide governs content; the LaTeX template governs format. If they conflict, preserve the guide's requirement and adapt the form.
2. **Do not invent evidence:** do not create results, hashes, captures, versions, or conclusions that are not in the files. If a datum is missing, write "not determined" or state it as a limitation.
3. **Do not delete existing work:** Cases 1, 3, 5, 7, 8, and 10 already have development. Edit incrementally and preserve figures, tables, and forms.
4. **Maintain traceability:** every new claim must point to a verifiable figure, table, PCAP, log, filter, or command.
5. **Anonymize:** do not add real people's names, credentials, emails, phone numbers, or public IPs. Use lab data.
6. **Integrity:** do not modify the original captures in `Capturas PCAP/Originales/`. If `laboratorio/captures/` is regenerated, keep a copy of the previous version, work on copies, and update `laboratorio/evidencias_sha256.txt` and Appendix A.
7. **LaTeX:** edit the corresponding section file, not `main.tex`, unless adding a section or changing the order. Compile at the end.
8. **Bibliography:** cite with BibLaTeX and keep APA 7 style. Do not use bare `\cite{}` if APA formatting is intended.
9. **Part II:** treat it as an academic design with consent; do not implement covert tracking, unofficial APIs, or real data collection.
10. **Before closing:** verify that no placeholders, broken references, or unjustified empty cells remain.
