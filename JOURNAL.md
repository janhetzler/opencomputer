# JOURNAL.md -- Entwicklungstagebuch opencomputer

Fork von: open-webui/computer
Zweck: GUI + API Gateway fuer den Local Agent Stack (la)

Neuester Eintrag oben.

---

## 2026-07-31 -- LA Stack auf HF Space: 2x 6/6 OK

Stack 2 (LA mit Granite-350m) laeuft parallel zu Stack 1
(cptr + Granite-Tiny) im selben Container. Zwei vollstaendige
Testlaeufe erfolgreich abgeschlossen.

**Commits heute:**
- Dockerfile: Python 3.11 als Default (`1b6a57c`)
- start_hfspace.py: mcp-server-git Pfad-Fix (`8fc7f4c`)
- HFSPACE_TESTRESULTS.md: Ergebnisse dokumentiert (`75d7dd9`)

**Testergebnisse:** siehe docs/HFSPACE_TESTRESULTS.md

**Offen:**
- inspect_phoenix.py HF-Space-kompatibel machen
- Automatischen Stack-Start ins Dockerfile integrieren

---

## 2026-07-31 -- HF Space Konzept erarbeitet

Konzept fuer den Betrieb des LA Stacks auf einem HF Space Free Tier definiert.
Details und Naechste Schritte: siehe [HFSPACE.md](HFSPACE.md)

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

### Ideen / Phase 2

- Eigenes cptr-Wheel aus dem Fork bauen und ueber GitHub Releases
  bereitstellen (analog PyPI, aber im eigenen Repo). Beschleunigt
  Docker-Builds gegenueber direkter Git-Installation. Paketname
  muss von "cptr" abweichen (z.B. cptr-la), da PyPI-Name belegt.

### Verwandte Repos

- LA Stack Repository -- Agent Stack
- `open-webui/computer` -- Original-Projekt
