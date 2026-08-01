# **Codebase-Analyse der Chat-Funktion, Prompt-Pipeline und Tool-Execution in open-webui/computer (cptr)**

Diese technische Recherche liefert eine datei- und zeilenbasierte Aufarbeitung des Repositories open-webui/computer (Paketname cptr). Entwicklerangaben und Quellcode-Analysen belegen, dass die Anwendung als modularer Agenten-Harness konzipiert ist1. Sie stellt eine vollständige Systemarbeitsstation mit Dateisystemzugriff, Terminal-Emulation, Git-Interaktion und Web-Browser-Automatisierung über eine verteilte Architektur bereit1.

## **1\. Input-Erfassung & Interface-Routing**

Die Systemarchitektur von cptr basiert im Backend auf dem FastAPI-Framework, dessen zentraler Anwendungsserver im Modul cptr/server.py instanziiert wird3. Der Server verknüpft voneinander isolierte Router-Module unter cptr/routers/, die eintreffende Anfragen segmentieren, validieren und an die internen Steuerungs- und Ausführungsschleifen weiterleiten3.

### **REST-API, Gateway-Endpoints und WebSocket-Handler**

Das Request-Routing gliedert sich primär in drei Kanäle: interaktive Weboberflächen-Anfragen, externe Gateway-Aufrufe und bidirektionale WebSocket-Verbindungen4. Das Modul cptr/routers/chat.py verarbeitet direkte Chat-Anfragen der nativen Benutzeroberfläche. Für Drittsysteme stellt das Modul cptr/routers/gateway.py eine standardisierte OpenAI-kompatible REST-Schnittstelle über den Endpoint /v1/chat/completions sowie eine Modellübersicht über /v1/models bereit4. Dadurch kann jeder in cptr definierte Workspace von externen Systemen wie Open WebUI als eigenständiges Agenten-Modell angesprochen werden1.  
Für die latenzarme Übertragung von Terminal-Outputs, Prozesszuständen und SSE-Events dient das Modul cptr/routers/ws.py, welches den Endpoint /ws steuert4. Entwicklerangaben zufolge bevorzugt die Verbindungslogik eine direkte WebSocket-Verbindung und fällt nur bei Netzwerkrestriktionen auf HTTP-Polling zurück4. Die dazugehörigen Client-State-Stores im Svelte-Frontend (unter cptr/frontend/src/lib/stores/socket.ts bzw. cptr/frontend/src/lib/api/chat.ts) verfügen über Re-Attachment-Mechanismen, die bei Verbindungsunterbrechungen Event-Verluste bei lang laufenden Agenten-Prozessen verhindern6.

| Endpoint / Pfad | Modul-Dateipfad | Ausführungslogik & Zweck |
| :---- | :---- | :---- |
| /v1/chat/completions | cptr/routers/gateway.py | Validiert Gateway-Keys (sk-cptr-...), übersetzt Chat-Completions-Anfragen und startet die Agenten-Schleife4. |
| /v1/models | cptr/routers/gateway.py | Fragt Datenbank-Workspaces ab und gibt diese als verfügbare OpenAI-Modelle zurück4. |
| /api/chat | cptr/routers/chat.py | Haupt-Endpoint für native Svelte-Frontend-Interaktionen und Chat-Erstellung4. |
| /ws | cptr/routers/ws.py | Verwaltet WebSocket-Sessions, bidirektionales Shell-Streaming und Event-Broadcasting4. |
| /api/audio/transcribe | cptr/routers/audio.py | Nimmt hochgeladene Audio-Dateien entgegen und leitet sie an STT-APIs weiter1. |

### **Audio-Verarbeitung und Speech-to-Text Pipeline**

Eingehende Audiodaten für Sprachnotizen ("Voice Memos") oder Diktatfunktionen werden im Backend über das Router-Modul cptr/routers/audio.py in Kombination mit der Hilfsklasse cptr/utils/audio.py verarbeitet1. Gemäß Quellcode-Spezifikation akzeptiert das System gängige Audio-Formate und leitet diese an eine konfigurierbare, OpenAI-kompatible Speech-to-Text (STT) Schnittstelle (wie Whisper oder Azure STT) weiter4.  
Die Konfigurationsparameter (Base URL, API-Key und Modell-Name) werden dynamisch aus den in der SQLite-Datenbank hinterlegten Admin-Einstellungen ausgelesen4. Nach erfolgreicher Transkription formatiert cptr/utils/audio.py den Text als strukturiertes Markdown und fügt dieses direkt in die Prompt-Eingabekette des aktiven Chat-Threads ein1.

