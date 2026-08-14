## 2026-08-14 -- cptr als Frontend verifiziert, Granite-Tiny aktiv

### Ergebnis

cptr laeuft als vollstaendiges Frontend fuer den LA Agent Stack.
Modell gewechselt von Granite-350m (:8090) auf Granite-Tiny (:8080) --
deutlich bessere Qualitaet bei Tool-Calling und Antworten.

### Testergebnisse mit Granite-Tiny (4B)

| Test | Ergebnis |
|------|---------|
| Supervisor "Hi, what can you do?" | OK -- vollstaendige strukturierte Antwort |
| Notes Agent "Save this note: ..." | OK -- "The note has been saved successfully" |
| ChromaDB Verifikation | OK -- Eintrag korrekt gespeichert |
| Comms Agent Statusmail | OK -- vollstaendige Email generiert |
| Researcher "Was steht in ROADMAP?" | FAIL -- sucht in ChromaDB statt Git (bekannt) |

### Vergleich 350m vs Granite-Tiny

| Funktion | 350m | Granite-Tiny |
|----------|------|-------------|
| Supervisor Routing | "Hello!" | Vollstaendige Uebersicht aller Agenten |
| Notes speichern | "Maximale Tool-Runden" | "Saved successfully" |
| ChromaDB Inhalt | Nur Dateiname | Vollstaendiger Text |
| Comms Email | Einfach | Strukturiert mit Bullet Points |

### LiteLLM Config Aenderung

granite-tiny api_base von :8090 auf :8080 umgestellt.
Neustart via pkill -f (nicht PID) -- heute gelernt und bewaehrt.

### Offene Punkte

- Researcher muss prompts/agents/researcher.md angepasst werden
  damit er mcp_git fuer Repo-Inhalte nutzt statt ChromaDB
- Dockerfile anpassen fuer automatischen Stack-Start
- la_stack.sh ins la Repo pushen (aktuell nur in opencomputer)

---

## 2026-08-14 -- LA Stack live, cptr als Frontend konfiguriert

### Erledigte Aenderungen

- LA Stack manuell hochgezogen (Phoenix, LiteLLM, Agent Server)
- PIDs gesichert unter /tmp/pids/ (phoenix.pid, litellm.pid, agent-server.pid)
- Logs unter /tmp/logs/ (phoenix.log, litellm.log, agent-server.log)
- cptr Connection auf LiteLLM :4000 umgebogen (war: Granite-Tiny :8080)
- MCP Server in cptr konfiguriert: mcp_git, mcp_fetch (mcp_stdio, la_env Python)
- mcp_git verifiziert: 12 Tools gefunden, Verbindung OK
- cptr_db_export.py ins Repo gepusht (scripts/hfspace/)
- CPTR_CONFIG_API.md vollstaendig (Config-Keys, DB-Schema, Logging ENV, Laufzeit)

### Stack-Status

Alle Komponenten laufen:

| Komponente | Port | PID-Datei |
|------------|------|-----------|
| llama-server (Granite-Tiny) | 8080 | via start.sh |
| llama-server (350m) | 8090 | via start.sh |
| Embedding-Server | 8081 | via start.sh |
| Phoenix | 6006 | /tmp/pids/phoenix.pid |
| LiteLLM | 4000 | /tmp/pids/litellm.pid |
| Agent Server | 8002 | /tmp/pids/agent-server.pid |
| cptr | 7860 | via start.sh |

cptr Frontend: verbunden mit LiteLLM :4000 (agent-local Modell)
MCP Tools: mcp_git (12 Tools), mcp_fetch -- beide aktiv in cptr

### Erkenntnisse

- PIDs IMMER sofort sichern -- alle Prozesse sind Kindprozesse von cptr (os.fork)
  Ohne PID-Datei ist gezieltes Kill sehr schwer (BUG-007)
- /tmp/pids/ und /tmp/logs/ muessen VOR dem Start angelegt werden
- MCP Server laufen als mcp_stdio -- werden von cptr bei Bedarf gestartet
  Python-Pfad muss absolut sein: /home/varxdev/la_env/bin/python3
- Phoenix healthz endpoint: /healthz (nicht /health)
- LiteLLM braucht ~15s zum Hochfahren -- nicht zu frueh testen

### Offene Punkte

- cptr Connection umbiegen noch nicht ausgefuehrt (Script bereit)
- Dockerfile anpassen sobald alles live verifiziert ist
- Gesamtes Start-Prozedere als Script ablegen

---

# JOURNAL.md -- Entwicklungstagebuch opencomputer

Fork von: open-webui/computer
Zweck: GUI + API Gateway fuer den Local Agent Stack (la)

Neuester Eintrag oben.

## 2026-08-01 -- HF Space Stack live, Researcher/Code Agent 500er

### Erledigte Aenderungen

- Dockerfile (70d995b6): start.sh Reihenfolge -- cptr erst nach nc -z 8002,
  Granite-Tiny zuletzt
- start_hfspace.py: Cleanup-Block entfernt, litellm_proc.wait() ergaenzt --
  Stack bleibt nach Testlauf am Leben
- Modellwechsel erfolgreich getestet: LA Stack auf Granite-Tiny :8080 umgebogen
  (Config-Aenderung in /tmp/litellm_hfspace.yaml, kein Neustart noetig)

### Stack-Status

