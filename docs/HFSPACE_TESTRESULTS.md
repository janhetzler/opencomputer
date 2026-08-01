## 2026-08-01 09:32-09:33 UTC -- 6/6 OK, manueller Testlauf

**Umgebung:** HF Space, Dockerfile Commit 70d995b6 (tini, netcat, neue Startreihenfolge)
**Gestartet:** manuell im cptr-Terminal (`python3 /tmp/start_hfspace.py`)
**Dauer:** ~85 Sekunden (Start bis Testergebnis)

### Testergebnisse

| Agent | Status | Zeit | Anmerkung |
|-------|--------|------|-----------|
| Supervisor Routing | OK | - | language=English -> meta |
| Comms Agent | OK | 21.3s | 845 Zeichen |
| Code Agent | OK | 6.9s | 293 Zeichen (heuristic -> comms, aber Antwort korrekt) |
| Researcher Agent | OK | 28.3s | 42 Zeichen (max Tool-Runden erreicht) |
| Notes Agent | OK | 12.0s | save_note OK, ChromaDB cosine |
| Handoff Agent | OK | 6.2s | 713 Zeichen |

**Tests: 6/6 OK**

### Phoenix Spans

19 Spans erfasst (alle OK):
- 9x ChatOpenAI
- 5x search_local_documents
- 1x save_note

### Auffaelligkeiten

- Phoenix :6006 TIMEOUT beim Start (40 Retries) -- aber Tracing funktioniert trotzdem
- Port-Check zeigt doppelte FAIL/OK Zeilen (cosmetic bug im Pre-Flight)
- Code Agent: heuristic routing -> comms statt code, Antwort aber korrekt
- Researcher: max Tool-Runden (5x search_local_documents, dann Abbruch)

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
