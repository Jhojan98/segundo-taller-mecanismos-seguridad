# AGENTS.md (reglas para opencode en este repositorio)

Proyecto: informe LaTeX del Segundo Taller de Mecanismos de Seguridad (Universidad Distrital) + laboratorio Docker.
Trabajo asignado a esta sesión: SOLO Casos 4 y 9.

Reglas obligatorias
- Idioma: español. No uses modelos de lenguaje para inventar cifras: toda cifra sale de archivos en laboratorio/work/.
- Archivos que SÍ puedes crear o editar: secciones/03-casos/04-anomalias-ml.tex, secciones/03-casos/09-siem-alertas.tex,
  laboratorio/scripts/analyze_cu4.py, laboratorio/scripts/analyze_cu9.py, laboratorio/scripts/case4_*.sh,
  laboratorio/work/cu4*, laboratorio/work/cu9, laboratorio/work/suricata_cu4, imagenes/Evidencias CU-4, imagenes/Evidencias CU-9.
- Solo AGREGAR al final (nunca reescribir): laboratorio/suricata/local.rules, laboratorio/evidencias_sha256.txt,
  secciones/11-anexos.tex (filas nuevas), referencias.bib, secciones/10-conclusiones.tex.
- NO tocar: otros casos (01 a 03, 05 a 08, 10), Bot/, main.pdf, laboratorio/xmpp/, Capturas PCAP/Originales (solo lectura).
- Seguridad: red del laboratorio 172.28.50.0/24 (Docker internal). Prohibido generar tráfico hacia cualquier otra dirección,
  escribir herramientas de ataque o ejecutar escaneos/inundaciones. No ejecutes docker ni comandos de red: los ejecuta la persona.
- No hagas commits ni push. No instales paquetes del sistema.
- Estilo LaTeX: copia la estructura y macros de secciones/03-casos/07-icmp.tex (situacion, figuras con \label, tablas tabularx, ficha final).
- Antes de editar varios archivos, muestra el plan y espera aprobación.