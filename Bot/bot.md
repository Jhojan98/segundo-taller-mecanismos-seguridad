# Bot de Telegram para compartir ubicación — Documento técnico para el informe

> **Mecanismos de Seguridad Informática — Taller 2.**
> Este documento describe el diseño, la implementación y la verificación del MVP descrito en
> [`README.md`](README.md). **Todos los resultados de pruebas que se reportan aquí corresponden a
> ejecuciones reales**.

---

## 1. Introducción y alcance

El proyecto implementa un bot de Telegram que permite a una persona **compartir su ubicación geográfica de forma voluntaria y explícita** 
con otros usuarios, y un **panel web** donde la información compartida se visualiza sobre un mapa (Leaflet + OpenStreetMap).

Alcance del MVP:

- **Sí hace**: registra ubicaciones que el usuario envía a propósito (botón de compartir ubicación
  del propio Telegram), gestiona invitaciones, relaciones de contacto y permisos, y muestra la
  información en un panel web autenticado.
- **No hace**: no rastrea GPS en segundo plano, no envía *push* silenciosos, no localiza números
  telefónicos ni a contactos sin su participación, no usa Google Maps ni claves de API externas.

---

## 2. Arquitectura general

Un único servicio (`backend`) contiene a la vez la **API REST (FastAPI)** y el **bot
(python-telegram-bot en modo polling)**, iniciados y detenidos en el *lifespan* de FastAPI. El
frontend (React + Vite, servido por nginx) se comunica con la API a través de un proxy interno.

```
Usuario ──Telegram──▶ Bot (polling) ──┐
                                      ├──▶ FastAPI ──▶ PostgreSQL (volumen pgdata)
Usuario ──Navegador──▶ nginx (front) ──┘   (misma red interna, 5432 no publicado)
```

| Componente | Rol |
|---|---|
| `Bot/back` | API REST + bot de Telegram + SQLAlchemy (un proceso, un contenedor) |
| `Bot/front` | Panel React (Login, Dashboard, Historial, Autorizaciones, Mi ubicación) con proxy `/api` → `backend:8000` |
| `postgres` | Base de datos con volumen y *healthcheck*; puerto no publicado al exterior |

---

## 3. Stack tecnológico

| Capa | Tecnología | Versión fijada |
|---|---|---|
| Bot | `python-telegram-bot` | 22.8 |
| API | `FastAPI` / `uvicorn` | 0.162.4 / 0.54.0 |
| ORM | `SQLAlchemy` | 2.1.8 |
| BD | `PostgreSQL` + `psycopg2-binary` | 2.9.13 |
| Config/Auth | `pydantic-settings`, `PyJWT` | 2.16.2 / 2.15.1 |
| Frontend | React, `react-leaflet`, `leaflet`, `react-router-dom` | 19.3.1, 5.0.0, 1.9.4, 7.18.5 |
| Pruebas | `pytest`, `httpx` | 9.2.0 / 0.28.1 |
| Despliegue | Docker / Docker Compose | Docker 29.4.3 / Compose v5.1.4 |

---

## 4. Modelado de datos y reglas de consentimiento

Entidades principales: `usuarios`, `configuraciones`, `ubicaciones`, `autorizaciones`,
`invitaciones` y `codigos_web`.

Reglas de seguridad implementadas (y verificadas con pruebas):

1. **Consentimiento explícito**: el botón del teclado usa
   `KeyboardButton(request_location=True)`, de modo que solo se comparte ubicación cuando el
   usuario pulsa y envía su posición. No hay captura automática.
2. **Doble consentimiento para consultar a terceros**: para ver la ubicación de otro usuario el
   backend exige **autorización `activa`** *y* `configuracion.compartir_ubicacion = true` del
   propietario. Si falta cualquiera de las dos, la respuesta es `403`. Detener la compartición
   oculta los datos de inmediato sin borrarlos.
3. **Relación pendiente hasta que el propietario acepta**: el canje de una invitación crea una
   autorización en estado `pendiente`; solo al aceptarla se vuelve `activa`.
4. **Invitaciones aleatorias, de un solo uso y con caducidad**: códigos de 8 caracteres
   generados con `secrets`, con fecha de expiración; reutilizar o canjear un código caducado
   falla.
5. **Identidad web por JWT vinculada a `telegram_id`**: `/web` genera un código de un solo uso
   que se canjea por un JWT cuyo `sub` es el `telegram_id`; el frontend solo envía el token, no
   credenciales de Telegram.
6. **Solo el propietario revoca**: `DELETE /api/authorizations/{id}` solo lo ejecuta quien creó
   la relación (probado con `403` para terceros).
7. **Sin secretos en código ni en logs**: la configuración sale de variables de entorno
   (`.env`), los mensajes de error no filtran tokens o contraseñas y el manejador global no
   imprime trazas internas.

---

## 5. Comandos del bot

