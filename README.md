# Segundo Taller de Mecanismos de Seguridad

Informe técnico, laboratorio y producto mínimo viable del **Segundo Taller de Mecanismos de Seguridad** de la Universidad Distrital Francisco José de Caldas. El trabajo tiene dos partes: el análisis forense de diez casos sobre tráfico de red y una aplicación funcional que comparte ubicación con consentimiento explícito.

- **Asignatura:** Mecanismos de Seguridad
- **Programa:** Ingeniería de Sistemas — Facultad de Ingeniería
- **Universidad:** Universidad Distrital Francisco José de Caldas

## Integrantes

| Integrante | Código |
|---|---|
| Juan David Orduz Sastoque | 20221020096 |
| Jhojan Aragón Ramírez | 20221020060 |
| Yader Ibraldo Quiroga Torres | 20222020034 |
| Arlo Nicolás Ocampo Gallego | 20221020104 |

## Contenido del informe

### Parte I. Análisis de casos

Diez fichas construidas sobre capturas de laboratorio, con indicadores, hipótesis alternativas, reglas de detección y medidas de defensa:

1. Análisis de un SYN Flood y del establecimiento TCP.
2. Túnel DNS sobre consultas TXT.
3. Servicios heredados y puertos en escucha.
4. Detección de anomalías con Isolation Forest.
5. Paquetes TCP RST y cierre de sesiones.
6. Reflexión y amplificación UDP (DNS, NTP y SSDP).
7. Barrido y túnel ICMP.
8. Escaneo de puertos y fingerprinting.
9. Correlación y priorización de alertas en un SIEM.
10. XMPP, TLS y cifrado de extremo a extremo.

Cada caso incluye su ficha de registro, la evidencia que lo sustenta y las limitaciones de la muestra. El formato de registro y el consolidado de los diez hallazgos están en la sección «Formato mínimo de registro por hallazgo» (sección 7); la síntesis de resultados, en «Conclusiones» (sección 20).

### Parte II. Programación: bot de Telegram y panel web

**Ubicación Compartida** es el MVP académico de la Parte II. Permite que una persona comparta su ubicación de forma voluntaria con contactos que ella misma autoriza y que esas posiciones se vean en un mapa. El bot no rastrea dispositivos ni localiza números telefónicos: la posición solo se registra cuando el propietario pulsa el botón nativo de ubicación de Telegram y confirma el envío.

- Bot de Telegram con registro, vinculación por invitación y gestión de permisos.
- API REST en FastAPI con autenticación por JWT y documentación OpenAPI.
- Panel web en React con mapa Leaflet/OpenStreetMap, historial y autorizaciones.
- PostgreSQL 16 con seis entidades y doble consentimiento.
- Despliegue reproducible con Docker Compose.
- 55 pruebas automatizadas y un recorrido de extremo a extremo de 13 pasos.

El código, la instalación y los detalles técnicos están en [`Bot/`](Bot/README.md).

## Laboratorio

El laboratorio se ejecuta en una red Docker aislada (`172.28.50.0/24`, opción `internal: true`), sin salida a Internet. Allí conviven el analista, un host pasivo, un resolver DNS y reflectores didácticos para DNS, NTP y SSDP.

- `laboratorio/docker-compose.yml`: topología de la red aislada.
- `laboratorio/scripts/`: generación de tráfico, análisis de capturas y reglas de Suricata.
- `laboratorio/suricata/`: configuración y reglas locales.
- `laboratorio/work/`: resultados intermedios y métricas.
- `laboratorio/evidencias_sha256.txt`: manifiesto de integridad de las capturas.
- `Capturas PCAP/`: capturas originales y de trabajo.

Las reglas de Suricata se validaron con la versión 7.0.7 sobre las capturas del laboratorio. La regla de correlación de Wazuh del Caso 9 quedó documentada como propuesta, sin despliegue ni validación. Ninguna prueba se dirigió a redes institucionales, direcciones de terceros ni servicios en producción.

## Requisitos

- TeX Live 2026 o MiKTeX con `pdflatex`, `latexmk` y `biber`.
- Paquetes de LaTeX: `apa7`, `biblatex-apa`, `newtx`, `tcolorbox`, `booktabs`, `tabularx`, `enumitem`, `makecell`, `pdflscape`, `colortbl`, `microtype`.
- Para la Parte II: Docker con Compose y un token de bot de Telegram (ver `Bot/README.md`).

El informe también se puede compilar en Overleaf seleccionando pdfLaTeX y Biber.

## Compilación

Desde la raíz del repositorio:

```bash
latexmk -pdf main.tex
```

El resultado queda en `main.pdf`. Si se compila manualmente:

```bash
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

En Windows, `latexmkrc` aparta el PDF anterior si un visor lo mantiene abierto. Si `main.bcf` quedó corrupto por una compilación interrumpida, borre `main.bcf` y `main.bbl` y repita la secuencia manual.

## Estructura del repositorio

```text
main.tex                         Preámbulo, portada y ensamblado del informe
referencias.bib                  Fuentes en BibLaTeX (APA 7)
latexmkrc                        Compilación en Windows sin bloqueo del PDF
secciones/
  02-marco-parte1.tex            Presentación, objetivos, topología y herramientas
  03-casos/                      Diez fichas de caso (01 a 10)
  04-registro-hallazgos.tex      Formato y consolidado de hallazgos
  05-entregables-parte1.tex      Entregables y criterios de calidad
  06-parte2-descripcion.tex      Descripción y alcance de la solución
  07-parte2-requisitos.tex       Requisitos funcionales, técnicos y de seguridad
  08-parte2-arquitectura.tex     Arquitectura, modelo de datos, despliegue y pruebas
  09-parte2-etica.tex            Consideraciones éticas, legales y de privacidad
  10-conclusiones.tex            Conclusiones, limitaciones y trabajo futuro
  11-anexos.tex                  Evidencias, lista de verificación y glosario
imagenes/                        Figuras y capturas por caso
Capturas PCAP/                   Capturas originales y de trabajo
laboratorio/                     Red aislada, scripts, Suricata y manifiesto de hashes
Bot/                             Bot de Telegram, API y panel web de la Parte II
```

## Reproducibilidad y evidencia

- Toda cifra del informe proviene de una captura, un script o un archivo de resultados del repositorio; no se usan datos inventados.
- Cada ficha indica el archivo analizado, el filtro o comando aplicado y la limitación de la muestra.
- Los hashes SHA-256 se verifican contra `laboratorio/evidencias_sha256.txt` y se reproducen en el Anexo A.
- Las reglas de detección y sus umbrales se calibraron contra la línea base del laboratorio y se validaron con Suricata.
- Los resultados de la Parte II se verificaron con pruebas automatizadas y un recorrido de extremo a extremo sobre la pila real.

## Uso académico y ético

Este material tiene fines exclusivamente académicos. Las actividades de laboratorio se realizan en un entorno aislado, con equipos propios o máquinas virtuales, direcciones privadas y autorización expresa. No se atacan redes ni sistemas reales y no se rastrea a personas sin consentimiento.

La Parte II implementa consentimiento explícito, finalidad limitada, minimización de datos y revocación inmediata. El rastreo encubierto, la captura en segundo plano y la localización de terceros quedan fuera del alcance por razones éticas y legales.

## Repositorio

https://github.com/Jhojan98/segundo-taller-mecanismos-seguridad
