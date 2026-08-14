---
title: "LA Stack mit cptr als Frontend: Aufbau und Betrieb"
type: Runbook
status: current
updated_at: 2026-08-14
stale_after: 2027-02-14
environment: hfspace
components: [cptr, litellm, phoenix, fastapi, llama-server, chromadb]
---

# LA Stack mit cptr als Frontend: Aufbau und Betrieb

Dieses Dokument beschreibt wie der LA Agent Stack auf dem HF Space
mit cptr als Frontend betrieben wird. Erarbeitet und verifiziert
am 2026-08-14.

Verwandte Dokumentation:
- [OPERATIONS_HFSPACE.md](OPERATIONS_HFSPACE.md)
- [CPTR_CONFIG_API.md](CPTR_CONFIG_API.md)

---

## Architektur

```
Browser
  -> cptr :7860 (Frontend -- janhetzler/opencomputer)
    -> LiteLLM :4000
      -> Agent Server :8002 (Supervisor + 6 Agenten)
        -> llama-server :8080 (Granite-Tiny 4B, --jinja)
        -> llama-server :8090 (Granite-350m, Reserve)
        -> Embedding :8081 (Granite-Embedding-30m)
        -> ChromaDB /tmp/chroma_la
        -> Phoenix :6006 (Tracing)
```

Stack 1 (cptr + Granite-Tiny) startet automatisch via Docker start.sh.
Stack 2 (LA Agent Stack) wird manuell gestartet via la_stack.sh.

---

## Voraussetzungen

Docker Container laeuft mit start.sh -- folgende Ports bereits aktiv:

| Port | Dienst | Modell |
|------|--------|--------|
| 7860 | cptr | -- |
| 8080 | llama-server Stack 1 | Granite-Tiny 4B |
| 8090 | llama-server Stack 2 | Granite-350m |
| 8081 | Embedding-Server | Granite-Embedding-30m |

Verzeichnisse anlegen (einmalig):

```sh
mkdir -p /tmp/pids /tmp/logs /tmp/chroma_la
```

---

## LA Stack starten

```sh
. /home/varxdev/la_env/bin/activate && \
curl -sL \
  "https://raw.githubusercontent.com/janhetzler/opencomputer/main/scripts/hfspace/la_stack.sh" \
  -o /tmp/la_stack.sh && \
chmod +x /tmp/la_stack.sh && \
sh /tmp/la_stack.sh start
```

Das Skript startet der Reihe nach:
1. Prueft Voraussetzungen (:8090, :8081)
2. Phoenix :6006
3. LiteLLM :4000 (mit Config auf :8080)
4. Agent Server :8002 (mit mcp.json)
5. Startet chat.py fuer Terminal-Test

PIDs werden gesichert unter /tmp/pids/.

---

## cptr als Frontend konfigurieren

Nach dem Stack-Start cptr einmalig konfigurieren:

```sh
. /home/varxdev/la_env/bin/activate && \
python3 /home/varxdev/la/scripts/hfspace/cptr_setup.py
```

Oder direkt von GitHub:

```sh
curl -sL \
  "https://raw.githubusercontent.com/janhetzler/opencomputer/main/scripts/hfspace/cptr_setup.py" \
  | python3
```

Dieses Skript:
- Biegt cptr Connection auf LiteLLM :4000 um
- Konfiguriert mcp_git und mcp_fetch als Tool-Server

---

## Modell wechseln

Standard: Granite-Tiny :8080 (empfohlen -- Tool-Calling funktioniert)
Fallback: Granite-350m :8090 (leichter, kein Tool-Calling)

```sh
# Auf Granite-Tiny wechseln (Standard)
python3 scripts/hfspace/cptr_litellm_switch.py 8080

# Auf Granite-350m wechseln
python3 scripts/hfspace/cptr_litellm_switch.py 8090
```

---

## Stack stoppen

```sh
sh /tmp/la_stack.sh stop
```

Oder direkt:

```sh
sh scripts/hfspace/cptr_kill_stack.sh
```

Wichtig: pkill -f verwenden, nicht kill via PID-Datei.
Hintergrund: Alle Prozesse sind Kindprozesse von cptr (os.fork).
Siehe BUG-007 in BUGS.md.

---

## Status pruefen

```sh
sh scripts/hfspace/cptr_port_status.sh
```

Oder:

```sh
sh /tmp/la_stack.sh status
```

---

## ChromaDB pruefen

```sh
. /home/varxdev/la_env/bin/activate && \
python3 scripts/hfspace/chroma_inspect.py
```

Zeigt alle Collections und gespeicherten Dokumente.

---

## Testergebnisse (2026-08-14, Granite-Tiny)

| Agent | Ergebnis |
|-------|---------|
| Supervisor | OK -- vollstaendige Uebersicht aller Agenten |
| Comms | OK -- Email korrekt generiert |
| Code | OK -- Python Funktion korrekt |
| Notes | OK -- "The note has been saved successfully" |
| Handoff | OK -- Prompt vorbereitet |
| Researcher | FAIL -- sucht in ChromaDB statt Git (BUG-027) |

Notes Agent Verifikation via chroma_inspect.py bestaetigt:
Eintrag korrekt in ChromaDB gespeichert.

---

## Vergleich Modelle

| Funktion | Granite-350m | Granite-Tiny (4B) |
|----------|-------------|------------------|
| Supervisor | "Hello!" | Vollstaendige Uebersicht |
| Notes speichern | Maximale Tool-Runden | Saved successfully |
| Email schreiben | Einfach | Strukturiert |
| RAM | ~34 MB | ~4.3 GB |
| Tool-Calling | Unzuverlaessig | Funktioniert |

---

## cptr Funktionen im Frontend-Betrieb

Alle folgenden cptr-Funktionen sind mit LA als Backend nutzbar:

| Funktion | Status | Hinweis |
|----------|--------|---------|
| Chat | OK | agent-local Modell |
| Datei anhangen | OK | Wird an Agent Server weitergeleitet |
| Planungsmodus | OK | Zeigt Plan vor Ausfuehrung |
| Tool-Berechtigung | OK | auto/ask/full konfigurierbar |
| Parameter | OK | Temperature, max_tokens pro Chat |
| MCP Tools (cptr) | Konfiguriert | mcp_git (12 Tools), mcp_fetch |
| Skills | Nicht benoetigt | LA Stack uebernimmt |
| Memory | Nicht benoetigt | ChromaDB uebernimmt |

---

## Skripte (alle unter scripts/hfspace/)

| Skript | Zweck |
|--------|-------|
| `la_stack.sh` | Stack start/stop/status + chat.py |
| `cptr_setup.py` | cptr Connection + MCP konfigurieren |
| `cptr_config_read.py` | Config, Connections, Tool Server auslesen |
| `cptr_litellm_switch.py` | Modell-Backend wechseln |
| `cptr_kill_stack.sh` | Stack sauber stoppen |
| `cptr_port_status.sh` | Port Status aller Komponenten |
| `cptr_db_export.py` | cptr SQLite DB exportieren |
| `chroma_inspect.py` | ChromaDB Inhalte pruefen |

---

## Offene Punkte

- Researcher Agent: prompts/agents/researcher.md anpassen
  damit mcp_git fuer Repo-Inhalte genutzt wird
- Dockerfile anpassen: la_stack.sh automatisch beim Start ausfuehren
- cptr Connection-ID hardcodiert -- bei Neuinstallation pruefen

---

## Changelog

| Datum | Version | Aenderung |
|-------|---------|-----------|
| 2026-08-14 | v1 | Initial -- LA Stack + cptr Frontend verifiziert |
