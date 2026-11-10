# Ubicación Compartida — MVP (Bot de Telegram + Web)

Sistema académico que permite **compartir de forma voluntaria** la ubicación geográfica de
usuarios mediante un bot de Telegram y visualizarla desde un panel web con mapa.

> **Nota ética y legal.** El sistema **no** rastrea personas, **no** obtiene el GPS en
> segundo plano y **no** localiza números telefónicos arbitrarios. La ubicación solo se
> registra cuando el propio usuario la envía desde Telegram, y solo se entrega a terceros
> cuando el propietario ha otorgado un consentimiento explícito que puede revocar en
> cualquier momento. El uso de este material es exclusivamente académico.

---

## 1. Introducción

### 1.1 Problema que busca resolver

Compartir la posición de un dispositivo entre personas que se conocen (familia, equipo de
trabajo, grupos de actividades) requiere mecanismos que sean a la vez **sencillos** y
**respetuosos con la privacidad**: cada persona debe saber quién puede ver su ubicación,
cuándo y cómo puede retirar ese permiso.

### 1.2 Objetivo general

Desarrollar un MVP funcional que registre usuarios a través de un bot de Telegram, permita
la vinculación voluntaria entre cuentas, reciba y almacene ubicaciones enviadas por sus
propietarios y las muestre en un mapa web únicamente cuando exista autorización vigente.

### 1.3 Objetivos específicos

1. Registrar usuarios por su `telegram_id` sin duplicar registros.
2. Vincular usuarios mediante códigos de invitación aleatorios, de un solo uso y con caducidad.
3. Recibir coordenadas enviadas explícitamente por el usuario con el botón de ubicación de
   Telegram (`KeyboardButton(request_location=True)`).
4. Almacenar latitud, longitud, precisión (cuando exista) y fecha/hora en PostgreSQL.
5. Exponer una API REST con autenticación basada en tokens y validación de permisos.
6. Visualizar las ubicaciones autorizadas y su historial en un mapa con Leaflet/OpenStreetMap.
7. Permitir la revocación de autorizaciones y la detención de la compartición.
8. Asegurar el despliegue local mediante Docker Compose.

### 1.4 Alcance del MVP

- Bot de Telegram con registro, vinculación, envío de ubicación y gestión de permisos.
- Backend FastAPI con API REST documentada (Swagger UI).
- Base de datos PostgreSQL con seis entidades relacionadas.
- Panel web React con mapa, historial y gestión de autorizaciones.
- Pruebas automatizadas con `pytest`.
- Despliegue local con Docker Compose (backend + frontend + PostgreSQL).

### 1.5 Limitaciones

- La ubicación **solo** se actualiza cuando el usuario envía una nueva posición: no hay
  rastreo continuo ni en segundo plano.
- No existe aplicación móvil nativa ni integración con APIs de localización del sistema
  operativo.
- No se pueden localizar números telefónicos: Telegram no ofrece esa capacidad a los bots.
- La autenticación web usa códigos de un solo uso emitidos por el bot (apropiada para un MVP,
  no sustituye a un sistema de identidad robusto en producción).
- La retención de datos se documenta, pero no hay un proceso programado de purga.

---

## 2. Tecnologías

| Tecnología | Función en el proyecto |
|---|---|
| **Python 3.12** | Lenguaje del backend y del bot. |
| **python-telegram-bot 22.8** | Interacción con la API de Telegram en modo *polling*. |
| **FastAPI 0.162** | API REST, validación de datos y documentación automática (Swagger UI). |
| **SQLAlchemy 2.1** | ORM: modelos, relaciones y consultas a la base de datos. |
| **PostgreSQL 16** | Almacenamiento persistente de usuarios, autorizaciones y ubicaciones. |
| **PyJWT 2.15** | Firma y validación de los tokens JWT del panel web. |
| **pydantic / pydantic-settings** | Esquemas de entrada/salida y configuración por variables de entorno. |
| **React 19 + Vite 8** | Panel web moderno y rápido (compilación de producción). |
| **React Router 7** | Navegación entre secciones del panel. |
| **React Leaflet 5 + Leaflet 1.9** | Mapa interactivo incrustado. |
| **OpenStreetMap** | Teselas del mapa sin necesidad de claves API. |
| **Nginx** | Servidor estático del frontend y proxy inverso `/api` → backend. |
| **Docker / Docker Compose** | Empaquetado y orquestación reproducible del entorno. |
| **pytest** | Pruebas automatizadas del backend. |

---

## 3. Arquitectura

