# HFSPACE.md -- HF Space Konzept

Ziel: LA Stack auf einem Hugging Face Space Free Tier betreiben.

Neuester Eintrag oben.

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
