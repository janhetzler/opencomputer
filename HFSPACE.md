# HFSPACE.md -- HF Space Konzept

Ziel: LA Stack auf einem Hugging Face Space Free Tier betreiben.

Neuester Eintrag oben.

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

### Auth-Loesung

Problem: cptr generiert beim Start einen zufaelligen Token -- manuelles
Nachschlagen in den Logs waere bei jeder Session noetig.

Loesung: Fester CPTR_STARTUP_TOKEN im Dockerfile (z.B. "la").
- Token ist immer bekannt
- Einmalig eingeben beim ersten Start der Session
- Kein Suchen in Logs

### Naechste Schritte

1. Dockerfile anpassen: CPTR_STARTUP_TOKEN setzen
2. LA Stack Installations-Skript fuer HF Space erstellen
3. Testen: Stack 2 parallel zu Stack 1 installieren und starten