```mermaid
flowchart LR
    subgraph Usuario
        U[Usuario de Telegram]
        N[Navegador web]
    end

    subgraph Contenedores_Docker
        BOT[Bot de Telegram<br/>python-telegram-bot<br/>modo polling]
        API[Backend FastAPI<br/>routers + servicios]
        DB[(PostgreSQL<br/>usuarios, autorizaciones,<br/>ubicaciones)]
        WEB[Frontend React<br/>Vite + Nginx]
    end

    MAPA[Leaflet + OpenStreetMap<br/>teselas del mapa]

    U -- "mensajes y ubicación" --> BOT
    BOT -- "mismo proceso / bucle asyncio" --> API
    U -- "código /web → JWT" --> WEB
    WEB -- "HTTP + JSON (/api)" --> API
    API -- "SQLAlchemy" --> DB
    WEB -- "teselas tile.openstreetmap.org" --> MAPA
```

### 3.1 Cómo se comunican los componentes

1. **Usuario ↔ Bot**: el usuario envía comandos y mensajes de texto, y comparte su
   ubicación con el botón nativo de Telegram. El bot consulta y escribe en la base de datos
   a través de los mismos servicios que la API.
2. **Bot ↔ Backend**: no hay red entre ambos: el bot se ejecuta **dentro del proceso de
   FastAPI**. Se inicializa en el *lifespan* de FastAPI y usa `start_polling()`, por lo que
   no se requiere dominio público, webhook ni un contenedor aparte.
3. **Frontend ↔ Backend**: el panel consume la API REST (`/api/...`) con HTTP y JSON. En
   producción, Nginx (contenedor `frontend`) hace de proxy y redirige `/api` a
   `backend:8000`.
4. **Frontend ↔ OpenStreetMap**: Leaflet descarga únicamente las teselas visibles desde
   `tile.openstreetmap.org` y muestra la atribución obligatoria.
5. **Backend ↔ PostgreSQL**: el backend se conecta al **nombre del servicio** `postgres`
   dentro de la red de Docker Compose (nunca a `localhost`).

---

## 4. Estructura de carpetas

```text
Bot/
├── back/                        # Backend (FastAPI + bot de Telegram)
│   ├── app/
│   │   ├── main.py              # Aplicación FastAPI, CORS y ciclo de vida del bot
│   │   ├── config.py            # Configuración por variables de entorno
│   │   ├── database.py          # Motor, sesión y base declarativa de SQLAlchemy
│   │   ├── models/              # Modelos ORM (usuarios, invitaciones, autorizaciones, …)
│   │   ├── schemas/             # Esquemas Pydantic de entrada y salida
│   │   ├── routers/             # Endpoints REST agrupados por recurso
│   │   ├── services/            # Lógica de negocio (validaciones y permisos)
│   │   ├── bot/                 # Aplicación PTB, manejadores, teclados y textos
│   │   └── utils/               # Seguridad (JWT), fechas, excepciones y dependencias
│   ├── tests/                   # Pruebas automatizadas con pytest
│   ├── requirements.txt         # Dependencias de producción (versiones fijadas)
│   ├── requirements-dev.txt     # Dependencias de prueba
│   ├── pytest.ini               # Configuración de pytest
│   ├── Dockerfile               # Imagen del backend (multi-propósito)
│   └── .dockerignore
├── front/                       # Panel web (React + Vite)
│   ├── src/
│   │   ├── components/          # Componentes reutilizables (mapa, tablas, tarjetas…)
│   │   ├── pages/               # Pantallas: login, mapa, historial, autorizaciones…
│   │   ├── services/api.js      # Cliente HTTP con manejo de JWT y errores
│   │   ├── hooks/               # useAuth y useResource
│   │   ├── styles/              # Hojas de estilo
│   │   ├── App.jsx              # Rutas protegidas
│   │   └── main.jsx             # Punto de entrada
│   ├── public/                  # Estáticos (favicon)
│   ├── package.json             # Dependencias (versiones fijadas)
│   ├── vite.config.js           # Configuración de Vite y proxy de desarrollo
│   ├── Dockerfile               # Build multi-stage + Nginx
│   ├── nginx.conf               # Proxy /api → backend:8000
│   └── .dockerignore
├── docker-compose.yml           # Orquestación de los tres servicios
├── .env.example                 # Plantilla de variables de entorno
├── .gitignore                   # Excluye .env, node_modules, cachés, etc.
├── README.md                    # Este documento
└── bot.md                       # Documento técnico para el informe académico
```

---

