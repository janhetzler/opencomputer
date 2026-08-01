---
type: Runbook
status: current
updated_at: 2026-08-01
stale_after: 2026-10-01
environment: hfspace
components: [llama-server, litellm, phoenix, fastapi, cptr]
---
# OPERATIONS_HFSPACE.md -- Betrieb & Logging (HF Space)

**Umgebung:** HuggingFace Space (Docker, Free Tier)
**Zuletzt aktualisiert:** 2026-08-01
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

---

## cptr-Verbindung konfigurieren

Einstellungen → Verbindungen → "la":
- Anbieter: OpenAI
- API-Typ: Chat-Vervollstaendigungen
- Basis-URL: `http://127.0.0.1:4000/v1`
- API-Key: `sk-cos-local-dev`

---

## Changelog

| Datum | Version | Aenderung |
|-------|---------|-----------|
| 2026-08-01 | v1 | Initial -- HF Space Betrieb dokumentiert |