### **Messaging-Integrationen und Workspace-Konsolidierung**

Die Anbindung externer Kommunikationsplattformen ist in spezialisierten Bot-Adaptern unter cptr/messaging/ bzw. cptr/routers/messaging.py verankert1. Eingehende Nachrichten aus Telegram, Discord, Slack, WhatsApp und Signal werden dort über platform-spezifische Webhooks oder Long-Polling-Handler empfangen1.  
Gemäß Entwicklerangaben zeichnet sich die Pipeline durch folgende verarbeitende Mechanismen aus:

* **Signal-Gruppen-Routing**: Im Signal-Bot-Adapter wird sichergestellt, dass Antworten, Tipp-Indikatoren und Anhänge explizit an die Gruppenadresse zurückgesendet werden, anstatt auf die Einzeladresse des Absenders zu verweisen4.  
* **Session- und Verlaufskonsolidierung**: Befehle wie /workspace oder /new erlauben das dynamische Umschalten des aktiven Arbeitsbereichs innerhalb des Chat-Threads1. Die Zusammenführung externer Nachrichten mit dem Workspace-Verlauf erfolgt im Modul cptr/db/chats.py. Vor dem Speichern bereinigt und vereinheitlicht cptr/utils/workspace.py alle Pfad- und Workspace-Identifikatoren, sodass plattformübergreifende Nachrichten lückenlos in derselben Konversationshistorie landen4.

## **2\. Prompt-Building & Kontext-Verarbeitung**

Die Prompt-Engine von cptr überführt unstrukturierte Benutzereingaben, System-Konfigurationen und Dateisystem-Artefakte in ein valides Kontext-Fenster für LLM-Provider.

### **System-Prompts, Prompt-Builder und Template-Injektion**

Das Erstellen des finalen System-Prompts wird zentral durch die Modullogik in cptr/agent/prompt.py über die Builder-Klasse PromptBuilder abgewickelt1. Der Prozess folgt einer strikten dreistufigen Hierarchie:

> 1. **Globaler System-Prompt**: Definiert Basisanweisungen bezüglich Werkzeugverfügbarkeit, Terminalregeln und Antwortformate1.  
> 2. **Modell-spezifischer System-Prompt**: Injiziert modellspezifische Besonderheiten, etwa Formatierungsanweisungen für Reasoner-Modelle wie llama.cpp oder Claude1.  
> 3. **Workspace-spezifischer System-Prompt**: Liest individuelle Projektanweisungen aus der Datenbankauswahl des aktiven Workspaces aus und ergänzt diese im Prompt1.

Während des Erstellungsprozesses löst die Template-Engine dynamische Platzhalter wie {{WORKSPACE\_PATH}}, {{CURRENT\_DATE}} oder {{SHELL\_ENV}} direkt auf1.

### **Context Compaction, Token-Limits und Message-Kompression**

Um Token-Limits des Zielmodells einzuhalten, steuert das Modul cptr/agent/compact.py über die Hauptfunktion compact\_chat() die automatische Zusammenfassung langer Konversationsbäume4. In Interaktion mit cptr/db/chats.py berechnet das System die geschätzte Token-Anzahl des Verlaufs4.  
Entwicklerangaben belegen, dass die Kompression schrittweise abläuft:

* **Verlaufsschnitt und Zusammenfassung**: Ältere Abschnitte des Konversationsbaums werden abgeschnitten, durch eine kompakte Zusammenfassung ersetzt und in einem spezialisierten Summary-Knoten zusammengefasst4.  
* **Invariante Zusammenfassungs-Verankerung**: Die generierte Zusammenfassung wird systematisch an einer stabilen Benutzer-Nachricht (user-Rolle) verankert4. Dies garantiert, dass beim Neu-Generieren einer Assistenten-Antwort (regenerate) die erstellte Zusammenfassung im Verlauf erhalten bleibt, anstatt vom Assistant-Node überschrieben zu werden4.  
* **Token-Usage-Normalisierung**: Entwicklerangaben zufolge normalisiert die Pipeline Verbrauchsdaten aus unterschiedlichen Quellen (z. B. OpenAI SSE vs. llama.cpp-Streams) und sendet permanente Kontextauslastungs-Updates an das Frontend4.

### **Context Injection: File-Mentions (@) und Skills ($)**

Das Einfügen externer Artefakte in den Prompt erfolgt über spezialisierte Parser-Module vor der Modell-Übergabe:

* **File-Mentions (@)**: Das Modul cptr/utils/files.py parst Eingabestrings nach dem Muster @dateipfad. Es prüft die Pfadberechtigungen innerhalb des Arbeitsbereichs, liest den Textinhalt vom Dateisystem ein und fasst diesen als strukturierten Kontext-Block im System- oder User-Prompt ein.  
* **Skills ($)**: Das Modul cptr/agent/skills.py verarbeitet Aufrufe mit dem Prefix $1. Es lädt vordefinierte Instruktionen aus entsprechenden SKILL.md-Dateien1. Ergänzend kann der Agent über die interne Funktion view\_skill gezielt projektspezifische Referenzdokumente (wie references/guide.md) nachladen, ohne vollen Zugriff auf das globale Heimatverzeichnis zu benötigen4.

| Element / Command | Verarbeitendes Modul | Quelle / Dateisystem | Funktionsweise |
| :---- | :---- | :---- | :---- |
| **System-Prompt** | cptr/agent/prompt.py | SQLite DB / Config | Generiert hierarchische System-Prompts mit Variableninjektion1. |
| **Compacting** | cptr/agent/compact.py | Konversationsbaum | Staucht alte Message-Trees und verankert Summaries auf User-Nodes4. |
| **@ File-Mention** | cptr/utils/files.py | Workspace-Dateien | Liest Dateiinhalte ein und bettet sie als Context-Block im Prompt ein. |
| **$ Skill** | cptr/agent/skills.py | SKILL.md / Skill-Ordner | Injiziert Skill-Anweisungen; erlaubt Nachladen via view\_skill1. |

## **3\. Execution-Layer & Bibliotheken**

Der Execution-Layer stellt das Bindeglied zwischen den Prompt-Verarbeitungsschritten und der physischen Ausführung dar. Er steuert sowohl die API-Kommunikation mit Cloud-Modellen als auch die Ausführung lokaler Subprozesse.

### **Python-Bibliotheken und Core-Dependencies**

Entwicklerangaben und die Manifest-Dateien des Repositories (pyproject.toml) belegen den Einsatz folgender zentraler Bibliotheken:

* **Netzwerk & API-Kommunikation**: httpx und aiohttp für asynchrone HTTP-Anfragen an externe LLM-Endpoints; openai für standardisierte Interaktionen mit OpenAI-kompatiblen Providern3.  
* **Model Context Protocol (MCP)**: mcp (unter Nutzung von ClientSession und streamablehttp\_client in cptr/utils/mcp/client.py) zur Anbindung externer MCP-Werkzeug-Server1.  
* **Authentifizierung & Sicherheit**: PyJWT (im Modul cptr/utils/config.py) zur Erzeugung und Prüfung von JSON Web Tokens8; cryptography für kryptografische Routinen9.  
* **Persistenz**: sqlite3 zur Anbindung der lokalen Datenbank schichtübergreifend in cptr/db/1.

### **Gateway-Architektur (/v1/chat/completions)**

Das Modul cptr/routers/gateway.py implemetiert das externe Agenten-Gateway. Es übersetzt OpenAI-konforme Anfragen in die interne Ausführungsschleife4:

> 1. **Authentifizierung**: Eingehende Inhaber-Tokens werden mit gehashten Schlüsseln in der Datenbanktabelle gateway\_keys verglichen4.  
> 2. **Context & Header Parsing**: Das Gateway extrahiert spezialisierte Header zur Aufrechterhaltung der Session-Synchronität5:  
   * X-OpenWebUI-Chat-Id  
   * X-OpenWebUI-Message-Id  
   * X-OpenWebUI-User-Message-Id  
   * X-OpenWebUI-User-Message-Parent-Id  
   * X-OpenWebUI-Task

> Diese Parameter stellen sicher, dass Antworten aus Open WebUI exakt demselben Chat-Verlauf und Branch im cptr-Workspace zugeordnet werden5.

> 3. **Loop-Handoff**: Die Anfrage wird an die zentrale Schleife run\_agent\_loop() im Modul cptr/agent/loop.py übergeben7. Ergebnisse werden in einen SSE-Stream gepackt und an den Aufrufer zurückgesendet4.

### **Native Coding-Agenten und Subprozess-Prozesssteuerung**

Neben API-Verbindungen bindet cptr externe Terminal- und Coding-Agenten (Codex, Claude Code, Cursor, OpenCode, Gemini, Pi) als lokale Subprozesse ein1. Die Treiber-Klassen und Adapter hierfür liegen im Verzeichnis cptr/agent/ (z. B. cptr/agent/claude\_code.py, cptr/agent/codex.py, cptr/agent/opencode.py)7.  
Gemäß Code-Analyse erfolgt die Subprozess-Steuerung über definierte Mechanismen:

* **Prozess-Instanziierung**: Über asyncio.create\_subprocess\_exec werden Prozesse gestartet, wobei stdin, stdout und stderr asynchron abgefangen werden.  
* **Transcript-Flattening**: Einige CLI-Adapter (wie claude\_code.py über \_prompt\_from\_messages und codex.py via \_messages\_to\_prompt) konvertieren mehrstufige Nachrichtenverläufe in einen einzelnen geglätteten Transkript-String7.  
* **Prozess-Lifecycle**: Prozess-IDs werden registriert und überwacht. Befehle können jederzeit aus der Chat-Oberfläche oder dem Live-Session-View gestoppt werden4.

| Agent-Adapter | Modul-Dateipfad | Subprozess-Schnittstelle | Funktionscharakteristika |
| :---- | :---- | :---- | :---- |
| **Claude Code** | cptr/agent/claude\_code.py | Asynchroner Subprozess | Erkennt Installationen aus der Claude Desktop App; führt Transkript-Flattening durch4. |
| **Codex** | cptr/agent/codex.py | Asynchroner Subprozess | Wandelt Nachrichtenbäume via \_messages\_to\_prompt in CLI-Prompts um7. |
| **OpenCode** | cptr/agent/opencode.py | Subprozess / Server | Erlaubt Server-Anbindung über konfigurierte Host-Interfaces (0.0.0.0:4096)1. |
| **Gemini / Pi** | cptr/agent/gemini.py / pi.py | Subprozess / CLI | Verwaltet native Sign-In Flows, Resumable Chats und Bild-Attachments4. |

## **4\. Output-Verarbeitung, Tool-Execution & Persistenz**

Die Aufbereitung der Modellausgaben, die Handhabung von Werkzeugaufrufen sowie die Speicherung der Systemzustände bilden den letzten Abschnitt der Verarbeitungskette.

### **Streaming Pipeline (SSE und WebSockets)**

Das Output-Streaming an das Frontend wird über zwei primäre Mechanismen abgewickelt:

> 1. **HTTP Server-Sent Events (SSE)**: In cptr/routers/chat.py und cptr/routers/gateway.py erzeugen FastAPI-Response-Handler kontinuierliche Event-Streams (text/event-stream). Die Svelte-Komponenten im Frontend verarbeiten diese Streams zeilenweise zur schrittweisen Textdarstellung.  
> 2. **WebSocket Event-Broadcasting**: Echtzeitdaten bezüglich Terminal-Outputs, Prozessfortschritten und Systemstatus fließen über das Modul cptr/routers/ws.py4.  
> 3. **Formatierung von Denkprozessen**: Entwicklerangaben zufolge verarbeitet die Streaming-Pipeline strukturierte Tags für Modelle mit Denkketten (o3, Claude, llama.cpp) und rendert diese im Frontend als aufklappbare Abschnitte1.

### **Tool-Calling Loop & System-Werkzeuge**

Die zentrale Interzeption und Ausführung von Werkzeugaufrufen erfolgt im Modul cptr/agent/loop.py innerhalb der Funktion run\_agent\_loop()7. Identifiziert das LLM einen Tool-Call-Bedarf, unterbricht die Schleife die Textgenerierung und leitet den Aufruf an das jeweilige Modul unter cptr/tools/ weiter:

* **Shell-Commands (cptr/tools/shell.py)**: Führt Konsolenbefehle direkt auf dem Host-System oder im Docker-Container aus1. Lang laufende Ausführungen werden asynchron gestreamt und lassen sich abbrechen4.  
* **Dateisystem-Werkzeuge (cptr/tools/files.py)**: Ermöglicht das Suchen, Lesen, Erstellen und Editieren von Dateien im Workspace1. Alle Schreib- und Lesezugriffe erzwingen strikt die UTF-8-Textkodierung4.  
* **Web-Browsing (cptr/tools/browser.py)**: Steuert eine Playwright-/Chromium-Instanz zur Seitennavigation, Formularinteraktion und Erstellung von Screenshots1. Auf headless Servern ohne GPU fällt das Videostreaming automatisch auf Software-Encoding zurück4.  
* **MCP-Client (cptr/utils/mcp/client.py)**: Verfällt die Anfrage auf ein MCP-Werkzeug, wird der Aufruf über das MCP-Protokoll an externe Tool-Server weitergereicht1.