| Comando | Función |
|---|---|
| `/start`, `/menu` | Registro/ bienvenida y menú principal con teclado personalizado |
| `/vincular` | Genera o explica el flujo de invitación para vincular contactos |
| `/compartir` | Activa o desactiva la compartición de ubicación |
| `/mis_ubicaciones` | Muestra las últimas ubicaciones registradas del usuario |
| `/contactos` | Lista contactos vinculados |
| `/permisos` | Muestra y gestiona permisos de autorización |
| `/detener` | Detiene la compartición (oculta datos a terceros) |
| `/ayuda` | Ayuda general y límites del sistema |
| `/web` | Genera el código de un solo uso para entrar al panel web |
| `/telefono` | (Opcional) captura opcional del teléfono declarado por el usuario |

El teclado principal incluye `KeyboardButton(request_location=True)`: la ubicación **solo** se
envía cuando el usuario pulsa ese botón.

---

## 6. API REST

| Método y ruta | Propósito | Auth |
|---|---|---|
| `GET /api/health` | Estado del servicio, la base de datos y el bot | No |
| `POST /api/auth/token` | Canjea el código `/web` por un JWT | Código de un solo uso |
| `GET /api/users/me` | Identidad del usuario autenticado | JWT |
| `GET /api/users` | Listado (búsqueda de contactos) | JWT |
| `GET/POST/DELETE /api/authorizations` | Consultar, crear y revocar permisos | JWT |
| `POST /api/invitations` | Crear invitación | JWT |
| `GET /api/locations/me` | Ubicaciones propias | JWT |
| `GET /api/locations/shared` | Ubicaciones de contactos autorizados | JWT + doble consentimiento |
| `GET /api/locations/history/{id}`, `/latest/{id}` | Historial y última ubicación | JWT + doble consentimiento |
| `GET/PUT /api/config/sharing` | Estado y conmutador de compartición | JWT |

El CORS se limita al origen del panel y las rutas de datos exigen token; sin él la respuesta es
`401` y sin permiso vigente `403`.

---

## 7. Pruebas

Se ejecutaron dos suites reales. Ambos resultados provienen de ejecuciones completas de
`pytest` en este proyecto:

| Suite | Entorno | Comando | Resultado |
|---|---|---|---|
| Suite completa con SQLite | Contenedor `bot-backend` (imagen ya construida) | `docker run --rm bot-backend pytest -q` | **53 superadas, 2 omitidas** (55 recolectadas, 13.73 s) |
| Suite completa con PostgreSQL | Pila levantada (`backend` + `postgres`) | `docker compose exec backend pytest -q` | **55 superadas** (10.44 s) |
| *E2E* de extremo a extremo por API | Pila levantada | Script interno contra `backend:8000` | **13/13 pasos correctos** |

Las 2 omitidas corresponden a `tests/test_postgres.py` en la suite SQLite: solo se ejecutan
cuando hay `TEST_DATABASE_URL` apuntando a PostgreSQL (en esa suite sí se ejecutaron y
pasaron). Ninguna prueba está marcada como fallida.

Desglose por archivo (resultado de la ejecución real con SQLite, 51 recolectadas):

| Archivo de pruebas | Casos | Resultado (SQLite) | Resultado (PostgreSQL) |
|---|---|---|---|
| `test_authorizations.py` | 10 | 10 superadas | 10 superadas |
| `test_bot.py` | 8 | 8 superadas | 8 superadas |
| `test_health_and_auth.py` | 8 | 8 superadas | 8 superadas |
| `test_invitations.py` | 10 | 10 superadas | 10 superadas |
| `test_locations.py` | 11 | 11 superadas | 11 superadas |
| `test_postgres.py` | 2 | 2 omitidas | 2 superadas |
| `test_users.py` | 6 | 6 superadas | 6 superadas |
| **Total** | **55** | **53 superadas + 2 omitidas** | **55 superadas** |

Qué cubren, en concreto:

- **Usuarios**: registro, no duplicados por `telegram_id`, actualización de datos visibles,
  `/api/users/me` con token ausente (`401`), válido e inválido.
- **Invitaciones**: creación, unicidad de códigos, canje a autorización `pendiente`, un solo
  uso, caducidad, no encontrada, auto-vinculación rechazada y sus endpoints API.
- **Ubicaciones**: registro, coordenadas inválidas rechazadas, precisión opcional nula,
  endpoints propios, y **todos los escenarios de permiso**: sin autorización (`403`), con
  autorización (`200`), tras revocar (`403`), con compartición detenida (`403`), propietario
  consultando siempre lo suyo, y retención (`purge_older_than`).
- **Autorizaciones**: creación idempotente, revocación solo por el propietario, listado con
  ambos roles, y errores de la API (sin vínculo previo, revocar la de otro, autorizarse a sí
  mismo).
- **Salud y autenticación**: `/api/health` con BD, flujo completo `/web` → token, código de un
  solo uso, código inválido y caducado, configuración de compartición, `shared` vacío para
  usuario nuevo, `history`/`latest` con datos nulos.
