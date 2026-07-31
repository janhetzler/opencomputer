# HFSPACE.md -- HF Space Konzept

Ziel: LA Stack auf einem Hugging Face Space Free Tier betreiben.

Neuester Eintrag oben.

---

## Logs, Traces und Testergebnisse -- wo landet was

### Laufzeit (ephemer -- nur waehrend Container laeuft)

| Pfad | Inhalt |
|------|--------|
| `/tmp/logs/` | llama-server, LiteLLM, Phoenix, Agent Server Logs |
| `/tmp/chroma_la/` | ChromaDB Daten |
| `/tmp/traces/` | Phoenix Trace Reports (JSON) |
| `/tmp/test_results_hfspace.json` | Letzter Testlauf Rohdaten |

Diese Dateien sind ephemer -- verschwinden beim Container-Stop.
Relevante Ergebnisse muessen ins Repo gepusht werden.

### Repo (persistent -- bleibt erhalten)

| Datei | Inhalt |
|-------|--------|
| `docs/HFSPACE_TESTRESULTS.md` | Alle Testlaeufe mit Ergebnissen und Traces |
| `docs/traces/` | Detaillierte Phoenix Trace Reports pro Testlauf |
| `BUGS.md` | Fehlerprotokoll |
| `JOURNAL.md` | Entwicklungstagebuch |

### Ablage-Regel

Nach jedem Testlauf:
1. Testergebnisse in `docs/HFSPACE_TESTRESULTS.md` ergaenzen
2. Phoenix Trace Report nach `docs/traces/YYYY-MM-DD_testlauf.json` pushen
3. JOURNAL.md Eintrag wenn etwas Neues passiert ist

---

## Dateiuebersicht -- Was liegt wo, was tut was

Alle relevanten Dateien fuer den HF Space Betrieb auf einen Blick.
Hier nachschauen wenn etwas geaendert werden muss.

### Dockerfile (Root)
**Zweck:** Image-Build -- definiert was zur Build-Zeit passiert.
**Aendern wenn:** neue Pakete, neues Modell, neue ENV-Variable,
EXPOSE-Ports aendern, start.sh anpassen.

### /usr/local/bin/start.sh (wird im Dockerfile inline definiert)
**Zweck:** Laufzeit-Startskript -- wird bei jedem Container-Start ausgefuehrt.
**Aendern wenn:** Stack-1 oder Stack-2 Startparameter aendern,
neue Komponente hinzufuegen, Reihenfolge aendern.
**Achtung:** Liegt nicht als eigene Datei im Repo -- ist inline im Dockerfile.

### scripts/hfspace/start_hfspace.py
**Zweck:** Stack-2-Start (LA Agent Stack) + 6-Agenten-Testlauf +
Phoenix Trace inline. Wird von start.sh aufgerufen.
**Aendern wenn:** Ports aendern, neue Agenten, Testlauf anpassen,
inspect-Logik aendern, ENV-Variablen ergaenzen.
**Umgebungsvariablen:** LA_REPO, LLAMA_SERVER_BIN, MODEL_PATH,
EMBED_MODEL_PATH, LLAMA_PORT, EMBED_PORT, CHROMA_PATH, LITELLM_KEY

### scripts/hfspace/inspect_phoenix_hfspace.py
**Zweck:** Separates Diagnose-Skript -- Phoenix Traces manuell auslesen
ohne vollen Testlauf. Fuer gezielte Diagnose im Terminal.
**Aendern wenn:** Trace-Format aendern, andere Ports, andere Ausgabepfade.
**Hinweis:** Setzt laufenden Stack voraus -- Pre-Flight-Check prueft das.

### docs/HFSPACE_TESTRESULTS.md
**Zweck:** Testergebnisse aller HF Space Testlaeufe.
**Aendern wenn:** Nach jedem Testlauf -- wird von start_hfspace.py
automatisch aktualisiert (Push via GH_TOKEN) oder manuell ergaenzt.

### HFSPACE.md (dieses Dokument)
**Zweck:** Konzept, Plan, Dateiuebersicht, Entscheidungen.
**Aendern wenn:** Neue Erkenntnisse, Planänderungen, Phase-2-Schritte
abgehakt werden.

---

## 2026-07-31 -- Produktionsreifer Dockerfile-Plan

### Was heute im Hottest validiert wurde

4x 6/6 Agenten OK. Phoenix Tracing: 73 Spans ausgelesen.
Ein Befehl, ein Terminal, vollautomatisch (start_hfspace.py c796f94).

### Plan: Alles zur Build-Zeit

Kein manueller Setup mehr nach Container-Start. Alles was moeglich
ist kommt in die Build-Phase des Dockerfile.

**Build-Zeit (RUN Bloecke -- einmalig beim Image-Build):**

1. Python 3.11 als Default -- bereits drin
2. LA Repo klonen nach /home/varxdev/la
   (oeffentliches Repo -- kein Token noetig)
3. virtualenv anlegen: /home/varxdev/la_env (Python 3.11)
4. requirements.txt aus LA Repo ins venv installieren
5. Granite-350m Q4_K_M herunterladen nach /data/models/
   (oeffentliches GitHub Release -- kein Token noetig)
6. Granite-Embedding-30m Q4_0 herunterladen nach /data/models/
   (oeffentliches GitHub Release -- kein Token noetig)
7. Verzeichnisse anlegen: /tmp/logs, /tmp/chroma_la, /tmp/traces

**Laufzeit (start.sh -- bei jedem Container-Start):**

1. Stack 1: llama-server :8080 (Granite-Tiny) starten
2. Stack 1: cptr :7860 starten
3. Stack 2: start_hfspace.py im Hintergrund starten
   (venv aktivieren, LA_REPO=/home/varxdev/la)