| Tool-Gruppe | Verarbeitendes Modul | Ausführungsmechanismus | Besonderheiten / Eigenschaften |
| :---- | :---- | :---- | :---- |
| **Shell & Terminal** | cptr/tools/shell.py | Asynchrone Shell-Subprozesse | Live-Output-Streaming; manuelle Abbruchsteuerung via UI4. |
| **Dateisystem** | cptr/tools/files.py | Native I/O Dateihandler | Erzwungene UTF-8 Kodierung; Suffix-Vergabe bei Dateikonflikten4. |
| **Web-Browser** | cptr/tools/browser.py | Playwright / Chromium | Sized Screenshots; Software-Encoding-Fallback für headless Instanzen4. |
| **MCP Integration** | cptr/utils/mcp/client.py | MCP Client Protocol | Erfordert optionale Extra-Dependencies (pip install 'cptr\[mcp\]')1. |

### **Persistenz, Datenbankschema und Pfad-Normalisierung**

Die Speicherung aller Anwendungszustände erfolgt in einer SQLite-Datenbank (/data/app.db im Docker-Container bzw. \~/.cptr/app.db bei lokaler Installation)1. Das Datenbankmodul cptr/db/database.py verwaltet Verbindungs-Pools und Schema-Migrationen10.  
In cptr/db/models.py sind die Kern-Modelle definiert:

* User: Speichert Authentifizierungsdaten und Präferenzen11.  
* Workspace: Verwaltet Pfade, projektspezifische System-Prompts und Einstellungen4.  
* Chat & Message: Repräsentieren die Konversationsbäume inklusive Baum-Verzweigungen und verankerten Summaries4.  
* GatewayKey: Hält gehaschte API-Schlüssel für die /v1/-Schnittstelle4.

Um Konsistenzprobleme zu vermeiden, führt das Modul cptr/utils/workspace.py eine Pfad-Normalisierung durch4. Pfad-Aliase (wie \~/Projects/myapp und /Users/you/Projects/myapp) werden vor Datenbankabfragen auf denselben kanonischen Pfad aufgelöst, wodurch Duplikate in den Arbeitsbereichen unterbunden werden4.

## **5\. Fazit**

Die Code-Analyse von open-webui/computer (cptr) belegt eine Architektur, die auf Modularität, Resilienz und enge Systemintegration ausgelegt ist1. Die Kombination aus entkoppeltem FastAPI-Backend3, strikter Session-Synchronisation im Gateway5, robuster Event-Führung via WebSockets4 und dezidierten Subprozess-Treibern für lokale Coding-Agenten4 ermöglicht eine konsistente Agenten-Steuerung über lokale und entfernte Schnittstellen hinweg1.

#### **Referenzen**

> 1. open-webui/computer: Your Computer. Anywhere. \- GitHub, [https://github.com/open-webui/computer](https://github.com/open-webui/computer)  
> 2. Open WebUI Computer, [https://docs.openwebui.com/ecosystem/computer/](https://docs.openwebui.com/ecosystem/computer/)  
> 3. MCP optional extra not installed in Docker image — MCP tool servers fail silently out of the box · Issue \#62 · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/issues/62](https://github.com/open-webui/computer/issues/62)  
> 4. computer/CHANGELOG.md at main · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/CHANGELOG.md](https://github.com/open-webui/computer/blob/main/CHANGELOG.md)  
> 5. cptr.mdx \- Open WebUI Computer \- GitHub, [https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx](https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx)  
> 6. Releases · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/releases](https://github.com/open-webui/computer/releases)  
> 7. bug: Agent fabricates user turns and self-executes tools (runaway) — history flattened into in-band \[role\] transcript with no turn-boundary stop · Issue \#152 · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/issues/152](https://github.com/open-webui/computer/issues/152)  
> 8. docs/docs/features/computer/index.md at main · open-webui/docs \- GitHub, [https://github.com/open-webui/docs/blob/main/docs/features/computer/index.md](https://github.com/open-webui/docs/blob/main/docs/features/computer/index.md)  
> 9. bug: cryptography 49.0.0 Rust bindings fail at runtime on Python 3.14 (Termux/Android) · Issue \#150 · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/issues/150](https://github.com/open-webui/computer/issues/150)  
> 10. bug: chat\_messages INSERT crashes when Open WebUI \`models, [https://github.com/open-webui/computer/issues/153](https://github.com/open-webui/computer/issues/153)  
> 11. Releases · open-webui/open-webui \- GitHub, [https://github.com/open-webui/open-webui/releases](https://github.com/open-webui/open-webui/releases)