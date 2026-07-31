# HFSPACE_TESTRESULTS.md -- HF Space Testergebnisse

## 2026-07-31 -- Erster vollstaendiger Testlauf

### Kontext

Erster erfolgreicher LA Stack Testlauf auf HF Space Free Tier.
Stack 2 (LA) laeuft parallel zu Stack 1 (cptr + Granite-Tiny).

### Commits

- start_hfspace.py: `8fc7f4c` (mcp-server-git Pfad-Bug Fix)
- Dockerfile: Python 3.11 als Default (`1b6a57c`)

### Stack-Konfiguration

| Komponente       | Port | Details                                      |
|------------------|------|----------------------------------------------|
| llama-server     | 8090 | Granite-350m Q4_K_M, /opt/llama/llama-server |
| Embedding-Server | 8081 | Granite-Embedding-30m Q4_0                   |
| LiteLLM          | 4000 | Proxy auf Port 8090                          |
| Phoenix          | 6006 | Tracing aktiv                                |
| Agent Server     | 8002 | FastAPI, alle 6 Agenten geladen              |

- venv: `/home/varxdev/la_env` (Python 3.11.0rc1)
- LA Repo: `/home/varxdev/la`
- mcp.json: laufzeit-generiert nach `/tmp/mcp_hfspace.json`

### Testergebnisse -- Testlauf 1 (2026-07-31T16:48:18)

| Agent             | Status | Antwortlaenge | Zeit   | HTTP |
|-------------------|--------|---------------|--------|------|
| Supervisor Routing| OK     | 65 Zeichen    | 7.6s   | 200  |
| Comms Agent       | OK     | 560 Zeichen   | 13.6s  | 200  |
| Code Agent        | OK     | 293 Zeichen   | 6.9s   | 200  |
| Researcher Agent  | OK     | 83 Zeichen    | 1.2s   | 200  |
| Notes Agent       | OK     | 58 Zeichen    | 15.2s  | 200  |
| Handoff Agent     | OK     | 702 Zeichen   | 7.8s   | 200  |

**Gesamt: 6/6 OK**

### Testergebnisse -- Testlauf 2 (2026-07-31T17:48:01) nach mcp-Bug Fix

| Agent             | Status | Antwortlaenge | Zeit   | HTTP |
|-------------------|--------|---------------|--------|------|
| Supervisor Routing| OK     | 65 Zeichen    | 7.6s   | 200  |
| Comms Agent       | OK     | 478 Zeichen   | 10.6s  | 200  |
| Code Agent        | OK     | --            | 3.8s   | 200  |
| Researcher Agent  | OK     | 42 Zeichen    | 27.4s  | 200  |
| Notes Agent       | OK     | 58 Zeichen    | 15.1s  | 200  |
| Handoff Agent     | OK     | 652 Zeichen   | 6.6s   | 200  |

**Gesamt: 6/6 OK**

### Bekannte Einschraenkungen

- inspect_phoenix.py nicht HF-Space-kompatibel: sucht
  `/tmp/llama-b9895/llama-server` (Sandbox-Pfad) -- wird uebersprungen
- Researcher Agent: mcp-server-git wirft intern Fehler aber Antwort
  kommt trotzdem (ExceptionGroup wird abgefangen)
- 350m Modell: Routing-Limitierung bekannt, heuristic layer uebernimmt

### Naechste Schritte

- inspect_phoenix.py fuer HF Space anpassen (LLAMA_SERVER_BIN ENV)
- Automatischen Stack-Start ins Dockerfile integrieren
- CPTR_STARTUP_TOKEN im Dockerfile setzen


---

# HF Space Trace Report -- 2026-07-31_18-25

**Tests:** 6/6 OK

## Testergebnisse

- OK **Supervisor Routing**: OK (65 Zeichen) | 7.5s | HTTP 200
- OK **Comms Agent**: OK (492 Zeichen) | 11.2s | HTTP 200
- OK **Code Agent**: OK (293 Zeichen) | 3.8s | HTTP 200
- OK **Researcher Agent**: OK (42 Zeichen) | 25.4s | HTTP 200
- OK **Notes Agent**: OK (58 Zeichen) | 15.3s | HTTP 200
- OK **Handoff Agent**: OK (655 Zeichen) | 7.1s | HTTP 200

## Phoenix Spans

```
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  save_note | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  save_note | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  save_note | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  search_local_documents | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms
  ChatOpenAI | OK | ?ms

```