cptr (v0.9.20) laeuft auf :7860, agent-local Verbindung konfiguriert
(http://127.0.0.1:4000/v1). Basisanfragen funktionieren.

### Offene Bugs

**Researcher + Code Agent werfen 500er** bei bestimmten Anfragen:
- `ExceptionGroup: unhandled errors in a TaskGroup` im Agent Server Log
- LiteLLM sieht Internal Server Error von :8002, retried 2x, gibt auf
- Tritt mit Granite-Tiny genauso auf wie mit 350m -- kein Modellproblem
- Phoenix und Inspect wurden beim Debugging nicht eingesetzt -- Fehlerursache
  noch unbekannt
- Dokumentiert als BUG-027 in janhetzler/la

### Erkenntnisse

- Testlauf (6/6 OK) war strukturell falsch -- "Maximale Tool-Runden erreicht"
  wurde als OK gewertet. Researcher hat nie wirklich funktioniert.
- Phoenix Tracing und Inspect muessen beim naechsten Debugging-Anlauf
  systematisch eingesetzt werden statt schrittweiser Log-Analyse
- Testlauf muss ueberarbeitet werden (BUG-027)

---

## 2026-08-01 -- Aktueller Dockerfile-Stand (Testversion)

start.sh laeuft mit cptr + beiden llama-servern (:8090, :8081).
start_hfspace.py (LA Stack) ist auskommentiert -- cptr startet
ohne Warteloop auf Port 8002.

```sh
# Auskommentiert (noch nicht aktiv):
# python3 /tmp/start_hfspace.py
# while ! nc -z localhost 8002; do sleep 0.5; done
```

Naechster Schritt (noch offen): Einkommentieren wenn LA Stack
automatisch beim Docker-Start hochkommen soll.

---

## 2026-08-01 -- 6/6 auf neuem Dockerfile bestaetigt

Manueller Testlauf 09:32-09:33 UTC -- 6/6 OK.
Neues Dockerfile: tini als PID 1, netcat Readiness-Checks,
korrekte Startreihenfolge (350m zuerst, Granite-Tiny zuletzt).
19 Phoenix Spans erfasst.

### Offene Untersuchung

- **Port-Routing im HF Space:** Subdomain-Schema
  `https://janhetzler-mytest2-6006.hf.space` funktioniert nicht
  fuer interne Ports (Phoenix :6006, LiteLLM :4000 etc.).
  `/proxy/PORT/` Schema funktioniert nur fuer VS Code / Jupyter.
  Muss untersucht werden wie interne Ports von aussen erreichbar
  gemacht werden koennen.

### Naechster Schritt

- start_hfspace.py in start.sh einkommentieren + ENV-Variablen
  exportieren fuer vollautomatischen Start beim Container-Start.

## 2026-07-31 -- 6/6 auch unter erschwerten Bedingungen

Testlauf 21:36 UTC -- 6/6 OK trotz 20 Zombie-Prozessen und knappem RAM.
19 Phoenix Spans. Alle Agenten stabil.

Erkenntnisse des Tages:
- Zombies entstehen weil cptr (PID 8) als Parent keine wait() aufruft
- Loesung fuer Zukunft: tini als PID 1 im Dockerfile
- LiteLLM Timeout-Problem: Granite-Tiny zuerst killen, dann LA Stack starten
- prisma fehlt in LA requirements.txt -- Workaround: cptr installiert es mit
- cptr Admin API vollstaendig dokumentiert (connections, users, config, tools)
- cptr Login: POST /api/auth/login, user/12345678, Cookie in /tmp/cptr_cookies.txt

---

## Offene Aenderungen (Todo)

- **Dockerfile:** Granite-Tiny llama-server (:8080) ans Ende von start.sh
  verschieben -- nach start_hfspace.py Aufruf, vor wait. Verhindert
  RAM-Engpass beim Start (16GB real auf HF Space Free Tier).

- **start_hfspace.py:** LiteLLM Timeout von 40 auf 90 Sekunden erhoehen.

- **janhetzler/la requirements.txt:** prisma ergaenzen (async_timeout bereits vorhanden)
- **Dockerfile Reihenfolge:** cptr zuerst installieren, dann LA requirements.txt --
  cptr zieht viele Abhaengigkeiten mit die LiteLLM benoetigt (inkl. prisma moeglicherweise)
- **tini als PID 1 im Dockerfile:** tini verhindert Zombie-Prozesse automatisch.
  Ursache: Python/Uvicorn als PID 1 raeumen verwaiste Kindprozesse nicht auf.
  Fix: apt-get install -y tini + ENTRYPOINT ["/usr/bin/tini", "--"]
  Quelle: Open WebUI Entwicklerangaben, verifiziertes Problem mit Subprozessen.
  (fehlen im Docker Build, wurden beim manuellen Test automatisch
  als Abhaengigkeit von LiteLLM installiert).

---

## 2026-07-31 -- Phoenix Tracing + Ein-Befehl-Skript

- 4x 6/6 Testlaeufe bestaetigt
- Phoenix Tracing: 73 Spans ausgelesen, alle OK
- save_note und search_local_documents korrekt getracet
- start_hfspace.py integriert inspect_phoenix inline --
  ein Befehl, ein Terminal, alles automatisch (c796f94)
- HFSPACE_TESTRESULTS.md aktualisiert mit vollstaendigem Trace-Report

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