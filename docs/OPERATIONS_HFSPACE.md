---
type: Runbook
status: current
updated_at: 2026-08-14
stale_after: 2026-10-14
environment: hfspace
components: [llama-server, litellm, phoenix, fastapi, cptr]
---
# OPERATIONS_HFSPACE.md -- Betrieb & Logging (HF Space)

**Umgebung:** HuggingFace Space (Docker, Free Tier)
**Zuletzt aktualisiert:** 2026-08-14
**Verwandt:** OPERATIONS_DOCKER.md (la Repo)

---

## Uebersicht: Alle Komponenten

| Komponente | Port | Log-Datei | Status |
|------------|------|-----------|--------|
| llama-server (Reasoning) | 8090 | `/tmp/logs/llama-server-la.log` | manuell gestartet |
| llama-server (Embedding) | 8081 | `/tmp/logs/llama-server-embed-la.log` | manuell gestartet |
| Phoenix | 6006 | `/tmp/logs/phoenix-la.log` | manuell gestartet |
| LiteLLM | 4000 | `/tmp/logs/litellm-la.log` | manuell gestartet |
| Agent Server | 8002 | (stdout von start_hfspace.py) | manuell gestartet |
| cptr | 7860 | (Docker start.sh) | automatisch |
| Granite-Tiny | 8080 | (Docker start.sh) | automatisch |

**Log-Verzeichnis:** `/tmp/logs/` (nicht persistent -- geht beim Container-Neustart verloren)

> **Wichtig:** Im HF Space laufen zwei Stacks parallel:
> Stack 1 (cptr + Granite-Tiny :8080) startet automatisch via start.sh.
> Stack 2 (LA Agent Stack) muss manuell gestartet werden (siehe unten).

---

## Stack starten (manuell)

```bash
cd /home/varxdev/la
MODEL_PATH=/data/models/granite-350m-Q4_K_M.gguf \
EMBED_MODEL_PATH=/data/models/granite-embedding-30m-Q4_0.gguf \
nohup python3 /tmp/start_hfspace.py > /tmp/logs/la_start.log 2>&1 &
echo "PID: $!"
```

`nohup` haelt den Stack am Leben auch wenn das Terminal geschlossen wird.
`start_hfspace.py` wird beim Start frisch von GitHub gezogen (immer aktuell).

---

## Stack-Diagnose

```bash
bash /home/varxdev/la/scripts/hfspace/inspect_stack_hfspace.sh
```

Oder direkt im cptr-Terminal ausfuehren. Gibt Port-Status, Prozesse
und die letzten Log-Zeilen aller Komponenten aus.

---

## Komponenten im Detail

### llama-server Reasoning (:8090)

**Modell:** `/data/models/granite-350m-Q4_K_M.gguf`
**Log:** `/tmp/logs/llama-server-la.log`

```bash
tail -20 /tmp/logs/llama-server-la.log
curl -s http://localhost:8090/v1/models
```

### llama-server Embedding (:8081)

**Modell:** `/data/models/granite-embedding-30m-Q4_0.gguf`
**Log:** `/tmp/logs/llama-server-embed-la.log`

```bash
tail -10 /tmp/logs/llama-server-embed-la.log
```

### LiteLLM (:4000)

**Log:** `/tmp/logs/litellm-la.log`
**API-Key:** `sk-cos-local-dev`

```bash
tail -30 /tmp/logs/litellm-la.log
curl -s http://localhost:4000/health -H "Authorization: Bearer sk-cos-local-dev"
```

**Bekannte Fehler:**
- `Connection error.. Model Group=agent-local` -- llama-server :8090 nicht erreichbar
- `Available Model Group Fallbacks=None` -- kein Fallback konfiguriert (erwartet)

### Phoenix (:6006)

**Log:** `/tmp/logs/phoenix-la.log`
**Web-UI:** Im cptr-Browser nicht darstellbar (React-heavy, WebSocket-Konflikt).
Traces werden per Python Client ausgelesen (start_hfspace.py).

```bash
curl -s http://localhost:6006/v1/projects
```

