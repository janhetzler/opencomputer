# **Comprehensive Technical Audit: Repository- und Aktivitäts-Analyse von open-webui/computer (cptr)**

Das Repository open-webui/computer (systemintern unter dem Paketnamen cptr geführt) stellt eine neuartige, browserbasierte Arbeitsumgebung dar, die ein lokales System – inklusive Dateisystem, Terminal, Git-Status, Editor und KI-Agenten – über eine mobilspezifische und native Schnittstelle im Browser bereitstellt1. Die nachfolgende technische Analyse basiert auf einer detaillierten Evaluierung des aktuellen Entwicklungsstands, der Open-Issue-Tickets, der Backend- und Frontend-Manifeste sowie der qualitätssichernden Tooling-Infrastruktur des Projekts. Alle getroffenen technischen Feststellungen stammen strikt aus den Auswertungen des Quellcodes, den Konfigurationsdateien sowie den amtlichen Entwicklerangaben im Issue-Tracker des Repositories2.

## **1\. Projekt-Aktivität und Bug-Tracker-Analyse**

Die Auswertung des Issue-Trackers und der Diskussionsforen verdeutlicht, dass sich das Projekt in einer Phase intensiver Architekturverfeinerung befindet. Der primäre Fokus der Entwicklungsaktivitäten liegt derzeit auf der Stabilisierung des Agenten-Routings, der Reparatur von Fehlern in der Container-Build-Kette sowie der Anpassung des Systems an isolierte, entkoppelte Ausführungsumgebungen2.  
Im Zentrum der Entwicklerdiskussionen stehen drei Hauptkomponenten: das KI-Gateway, das Docker-Deployment sowie die Benutzeroberfläche bei extremen Display-Formatfaktoren2. Die gravierendsten Fehlverhalten betreffen das Zusammenspiel zwischen dem integrierten Chat-Completions-Gateway (/v1/chat/completions) und externen Chat-Interfaces wie OpenWebUI5.  
Anhand der Issue-Protokolle lassen sich die nachfolgenden Kernprobleme und Entwicklungsaktivitäten identifizieren:

* **Agenten-Routing & Turn-Boundary-Handling (Issue \#152, \#50, \#77)**: Laut Entwicklerangaben kommt es bei der Anbindung von cptr als Modell-Backend über die Chat-Completions-Schnittstelle zu schwerwiegenden Synchronisationsfehlern im Dialogfluss5. Entwickler dokumentieren ein Phänomen, bei dem der Agent selbstständig gegnerische Benutzer-Turns erzeugt und Werkzeuge in einer unkontrollierten Schleife ("Runaway Execution") ausführt5. Die Ursache liegt laut Issue-Analyse in einer Verflachung des Kontext-Verlaufs in einen in-band \[role\]-Fließtext ohne explizite Turn-Boundary Stop-Sequenzen5.  
* **Docker-Containerization & MCP-Abhängigkeiten (Issue \#62)**: Das Model Context Protocol (MCP) wird für externe Werkzeug-Server genutzt2. Im offiziellen Docker-Image ghcr.io/open-webui/computer schlägt die Verifizierung von MCP-Servern jedoch systematisch fehl2. Entwickleranalysen belegen, dass in pyproject.toml zwar die Abhängigkeit mcp\>=1.8 als optionales Extra \[mcp\] deklariert ist, die Bauanweisung im Dockerfile das Python-Wheel jedoch ohne Extra-Tags installiert (uv pip install /tmp/\*.whl)2. Dadurch löst der Aufruf in cptr/routers/admin.py über cptr/utils/mcp/client.py einen ModuleNotFoundError aus, welcher im Backend stumm abgefangen und als allgemeiner Fehler ausgegeben wird2.  
* **Deployment in air-gapped Netzwerken (Issue \#95)**: Bei geschützten Enterprise-Einsätzen stößt der aktuelle Installationspfad an Grenzen6. Der Bau- und Startprozess erzwingt aktuell dynamische Downloads über Paketmanager (npm ci, uv build, apt-get install, PyPI)6. Entwickler fordern vorkompilierte Wheelhouses, Offline-OCI-Archive sowie eigenständige SBOM- und Prüfsummen-Artefakte6.  
* **UI/UX und Desktop-Ergonomie (Issue \#91)**: In Bezug auf das Frontend melden Anwender fehlende Kontraste im Dark Theme für OLED-Displays, unzureichende Skalierungsoptionen für Ultra-Wide-Monitore (21:9) sowie den Wunsch nach automatischer Erkennung von Git Worktrees innerhalb der Workspace-Navigation7.

| Komponente / Modul | Relevante Issue-IDs | Schweregrad | Technische Problembeschreibung laut Entwicklerangaben |
| :---- | :---- | :---- | :---- |
| **Agent Gateway Routing** | \#50, \#77, \#152 | Hoch | Verflachung der Chathistorie führt zu erfundenen Benutzer-Turns und Endlosschleifen bei Tool-Aufrufen5. |
| **Docker & Tooling** | \#62 | Hoch | Fehlen der mcp-Bibliothek im Docker-Image führt zu ModuleNotFoundError beim Laden von cptr/utils/mcp/client.py2. |
| **Deployment / Build** | \#95 | Mittel | Fehlender Support für strikt isolierte (Air-Gapped) Netzwerke durch externe Paketabhängigkeiten im Startpfad6. |
| **Frontend / Ergonomie** | \#91 | Niedrig \- Mittel | Mangelnde UI-Skalierung, fehlender OLED-Kontrast und fehlende Git-Worktree-Erkennung in der Benutzeroberfläche7. |

## **2\. Backend-Architektur und Bibliotheken-Evaluation**

Das Backend von cptr ist als hochperformante, asynchrone Python-Anwendung konzipiert, die primär auf schnelle Dateisystem-Echtzeitoperationen und einfache Bereitstellung ausgelegt ist1. Die Projektkonfiguration erfolgt zentral über die Datei pyproject.toml unter Nutzung des Build-Systems Hatchling (hatchling)3.

### **Analyse der Abhängigkeiten (pyproject.toml)**

Aus dem Manifest pyproject.toml lassen sich folgende Kern-Frameworks und Bibliotheken für den Laufzeitbetrieb entnehmen3:

* **Web-Framework & API-Schicht**: fastapi\[standard\]\>=0.128.8 stellt das primäre REST- und WebSocket-Framework bereit3. Standardmäßig werden HTTP-Endpunkte sowie WebSocket-Verbindungen für Terminal-Streamings und Status-Updates verwendet3.  
* **Datenbank & Persistenz**: Die Anwendung nutzt sqlalchemy\[asyncio\]\>=2.0 in Verbindung mit aiosqlite\>=0.20 zur vollständig asynchronen Abwicklung von Datenbankoperationen3. Das Datenbankschema wird über alembic\>=1.13 verwaltet und in einer lokalen SQLite-Datei (/data/app.db) gespeichert1.  
* **Sicherheit & Authentifizierung**: Für Kennwort-Hashing, Verschlüsselung und Sitzungssicherheit werden bcrypt\>=4.0, PyJWT\>=2.8 sowie cryptography\>=42.0 eingesetzt3.  
* **Dateisystem- und Netzwerk-I/O**: watchdog\>=6.0.0 überwacht Dateisystemänderungen im Workspace in Echtzeit3. Externe HTTP-Aufrufe (z. B. an KI-Provider oder Suchmaschinen) werden über den asynchronen Client httpx\>=0.28.1 abgewickelt3.  
* **Logging & CLI**: Strukturiertes Logging erfolgt über loguru\>=0.7.3, während Befehlszeilen-Aufrufe (cptr run) über click\>=8.1 realisiert werden1.

| Bibliothek / Framework | Version (Manifest) | Anwendungszweck im Backend |
| :---- | :---- | :---- |
| **FastAPI** | \>=0.128.8 | Haupt-Webframework für REST-Endpunkte und WebSocket-Streaming3 |
| **SQLAlchemy (AsyncIO)** | \>=2.0 | Asynchrones ORM zur Abbildung von Benutzern, Sitzungen und Konfigurationen3 |
| **aiosqlite** | \>=0.20 | Asynchroner Treiber für die SQLite-Datenbank (app.db)1 |
| **Alembic** | \>=1.13 | Verteilung und Ausführung von Datenbank-Schema-Migrationen3 |
| **Watchdog** | \>=6.0.0 | Event-gesteuerte Dateisystem-Überwachung zur Echtzeit-Synchronisation3 |
| **httpx** | \>=0.28.1 | Asynchroner HTTP-Client für Model-Gateways und Such-Integratoren3 |
| **Loguru** | \>=0.7.3 | Zentrales, strukturiertes Logging-System3 |

### **Ordnerstruktur und Modulorganisation**

Der Quellcode des Backends befindet sich im Unterordner cptr/ und ist strikt nach funktionalen Zuständigkeiten gegliedert3:

* cptr/routers/: Enthält die API-Routing-Logik unterteilt nach Subsystemen2. So verwaltet cptr/routers/admin.py administrative Einstellungen und Werkzeug-Server (z. B. MCP-Verifizierung), während cptr/routers/auth.py die Benutzeranmeldung steuert2.  
* cptr/db/: Beinhaltet die ORM-Modelle, Datenbanktreiber-Initialisierungen und Alembic-Migrationsskripte für die SQLite-Persistenz1.  
* cptr/utils/: Hilfsmodule und externe Protokoll-Adapter2. Hier befindet sich unter cptr/utils/mcp/client.py die Client-Implementierung für das Model Context Protocol2.  
* cptr/frontend/: Enthält den Quellcode sowie das kompilierte Build-Artefakt des Frontends (cptr/frontend/build), welches bei der Wheel-Erstellung direkt in das Python-Paket eingebunden wird3.  
* **Terminal- & Prozesssteuerung**: Die Ausführung von Shell-Befehlen erfolgt laut CHANGELOG.md über ein echtes Pseudo-Terminal (PTY), um die native Handhabung von interaktiven CLI-Werkzeugen und Terminal-Agenten zu gewährleisten9.  
* **Gateway-Komponente**: Implementiert die OpenAI-kompatible Schnittstelle /v1/chat/completions, wodurch Workspaces als virtuelle Modelle für externe Clients bereitgestellt werden1.

## **3\. Frontend-Architektur und Benutzeroberflächen-Stack**

Das Frontend ist als hochmoderne, responsive Single Page Application (SPA) mit ausgeprägten PWA-Fähigkeiten (Progressive Web App) umgesetzt10. Laut Entwicklerdokumentation wurde die Benutzeroberfläche speziell für Touch- und Portrait-Betrieb auf Mobilgeräten optimiert1.

### **Paketierung und Manifest-Logik (package.json)**

Das Root-Manifest package.json fungiert als Steuerungsdatei für die gesamte Repository-Werkzeugkette4. Es delegiert Frontend-Befehle direkt an das Unterverzeichnis cptr/frontend/4.  
Anhand des Wurzel-Manifests package.json sind folgende Skripte definiert4:

* "format:frontend": Ruft npm \--prefix cptr/frontend run format:frontend auf4.  
* "format:check:frontend": Prüft die Frontend-Formatierung im Sub-Repository4.  
* "format:backend": Führt uv run ruff format cptr aus4.

### **UI-Komponenten und State-Management**

Das Frontend kombiniert mehrere spezialisierte Benutzeroberflächen-Komponenten, um ein vollständiges Desktop-Erlebnis im Browser abzubilden1:

* **Terminal-Integration**: Bereitstellung einer vollständigen Shell-Schnittstelle im Browser auf Basis von Pseudo-Terminals (PTY)1. Terminalsitzungen laufen serverseitig weiter, selbst wenn die Browser-Registerkarte geschlossen wird1.  
* **Editor & Git-Panel**: Tab-basierter Code-Editor mit Syntax-Highlighting sowie ein visuelles Git-Panel zum Stagen, Committen, Diffen und Verwalten von Branches1.  
* **Mobile-First PWA & Offline-Fähigkeit**: Das Frontend verfügt über umfassende PWA-Unterstützung inklusive Offline-Caching über Service Worker, Home-Screen-Shortcuts ("New Chat", "Open Workspace", "New Terminal") sowie eine W3C Share Target Schnittstelle, mit der Dateien direkt aus mobilen Betriebssystemen importiert werden können10.  
* **Echtzeit-Synchronisation & Event-Architektur**: Die Benutzeroberfläche kommuniziert über ein hybrides WebSocket-Protokoll9. Ereignisse werden zentral über einen Socket-Listener verwaltet, der Verbindungsabbrüche automatisch abfängt und Listener neu registriert, um Event-Verluste bei instabilen Netzwerkbedingungen zu verhindern10.  
* **Leistungsoptimierung**: Um die Reaktionsfähigkeit der UI bei massiven Dateisystemänderungen zu sichern, werden Git-Statusaktualisierungen laut Entwicklerangaben in CHANGELOG.md über Debouncing-Mechanismen verzögert und in Batches verarbeitet9.

## **4\. Code-Qualität, Typisierung und Testinfrastruktur**

Die Qualitätssicherung im Repository basiert auf modernen, schnellen Toolchains aus dem Python- und JavaScript-Ökosystem3.

### **Statische Code-Analyse und Linter (Python)**

Gemäß der Konfiguration im Abschnitt \[tool.ruff\] der Datei pyproject.toml kommt das High-Performance-Tooling **Ruff** für Linting und Formatierung zum Einsatz3:

* **Maximale Zeilenlänge**: Auf 100 Zeichen festgelegt (line-length \= 100\)3.  
* **Python-Zielversion**: py310 (Python 3.10)3.  
* **Ausschlüsse**: Die Ordner cptr/frontend und dist sind explizit von der Python-Analyse ausgenommen (extend-exclude)3.

### **Build- und Skriptinfrastruktur**

Die Qualitätssicherung ist über einheitliche Skripte im Root-package.json orchestriert4:

| NPM Skript Command | Ausgeführter Befehl | Zweck / Wirkung |
| :---- | :---- | :---- |
| npm run format | npm run format:frontend && npm run format:backend | Formatiert die gesamte Frontend- und Backend-Codebasis parallel4. |
| npm run format:check | npm run format:check:frontend && npm run format:check:backend | Validiert im CI-Prozess, ob sämtliche Dateien den Stilrichtlinien entsprechen4. |
| npm run format:backend | uv run ruff format cptr | Formatiert das Python-Backend im Verzeichnis cptr/ mittels Ruff4. |
| npm run format:check:backend | uv run ruff format \--check cptr | Führt eine zerstörungsfreie Formatierungsprüfung des Backends durch4. |

Anhand der Manifeste lässt sich feststellen, dass der Fokus im Repository primär auf lintergestützter Formatierung (ruff) und modularer Entkopplung liegt3.

## **5\. Fazit und Architektur-Empfehlungen**

Die Analyse des Repositories open-webui/computer offenbart eine durchdachte und moderne Architektur, die die Grenze zwischen lokaler Workstation und browserbasierter Cloud-Erfahrung aufhebt1. Dennoch ergeben sich aus den Quellcodes und Issue-Tracker-Daten konkrete Handlungsfelder für das Entwicklerteam:  
Die Entkopplung der Gateway-Prompts ist von hoher Priorität. Die Vorfälle bezüglich unbeabsichtigter Werkzeugausführungen (\#152) verdeutlichen, dass das Auslesen und Verflachen von Chat-Historien über /v1/chat/completions eine Überarbeitung der Prompt-Parser-Logik erfordert5. Es sollten strikt separierte API-Rollen-Grenzen anstelle von In-Band-Textmarkern durchgesetzt werden5.  
Ebenso ist eine Korrektur der Docker-Pipeline zwingend erforderlich. Der Build-Prozess im Dockerfile muss angepasst werden, um optionale Abhängigkeiten wie cptr\[mcp\] korrekt zu installieren und funktionale Brüche bei der Nutzung externer Tool-Server abzuwenden2. Für den Einsatz in geschützten Unternehmensumgebungen sind zudem isolierte Release-Bundles (offline wheelhouses, vorgebaute OCI-Container) bereitzustellen, um dynamische Nachdownloads zur Laufzeit zu eliminieren6.

#### **Referenzen**

> 1. open-webui/computer: Your Computer. Anywhere. \- GitHub, [https://github.com/open-webui/computer](https://github.com/open-webui/computer)  
> 2. MCP optional extra not installed in Docker image — MCP tool servers fail silently out of the box · Issue \#62 · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/issues/62](https://github.com/open-webui/computer/issues/62)  
> 3. pyproject.toml \- open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/pyproject.toml](https://github.com/open-webui/computer/blob/main/pyproject.toml)  
> 4. package.json \- open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/package.json](https://github.com/open-webui/computer/blob/main/package.json)  
> 5. bug: Agent fabricates user turns and self-executes tools (runaway) — history flattened into in-band \[role\] transcript with no turn-boundary stop · Issue \#152 · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/issues/152](https://github.com/open-webui/computer/issues/152)  
> 6. feat: Support fully air-gapped installation and first run · Issue \#95 · open-webui/computer · GitHub, [https://github.com/open-webui/computer/issues/95](https://github.com/open-webui/computer/issues/95)  
> 7. Desktop UX: contrast, scaling, and git worktree discovery · Issue \#91 · open-webui/computer, [https://github.com/open-webui/computer/issues/91](https://github.com/open-webui/computer/issues/91)  
> 8. cptr.mdx \- Open WebUI Computer \- GitHub, [https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx](https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx)  
> 9. computer/CHANGELOG.md at main · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/CHANGELOG.md](https://github.com/open-webui/computer/blob/main/CHANGELOG.md)  
> 10. Releases · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/releases](https://github.com/open-webui/computer/releases)