4. wait -- haelt beide Stacks am Leben

**EXPOSE:**
EXPOSE 7860 8080 8090 8081 4000 6006 8002

### Umgebungsvariablen

Alle haben sinnvolle Defaults -- kein manuelles Setzen noetig:

| Variable | Default | Zweck |
|----------|---------|-------|
| LA_REPO | /home/varxdev/la | Pfad zum LA Repo |
| LLAMA_SERVER_BIN | /opt/llama/llama-server | Binary-Pfad |
| LLAMA_PORT | 8090 | LA llama-server Port |
| EMBED_PORT | 8081 | Embedding-Server Port |
| MODEL_PATH | /data/models/granite-350m-Q4_K_M.gguf | Reasoning-Modell |
| EMBED_MODEL_PATH | /data/models/granite-embedding-30m-Q4_0.gguf | Embedding-Modell |

Kein GH_TOKEN noetig -- alle Repos und Releases sind oeffentlich.

### Noch offen (Phase 2)

- CPTR_STARTUP_TOKEN: fester Token fuer cptr Login
- Automatische cptr-Konfiguration via REST API (LA Agent Server verbinden)

---

## 2026-07-31 -- Umgebungs-Check Ergebnisse

### Festgestellte Umgebung im HF Space Terminal

- Python 3.10.12
- pip 22.0.2 -- KEIN --break-system-packages (Option nicht vorhanden in pip 22)
- Disk: 1.7T total, 328G frei (HF Space shared storage)
- RAM: 123 GB angezeigt -- real 16 GB (bekannter HF Space Anzeigebug)
- curl, git, wget vorhanden
- llama-server b9895 bereits unter /opt/llama/llama-server
- Bereits installiert: fastapi, httpx, uvicorn
- Fehlen noch: langchain, chromadb, litellm, phoenix, arize-phoenix

### Konsequenz fuer Installation

pip install OHNE --break-system-packages verwenden:
  pip3 install --quiet -r la/requirements.txt

llama-server muss NICHT neu installiert werden -- bereits vorhanden.

---

## 2026-07-31 -- Konzept definiert

### Umgebung

- Hugging Face Space Free Tier (ephemer -- kein persistenter Storage)
- 2 vCPU (Xeon virtualisiert), 16 GB RAM
- Jede Session baut den Stack komplett neu auf

### Weboberfläche

- cptr (opencomputer) stellt eine Weboberfläche bereit
- Ohne cptr: nur Terminal ODER Web -- nicht beides gleichzeitig
- Mit cptr: vollstaendige Weboberfläche inkl. Terminal-Zugang

### Stack-Aufbau

Zwei unabhaengige Stacks laufen parallel im selben Container:

**Stack 1 -- cptr + llama-server (bereits im Dockerfile)**
- cptr Weboberfläche: Port 7860
- llama-server mit Granite-Tiny Q4_K_XL: Port 8080
- Wird nicht veraendert

**Stack 2 -- LA Sandbox (neu, analog zur Claude-Sandbox)**
- llama-server mit Granite-350m: Port 8090
- Embedding-Server mit Granite-Embedding-30m: Port 8081
- LiteLLM: Port 4000
- Phoenix: Port 6006
- Agent Server: Port 8002
- Identischer Aufbau wie die bekannte Sandbox -- llama-server-Start entfaellt nicht

### Ports

Alle Ports sind getrennt -- kein Konflikt zwischen Stack 1 und Stack 2.
Zwei llama-server-Instanzen im selben Container sind kein Problem.

HF Space DNS-Routing: Jeder per EXPOSE freigegebene Port ist direkt
im Browser erreichbar -- z.B.:
- janhetzler-opencomputer-7860.hf.space  (cptr)
- janhetzler-opencomputer-6006.hf.space  (Phoenix)
- janhetzler-opencomputer-4000.hf.space  (LiteLLM)

Dockerfile EXPOSE muss entsprechend erweitert werden:
EXPOSE 7860 8080 8090 8081 4000 6006 8002

### Auth-Loesung

Problem: cptr generiert beim Start einen zufaelligen Token -- manuelles
Nachschlagen in den Logs waere bei jeder Session noetig.

Loesung: Fester CPTR_STARTUP_TOKEN im Dockerfile (z.B. "la").
- Token ist immer bekannt
- Einmalig eingeben beim ersten Start der Session
- Kein Suchen in Logs

### Automatische cptr-Konfiguration via REST API

Problem: Nach jedem Neustart muss die Verbindung zu llama-server
manuell im Setup-Dialog eingegeben werden (Base-URL, API-Key, Modell).

Loesung: Ein Setup-Skript das automatisch nach dem cptr-Start laeuft
und die Konfiguration per REST API eintraegt.

- Endpunkt: chat.connections via cptr Admin REST API
- Base-URL: http://127.0.0.1:8080/v1
- API-Key: local
- Das Skript wird Teil von start.sh im Dockerfile
- Ablauf: cptr starten -> warten bis API bereit -> Verbindung per REST API setzen

Vorteil: cptr ist sofort nach dem Start betriebsbereit -- kein manueller
Setup-Dialog, keine Konfiguration von Hand.

### Naechste Schritte

1. Dockerfile anpassen: CPTR_STARTUP_TOKEN setzen + EXPOSE erweitern
2. Setup-Skript implementieren: cptr REST API Verbindungskonfiguration
3. LA Stack Installations-Skript fuer HF Space erstellen
4. Testen: Stack 2 parallel zu Stack 1 installieren und starten