## 5. Requisitos previos

| Requisito | Observaciones |
|---|---|
| **Docker Desktop** (o Docker Engine + Compose v2) | Permite ejecutar el proyecto con un solo comando. |
| **Cuenta de Telegram** | Para interactuar con el bot desde el móvil o la web de Telegram. |
| **Bot creado con [@BotFather](https://t.me/BotFather)** | Se obtiene el token necesario. |
| (Opcional) **Node.js ≥ 20.19** | Solo si desea ejecutar el frontend en modo desarrollo (`npm run dev`). |
| (Opcional) **Python ≥ 3.11** | Solo si desea ejecutar las pruebas fuera de Docker. |

### 5.1 Cómo obtener el token del bot

1. En Telegram, abra **@BotFather** y envíe `/newbot`.
2. Elija un nombre y un nombre de usuario (debe terminar en `bot`).
3. BotFather responderá con un token de la forma `123456789:AAH-...`.
4. Copie ese token en `TELEGRAM_BOT_TOKEN` dentro del archivo `.env`.

> El token es una credencial: **no lo suba al repositorio**. Si se filtra, genere uno nuevo
> con `/revoke` en BotFather.

---

## 6. Configuración

```bash
# 1. Entre a la carpeta del proyecto
cd Bot

# 2. Cree el archivo de entorno a partir de la plantilla
    Linux/macOS:  cp .env.example .env
    Windows:      copy .env.example .env

# 3. Edite .env y complete:
    - TELEGRAM_BOT_TOKEN=<token de BotFather>
    - POSTGRES_PASSWORD=<una contraseña propia>
    - JWT_SECRET_KEY=<clave aleatoria, p. ej. python -c "import secrets; print(secrets.token_urlsafe(48))">
    El resto de variables tienen valores aptos para el entorno local.
```

| Variable | Descripción |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot. Vacío = el sistema arranca **sin bot** (solo API y web). |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Credenciales de la base de datos. |
| `JWT_SECRET_KEY` | Clave para firmar los JWT del panel. Vacío = secreto efímero (solo desarrollo). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia de la sesión web (60 min por defecto). |
| `WEB_CODE_EXPIRE_MINUTES` | Caducidad del código `/web` (5 min). |
| `INVITATION_EXPIRE_MINUTES` | Caducidad de los códigos `/vincular` (15 min). |
| `CORS_ORIGINS` | Orígenes permitidos para el navegador (separados por coma). |
| `FRONTEND_URL` | URL del panel que el bot ofrece como enlace. Debe ser **pública** para que Telegram muestre botones clicables (rechaza `localhost`; en local el enlace se envía como texto). |
| `LOCATION_RETENTION_DAYS` | Días de retención de ubicaciones (política documentada en §9). |
| `VITE_API_URL` | Vacío en Docker (Nginx hace de proxy). Defina `http://localhost:8000` solo para `npm run dev`. |

---

## 7. Ejecución

### 7.1 Con Docker Compose (recomendado)

```bash
cd Bot

docker compose build        # construye las imágenes (la primera vez tarda unos minutos)
docker compose up -d        # levanta los tres servicios
docker compose ps           # comprueba el estado (deben figurar "healthy")
docker compose logs -f backend   # sigue los registros del backend y del bot
docker compose down         # detiene los servicios (los datos se conservan)
```

También puede ejecutar todo en un solo paso: `docker compose up --build -d`.

### 7.2 Verificación

```bash
# Estado de los servicios
docker compose ps

# Salud del backend (también se puede abrir en el navegador)
curl http://localhost:8000/api/health

# El frontend debe responder con el HTML del panel
curl -I http://localhost:3000

# El proxy de Nginx debe responder la API desde el puerto del frontend
curl http://localhost:3000/api/health
```

Respuesta esperada de `/api/health`:

```json
{ "status": "ok", "database": "ok", "bot": "disabled", "timestamp": "2026-01-01T12:00:00Z" }
```

- `database: "ok"` → PostgreSQL responde.
- `bot: "running"` → el bot está conectado a Telegram (requiere token válido).
- `bot: "disabled"` → no hay token configurado o el bot no pudo iniciar.
- `bot: "error"` → el backend funciona, pero el bot no pudo arrancar (revise el token).

### 7.3 URLs de acceso

| Servicio | URL |
|---|---|
| Frontend (panel) | http://localhost:3000 |
| Backend (API) | http://localhost:8000 |
| Swagger UI (documentación) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/health |
| PostgreSQL | **No publicado** (solo accesible desde la red interna de Compose) |

### 7.4 Ejecución sin Docker (opcional)

```bash
# Backend
cd Bot/back
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
set DATABASE_URL=postgresql+psycopg2://usuario:clave@localhost:5432/location_mvp   # PowerShell
uvicorn app.main:app --reload

# Frontend
cd Bot/front
npm install
npm run dev        # http://localhost:5173 (proxea /api a localhost:8000)
```

---

## 8. Uso del sistema

### 8.1 Iniciar el bot

1. Levante los servicios (`docker compose up -d`).
2. En Telegram, busque el nombre de usuario de su bot y abra la conversación.
3. Compruebe `docker compose logs backend`: debe aparecer
   *«Bot de Telegram iniciado en modo polling»*.

### 8.2 Registrar un usuario

```
/start
```

El bot responde con la bienvenida y el menú principal. Si el usuario ya existía, solo lo
reconoce (no duplica el registro).

### 8.3 Generar una invitación (usuario A)

```
/vincular
```

Respuesta: código de 8 caracteres, válido durante 15 minutos y de un solo uso, por ejemplo

```
🔗 Invitación generada
Código: K7M2P9QD
```

### 8.4 Vincular otro usuario (usuario B)

```
/start
/vincular K7M2P9QD
```

- Se crea la relación entre ambos usuarios con estado **pendiente**.
- El bot notifica a A con los botones **✅ Autorizar** / **❌ Rechazar**.
- Solo cuando A pulsa *Autorizar* la autorización pasa a **activa**.

### 8.5 Compartir una ubicación

```
/compartir
```

El bot envía un teclado con el botón **«📍 Enviar mi ubicación actual»**
(`KeyboardButton(request_location=True)`). Al enviarlo, Telegram muestra el selector nativo
y solo transmite las coordenadas si el usuario lo confirma.

Respuesta del bot:

```
✅ Ubicación recibida y almacenada
Latitud: 4.71100
Longitud: -74.07210
Precisión: 12.5 m
Fecha y hora (UTC): 2026-01-01T12:34:56Z
```

### 8.6 Iniciar sesión en el panel web

```
/web
```

El bot entrega un código de un solo uso (5 minutos). Introdúzcalo en
http://localhost:3000: el backend lo canjea por un JWT cuya identidad es su `telegram_id`.

### 8.7 Consultar una ubicación autorizada

- En el bot: `/contactos` muestra quién está vinculado y el estado de los permisos.
- En el panel: la sección **Mapa** dibuja su última posición (verde) y la de quienes lo
  autorizaron (azul), con nombre, coordenadas y fecha en cada marcador.

### 8.8 Consultar el historial

- Bot: `/mis_ubicaciones` resume su propio historial.
- Panel: **Historial** permite elegir un usuario y ver sus registros más recientes.
  Si no hay autorización vigente, la API responde `403` y el panel muestra el motivo.

### 8.9 Revocar permisos

- Bot: `/permisos` lista las autorizaciones con botones **🚫 Revocar**.
- Panel: sección **Autorizaciones** → botón **Revocar** de la fila correspondiente.
- El acceso deja de funcionar de inmediato (verificado por pruebas).

### 8.10 Detener la compartición

```
/detener
```

También desde el panel, sección **Mi ubicación** → **Detener compartición**. Mientras esté
detenida, el backend no entrega sus ubicaciones a terceros aunque existan autorizaciones
vigentes.

### 8.11 Comandos del bot

| Comando | Función |
|---|---|
| `/start` | Registra o reconoce al usuario. |
| `/menu` | Menú principal con botones. |
| `/vincular` | Genera un código de invitación. |
| `/vincular CODIGO` | Canjea un código recibido (vinculación). |
| `/compartir` | Solicita el envío de la ubicación actual. |
| `/mis_ubicaciones` | Resumen de sus ubicaciones y estado de compartición. |
| `/contactos` | Usuarios vinculados y permisos mutuos. |
| `/permisos` | Autorizaciones vigentes y botón de revocación. |
| `/detener` | Detiene la compartición de ubicación. |
| `/telefono` | Ofrece compartir el número (opcional, por botón de contacto). |
| `/web` | Genera el código de acceso al panel web. |
| `/ayuda` | Instrucciones de uso y límites del sistema. |

### 8.12 Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Estado del backend y de la base de datos. |
| POST | `/api/auth/token` | Canjea el código `/web` por un JWT. |
| GET | `/api/users/me` | Usuario autenticado (identidad del token). |
| GET | `/api/users` | Contactos vinculados y estado de permisos. |
| GET | `/api/authorizations` | Autorizaciones del usuario (rol y estado). |
| POST | `/api/authorizations` | Crea/reactiva una autorización (requiere vinculación). |
| DELETE | `/api/authorizations/{id}` | Revoca una autorización (solo el propietario). |
| GET | `/api/locations/me` | Historial propio. |
| GET | `/api/locations/shared` | Últimas ubicaciones compartidas conmigo. |
| GET | `/api/locations/history/{user_id}` | Historial autorizado (`403` sin permiso). |
| GET | `/api/locations/latest/{user_id}` | Última ubicación autorizada (`null` si no hay). |
| POST | `/api/invitations` | Genera un código de invitación. |
| GET | `/api/invitations` | Invitaciones emitidas. |
| GET/PUT | `/api/config` | Consulta o cambia el interruptor de compartición. |

Documentación interactiva en **http://localhost:8000/docs** (Swagger UI).

---

## 9. Autenticación y autorización

### 9.1 Cómo se obtiene la identidad

1. El usuario pide un código con `/web` **en Telegram** (eso demuestra que controla la cuenta).
2. El código es aleatorio, de un solo uso y caduca en 5 minutos; se almacena en la tabla
   `codigos_web`.
3. El panel envía el código a `POST /api/auth/token`; el backend lo valida, lo marca como
   utilizado y devuelve un **JWT** firmado cuyo campo `sub` es el `telegram_id`.
4. Cada petición protegida lleva `Authorization: Bearer <token>`; la dependencia
   `get_current_user` decodifica el token y carga el usuario **desde la base de datos**.

> **Esto no es un mecanismo de producción.** No hay segunda factor, ni recuperación de
> cuenta, ni lista negra de tokens: un JWT robado es válido hasta expirar. Es una
> demostración adecuada para un MVP académico, y así se documenta.

### 9.2 Validación de permisos

- El frontend **nunca** envía un `user_id` para decidir a quién puede consultar: la
  identidad sale del token firmado.
- Toda consulta de ubicaciones de terceros exige, en el **backend**:
  1. una `Authorization` con `estado = activa` entre el propietario y el consultante, y
  2. `configuracion.compartir_ubicacion = true` del propietario.
- Si falta cualquiera de las dos, la API responde `403` sin revelar si existen datos.
- Revocar una autorización o detener la compartición surte efecto inmediato.

### 9.3 Protección de datos

- Credenciales y token del bot solo en variables de entorno (`.env` excluido de Git).
- CORS restringido a los orígenes configurados (`CORS_ORIGINS`).
- Los logs no imprimen tokens, contraseñas ni coordenadas completas de terceros.
- Los errores inesperados responden `500` genérico; el detalle solo va a los registros.
- El teléfono se almacena únicamente si el usuario lo envía con el botón de contacto.
- **Retención:** se recomienda eliminar las ubicaciones con más de
  `LOCATION_RETENTION_DAYS` días. En el MVP existe la función
  `location_service.purge_older_than(db, days)` (probada en `test_purge_older_than…`),
  invocable desde una tarea programada o manualmente:

  ```sql
  DELETE FROM ubicaciones WHERE fecha_hora < NOW() - INTERVAL '30 days';
  ```

  O conservar solo la última posición por usuario:

  ```sql
  DELETE FROM ubicaciones u
  USING ubicaciones m
  WHERE u.usuario_id = m.usuario_id AND u.id < m.id;
  ```

---

## 10. Persistencia

- Los datos viven en el **volumen de Docker** `pgdata`, montado en
  `/var/lib/postgresql/data` del contenedor `postgres`.
- `docker compose down` **no** elimina los volúmenes: al volver a levantar, los usuarios,
  autorizaciones y ubicaciones siguen ahí.
- Para borrar **todo** el contenido (irreversible):

  ```bash
  docker compose down -v      # -v elimina el volumen pgdata
  ```

- Otra opción es eliminar solo el contenido sin borrar el volumen:

  ```bash
  docker compose exec postgres psql -U location_user -d location_mvp -c "TRUNCATE ubicaciones, autorizaciones, invitaciones, configuraciones, codigos_web, usuarios CASCADE;"
  ```

---

## 11. Licencia y uso académico

Material desarrollado para la asignatura **Mecanismos de Seguridad Informática**. Su uso es
académico y debe realizarse en entornos propios y aislados, con consentimiento expreso de
las personas cuyas ubicaciones se compartan. No se permite su empleo para el seguimiento de
personas sin autorización.