- **Bot**: construcción de la aplicación con todos los handlers, teclado del menú con
  `request_location=True`, texto de ayuda que documenta los límites, y recepción de ubicación
  usando un **`telegram.Location` real** de python-telegram-bot, con precisión informada
  (`horizontal_accuracy`) y sin precisión (guardada como `None`, no inventada). Estas
  pruebas se añadieron como **regresión** tras detectar en pruebas manuales con Telegram real
  dos fallos: el uso de `location.accuracy` (atributo inexistente en PTB 22.x, ver §13.10) y
  el envío de botones inline con `localhost` (Telegram los rechaza con `wrong http url`,
  §13.10).

---

## 8. Verificación del despliegue

Además de `pytest`, se verificó manualmente el despliegue con `docker compose up --build`
(Docker 29.4.3 / Compose v5.1.4):

| Verificación | Resultado observado |
|---|---|
| `docker compose up --build` | 3 servicios (`postgres`, `backend`, `frontend`) levantados |
| `GET /api/health` directo | `{"status":"ok","database":"ok","bot":"running"}` con `TELEGRAM_BOT_TOKEN` configurado (antes de configurarlo: `bot:"disabled"`) |
| `GET /api/health` vía proxy del frontend | `200` en `http://localhost:3000/api/health` |
| `GET /docs` (Swagger) | `200` |
| `GET /` (panel) | `200` |
| `GET /api/users/me` sin token | `401` |
| Logs del backend | `Polling de Telegram activo` + `Application started` sin errores |
| `pytest` en la pila (PostgreSQL) | 55 superadas |
| Envío real de ubicación desde Telegram | Detectó el fallo `location.accuracy` (§13.10); tras corregir y reconstruir la imagen, se repitió la prueba manual |
| Botones «Consultar mapa»/«Historial» en el chat real | Detectó el rechazo de `localhost` por Telegram (§13.10); corregido: el enlace se envía como texto con aviso en el arranque |
| *E2E* por API (registro → `/web` → invitación → pendiente `403` → ubicación → autorizar → `shared`/`history` `200` → detener → revocar → `403` → revocar como tercero `403` → `health` con PostgreSQL) | **13/13 pasos correctos** |

---

## 9. Decisiones de seguridad y sus justificaciones

| Decisión | Justificación |
|---|---|
| Consentimiento por botón explícito de Telegram | Evita cualquier rastreo silencioso; el usuario ve y confirma cada envío |
| Doble consentimiento (autorización activa **y** compartición activada) | El propietario puede cortar el acceso sin revocar relaciones, y nadie ve datos sin permiso vigente |
| JWT con `sub = telegram_id` | Vincula la sesión web a la identidad de Telegram sin almacenar contraseñas ni exponer el token de bot |
| Códigos `/web` e invitaciones de un solo uso con caducidad | Reduce la ventana de abuso si un código se filtra |
| Polling dentro del *lifespan* de FastAPI | Un solo proceso y un solo bucle `asyncio`; sin procesos externos que supervisar |
| Puerto 5432 no publicado + red interna | La base de datos solo es accesible desde la red de Compose |
| CORS restringido al origen del panel | Impide que otros sitios web consuman la API con la sesión del usuario |
| Configuración solo por variables de entorno | Ningún secreto en el repositorio; `.env.example` documenta las claves necesarias |

---

## 10. Limitaciones conocidas

- **Sin migraciones de esquema**: se usa `Base.metadata.create_all` en el arranque; si los
  modelos cambian sobre una base existente hay que recrearla (o añadir Alembic).
- **Corrección tras prueba manual con Telegram real**: el primer envío de ubicación falló en
  vivo porque el código usaba `location.accuracy`, atributo **inexistente** en
  `python-telegram-bot` 22.x (el correcto es `horizontal_accuracy`). Se corrigió en
  `app/bot/handlers.py` y se añadieron dos pruebas de regresión que usan un
  `telegram.Location` real (§13.7). Lección: las pruebas previas pasaban porque doblaban el
  objeto en lugar de usar la clase real de la librería.
- **Corrección tras prueba manual con Telegram real (botones inline)**: «Consultar mapa» e
  «Historial» fallaban con `BadRequest: wrong http url` porque el Bot API de Telegram **rechaza
  `localhost`** en los botones de URL inline. Se añadió `app/utils/urls.py` para validar la
  URL; si no es apta (local o sin esquema http/https), el enlace se envía **como texto** en el
  mensaje y el arranque emite un aviso. Para ver botones en el chat hay que definir
  `FRONTEND_URL` con una URL pública (p. ej. un túnel HTTPS). Pruebas de regresión en §13.7.
- **Una ubicación activa a la vez**: el MVP conserva el histórico completo, pero la visualización
  «en vivo» es la última posición recibida.
- **Retención por purga**: los datos se eliminan según la política configurada; no hay
  cifrado en reposo a nivel de aplicación (se delega al motor de PostgreSQL).
- **Anonimato geográfico de OpenStreetMap**: la precisión del mapa depende del servicio público
  de teselas, sin SLA.

---