### Agent Server (:8002)

```bash
curl -s http://localhost:8002/health
curl -s -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-cos-local-dev" \
  -d '{"model":"agent-local","messages":[{"role":"user","content":"hello"}],"max_tokens":100}'
```

### cptr (:7860)

Startet automatisch via Docker start.sh. Verbindung "la" zeigt auf
LiteLLM :4000 (`http://127.0.0.1:4000/v1`).

**Datendateien:**

| Datei | Inhalt |
|-------|--------|
| `/home/varxdev/.cptr/app.db` | SQLite DB (WAL-Modus) |
| `/home/varxdev/.cptr/app.db-shm` | WAL Shared Memory |
| `/home/varxdev/.cptr/app.db-wal` | WAL Log |
| `/home/varxdev/.cptr/config.toml` | JWT Secret + App-Config Mirror |

---

## cptr -- Verbindung konfigurieren (via REST API)

Verbindung per Script setzen (kein manueller Setup-Dialog noetig):

```python
import urllib.request, json, http.cookiejar

BASE = "http://localhost:7860"
CONN_ID = "33597f72-5ec3-4c56-9e00-e28b7884cb44"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"username":"user","password":"12345678"}).encode(),
    headers={"Content-Type":"application/json"}
))

# provider_type auf llama.cpp setzen
update = {"provider_type": "llama.cpp", "api_key": "local"}
req = urllib.request.Request(
    f"{BASE}/api/admin/connections/{CONN_ID}",
    data=json.dumps(update).encode(),
    headers={"Content-Type":"application/json"},
    method="PUT"
)
resp = opener.open(req)
print("Update:", resp.status, resp.read().decode())
```

Connections auslesen:

```python
resp = opener.open(urllib.request.Request(f"{BASE}/api/admin/connections"))
print(json.dumps(json.loads(resp.read()), indent=2))
```

---

## cptr -- Logging aktivieren

cptr-Logging wird ausschliesslich ueber Umgebungsvariablen konfiguriert.
In `start.sh` vor dem `cptr run` Aufruf setzen:

```sh
# Audit-Logging auf METADATA-Level aktivieren
CPTR_AUDIT_LOG_LEVEL=METADATA \
CPTR_AUDIT_LOG_PATH=/home/varxdev/.cptr/logs/audit.jsonl \
cptr run --host 0.0.0.0 --port 7860 &
```

Audit-Level:
- `NONE` -- kein Logging (Default)
- `METADATA` -- Method, Path, Status, User, IP
- `REQUEST` -- + Request Body (sensitive Felder redaktiert)
- `REQUEST_RESPONSE` -- + Response Body

Upstream-Requests (Anfragen an das Modell) loggen:

```sh
CPTR_LOG_UPSTREAM_REQUESTS=true \
CPTR_UPSTREAM_REQUEST_LOG_PATH=/home/varxdev/.cptr/logs/upstream.jsonl \
cptr run --host 0.0.0.0 --port 7860 &
```

Alle Logging-Variablen: [CPTR_CONFIG_API.md](CPTR_CONFIG_API.md)

---

## cptr -- DB Export

Vollstaendigen DB-Export erzeugen:

```bash
python3 /home/varxdev/la/scripts/hfspace/cptr_db_export.py
ls /tmp/cptr_export/
```

Exportiert alle Tabellen als JSON nach `/tmp/cptr_export/`.
Script: [scripts/hfspace/cptr_db_export.py](../scripts/hfspace/cptr_db_export.py)

---

## cptr-Verbindung konfigurieren (manuell via UI)

Einstellungen → Verbindungen → "la":
- Anbieter: OpenAI
- API-Typ: Chat-Vervollstaendigungen
- Basis-URL: `http://127.0.0.1:4000/v1`
- API-Key: `sk-cos-local-dev`

---

## Changelog

| Datum | Version | Aenderung |
|-------|---------|-----------| 
| 2026-08-14 | v2 | cptr Logging, DB Export, REST API Skripte ergaenzt |
| 2026-08-01 | v1 | Initial -- HF Space Betrieb dokumentiert |
