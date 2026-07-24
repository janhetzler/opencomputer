# JOURNAL.md -- Entwicklungstagebuch opencomputer

Fork von: open-webui/computer
Zweck: GUI + API Gateway fuer den Local Agent Stack (la)

Neuester Eintrag oben.

---

## 2026-07-24 -- Fork erstellt, Konzept definiert

### Kontext

Dieser Fork von `open-webui/computer` (cptr) wird als GUI und
API-Gateway fuer den Local Agent Stack eingesetzt.

### Warum opencomputer

- FastAPI + Python -- gleiche Technologie wie der LA Stack
- Vollstaendig automatisierbar via REST API
- MCP (Stdio + HTTP) nativ unterstuetzt
- Eingebauter /v1 API-Gateway ersetzt LiteLLM
- Terminal, Git, Dateiverwaltung direkt im Browser

### Geplante Integration mit dem LA Stack

1. Agent Server :8002 als OpenAPI Tool-Server in opencomputer
2. MCP-Server (git, fetch) als mcp_stdio Tool-Server
3. Phoenix Tracing direkt im Agent Server (nicht via LiteLLM)
4. llama-server Binary direkt angebunden (kein LiteLLM)

### Aktueller Stand

- Fork erstellt: 2026-07-24
- Granite-Tiny (4B) laeuft bereits mit --jinja + Tool-Calling bewiesen
- Naechster Schritt: LA Stack Integration

### Verwandte Repos

- LA Stack Repository -- Agent Stack
- `open-webui/computer` -- Original-Projekt
