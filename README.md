# Segundo Taller — Mecanismos de Seguridad

Plantilla en **LaTeX** para el Segundo Taller de Mecanismos de Seguridad. El documento está dividido por secciones y contiene una ficha independiente para cada uno de los diez casos de la Parte I, además de la estructura de la Parte II (programación) y los anexos de evidencias.

La portada está configurada con **cuatro integrantes**, la materia **Mecanismos de Seguridad** y la **Facultad de Ingeniería** de la Universidad Distrital Francisco José de Caldas. No se incluye línea de profesor.

## Contenido

- **Parte I. Análisis de casos:** presentación, objetivos, resultados de aprendizaje, topología, reglas del laboratorio, herramientas y diez fichas de caso.
- **Parte II. Programación:** descripción de la solución de rastreo autorizado, requisitos funcionales, requisitos técnicos, requisitos de seguridad, arquitectura de referencia, modelo de datos, plan de trabajo y consideraciones éticas y legales.
- **Cierre:** conclusiones, referencias en APA 7 y anexos (evidencias, lista de verificación y glosario).

## Requisitos

- TeX Live 2026 o superior, o una distribución equivalente con los paquetes:
  - `apa7`
  - `biblatex-apa` y `biber`
  - `newtx`, `tcolorbox`, `booktabs`, `tabularx`, `enumitem`
- Alternativamente, el proyecto se puede compilar en **Overleaf** seleccionando pdfLaTeX y Biber.

## Compilación

Desde la raíz del proyecto:

```bash
latexmk -pdf main.tex
```

Si se compila manualmente:

```bash
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

El resultado se genera en `main.pdf`. En el repositorio se incluye una versión compilada de la plantilla.

## Estructura

```text
main.tex                         Preámbulo, portada y ensamblado
referencias.bib                  Fuentes en BibLaTeX (APA 7)
latexmkrc                        Configuración de compilación en Windows
imagenes/Logo_UD.png             Logo institucional
secciones/
  01-introduccion.tex            Introducción, alcance, nota ética y equipo
  02-marco-parte1.tex            Presentación, objetivos, topología y herramientas
  03-casos/                      Diez fichas de caso independientes
  04-registro-hallazgos.tex      Formato y consolidado de hallazgos
  05-entregables-parte1.tex      Entregables y criterios de calidad
  06-parte2-descripcion.tex      Descripción de la solución de rastreo
  07-parte2-requisitos.tex       Requisitos funcionales, técnicos y de seguridad
  08-parte2-arquitectura.tex     Arquitectura, modelo de datos y plan de trabajo
  09-parte2-etica.tex            Consideraciones éticas, legales y de privacidad
  10-conclusiones.tex            Conclusiones y limitaciones
  11-anexos.tex                  Evidencias, checklist y glosario
```

## Personalización

1. En `main.tex`, reemplace `Integrante 1`, `Integrante 2`, `Integrante 3` e `Integrante 4` por los nombres y códigos reales.
2. Ajuste la fecha de entrega en `\duedate{...}`.
3. Complete la tabla de integrantes y la distribución de responsabilidades en `secciones/01-introduccion.tex`.
4. Reemplace los diagramas de topología y arquitectura por las figuras del equipo.
5. Complete cada ficha de caso en `secciones/03-casos/` y registre los hashes SHA-256 en el Anexo A.
6. Actualice `referencias.bib` y cite con `\parencite{clave}` o `\textcite{clave}`.

## Notas de la plantilla

- La portada usa la clase `apa7` y el logo institucional.
- El documento no incluye el nombre del docente.
- Las fichas de caso conservan las preguntas de análisis y agregan una tabla de registro con los campos mínimos de evidencia.
- La Parte II incluye una advertencia explícita sobre consentimiento, privacidad y uso académico. El rastreo de ubicaciones solo es válido con autorización del usuario.
- El archivo PDF de la guía original no se publica en el repositorio; la plantilla es autónoma.

## Uso académico

Este material se distribuye con fines académicos. Las actividades de laboratorio deben realizarse en un entorno aislado, con equipos propios o máquinas virtuales, direcciones privadas y autorización expresa. No se permite atacar redes o sistemas reales ni rastrear personas sin consentimiento.

## Repositorio

https://github.com/Jhojan98/segundo-taller-mecanismos-seguridad
