# **Systematische Code-Analyse und Automatisierungsarchitektur von Open WebUI Computer (cptr)**

Die Software-Architektur von Open WebUI Computer (cptr) basiert auf einem hybriden Modell, das ein Python-Backend auf FastAPI- und Uvicorn-Basis mit einem reaktiven TypeScript- und Svelte-Frontend sowie einer eingebetteten SQLite-Datenbank kombiniert1. Das System dient als direkte Steuerungsschicht für die darunterliegende Systemressource und stellt Dateisystem-, Terminal-, Git-, Browser- und KI-Agenten-Funktionen über Weboberflächen und API-Gateway-Schnittstellen bereit1. Für Administratoren bietet diese Architektur Schnittstellen zur automatisierten Konfiguration, Rechtevergabe und Fernsteuerung. Die nachfolgende Analyse schlüsselt die technischen Komponenten, Endpunkte, Datenbankstrukturen und Automatisierungsstrategien auf Basis des Quellcodes auf.

## **Benutzerverwaltung und Authentifizierungsautomatisierung**

Die Benutzerverwaltung und Authentifizierung von cptr sind darauf ausgelegt, den Erstzugriff über Token-Links abzuwickeln und spätere Sitzungen über JSON Web Tokens (JWT) abzusichern2. Der Backend-Code ist modular strukturiert, wobei die Authentifizierungslogik vorwiegend in den Modulen cptr/routers/auth.py, cptr/db/users.py und cptr/utils/config.py verankert ist3.

### **Backend-Endpunkte und Erstregistrierung**

Beim ersten Start ohne vorhandene Konfiguration erzeugt cptr einen einmaligen Setup-Token, der über die Konsole ausgegeben wird (z. B. http://localhost:8000/?token=...)1. Dieser Token berechtigt den Inhaber zur Ausführung des initialen Registrierungs-Endpunkts, über den der erste Administrator-Account angelegt wird2.

* **Setup & Registrierung (cptr/routers/auth.py)**: Über den Endpunkt POST /api/v1/auth/setup nimmt das Backend Benutzername, E-Mail-Adresse und Passwort entgegen. Der erste registrierte Benutzer erhält automatisch die Rolle admin zugewiesen2.  
* **Login & Token-Ausstellung (POST /api/v1/auth/login)**: Validiert die Anmeldedaten gegen die SQLite-Datenbank und gibt ein signiertes JWT-Token zurück2. Dieses Token muss bei allen nachfolgenden API-Aufrufen im HTTP-Header als Authorization: Bearer \<JWT\_TOKEN\> übergeben werden.  
* **Benutzerverwaltung (cptr/routers/admin.py)**: REST-Endpunkte wie GET /api/v1/admin/users, POST /api/v1/admin/users sowie PATCH /api/v1/admin/users/{user\_id} gestatten es Administratoren, neue Konten anzulegen, Passwörter zurückzusetzen oder Rollen (Admin vs. Standardnutzer) zu ändern5.

### **SQLite-Datenmodell (/data/app.db)**

Der Persistenzzustand der Instanz wird standardmäßig im Verzeichnis \~/.cptr/app.db bzw. im Docker-Container unter /data/app.db gespeichert1. Das Datenbankschema beruht auf SQLite3 und wird über interne Migrationsscripte gesteuert1. Die zentrale Tabelle für die Benutzerverwaltung ist user7.

| Tabellenspalte | Datentyp | Beschreibung & Automatisierungsrelevanz |
| :---- | :---- | :---- |
| id | TEXT / INTEGER | Primärschlüssel (UUIDv4 oder aufsteigende ID). |
| username | TEXT | Eindeutiger Anmeldename des Benutzers. |
| email | TEXT | E-Mail-Adresse des Kontos. |
| password\_hash | TEXT | Mit Passlib (Bcrypt/PBKDF2) gehashter Passwort-String3. |
| role | TEXT | Rolle des Benutzers (z. B. admin oder user). Steuert Berechtigungsprüfungen7. |
| is\_active | BOOLEAN / INTEGER | Flag zur Aktivierung/Deaktivierung des Zugangs (1 \= aktiv, 0 \= gesperrt). |
| created\_at | TIMESTAMP | Erstellungszeitpunkt des Eintrags. |

Eine direkte Skript-Injektion in /data/app.db ermöglicht ein Headless-Provisioning ohne Ausführen des interaktiven Weblinks. Das folgende Python-Skript demonstriert die direkte Datenbank-Injektion eines Admin-Benutzers:

Python  
import sqlite3  
import uuid  
from datetime import datetime  
from passlib.hash import bcrypt

DB\_PATH \= "/data/app.db"

def inject\_admin\_user(username, email, plain\_password):  
    password\_hash \= bcrypt.hash(plain\_password)  
    user\_id \= str(uuid.uuid4())  
    now \= datetime.utcnow().isoformat()

    conn \= sqlite3.connect(DB\_PATH)  
    cursor \= conn.cursor()

    cursor.execute("""  
        INSERT INTO user (id, username, email, password\_hash, role, is\_active, created\_at)  
        VALUES (?, ?, ?, ?, ?, 1, ?)  
    """, (user\_id, username, email, password\_hash, "admin", now))

    conn.commit()  
    conn.close()  
    print(f"Admin-Benutzer '{username}' erfolgreich in DB injiziert.")

if \_\_name\_\_ \== "\_\_main\_\_":  
    inject\_admin\_user("sysadmin", "admin@example.com", "SecurePassword123\!")

### **Steuerung über Umgebungsvariablen und CLI-Flags**

Die globale Authentifizierung und Laufzeitkonfiguration lassen sich direkt beim Aufruf von cptr run sowie über System-Umgebungsvariablen steuern1.

| Variable / Flag | Typ | Standardwert | Funktion & Beschreibung |
| :---- | :---- | :---- | :---- |
| CPTR\_DATA\_DIR | Env Var | \~/.cptr | Bestimmt den Pfad zum Datenverzeichnis inklusive app.db2. |
| CPTR\_AUDIT\_LOG\_LEVEL | Env Var | *keiner* | Steuert die Protokollierung mutating Aufrufe (POST/PUT/DELETE) in eine JSON-Datei2. |
| CPTR\_LOG\_UPSTREAM\_REQUESTS | Env Var | false | Aktiviert das Logging abgehender KI-Modellaufrufe2. |
| PERPLEXITY\_BASE\_URL | Env Var | *Standard-API* | Konfiguriert die Ziel-URL für Perplexity-Suchanfragen (z. B. LiteLLM Proxy)8. |
| \--host | CLI Flag | 127.0.0.1 | Bindet den HTTP-Server an Netzwerk-Schnittstellen (z. B. 0.0.0.0)1. |
| \--port | CLI Flag | 8000 | Legt den Listening-Port des Uvicorn-Servers fest2. |
| \--headless | CLI Flag | false | Verhindert das automatische Öffnen des Browsers beim Start2. |
| \--reload | CLI Flag | false | Entwicklungsmodus mit automatischem Hot-Reloading2. |

## **UI-Administration, Theme-Konfiguration und Bildschirmeinstellungen**

Die Benutzeroberfläche von cptr trennt strikt zwischen rein lokalen Client-Einstellungen und serverseitig erzwungenen System-Konfigurationen9.

### **Trennung zwischen Browser LocalStorage und Server-Persistenz**

Eine Untersuchung der Svelte-Frontend-Komponenten zeigt die genaue Aufteilung der Zuständigkeiten:

* **Client-seitig (LocalStorage)**: Im LocalStorage des Browsers verbleiben rein darstellungsbezogene Präferenzen. Dazu gehören der visuelle Rahmenkontrast (border contrast control)9, aktive Split-Layouts, Fenstergrößen der Panels, die Anordnung geöffneter Workspace-Tabs9 sowie lokale Audio-Wiedergabeeinstellungen (wie der Schalter für automatisches Vorlesen im Client)9 und PWA-Service-Worker-Caches8.  
* **Server-seitig (app.db & administrative REST-APIs)**: Serverseitig in der SQLite-Datenbank abgelegt und über administrative Endpunkte gesteuert werden global gültige System-Prompts für KI-Agenten1, die Definition und Aktivierung von Skills (Instruktionsdateien/SKILL.md)1, die Zuordnung zulässiger Werkzeuggruppen (Tool-Gruppen wie Terminal-, Dateisystem- oder Browserzugriff) pro KI-Modell9, die Konfiguration der Headless-Browser-Streaming-Qualität (Encoder-Einstellungen: Auto, Software- oder Hardware-Kodierung)9 sowie die automatische Verwaltung von .gitignore-Einträgen für .cptr-Daten9.

### **Administrative REST-Endpunkte für UI- und Modell-Standards**

Administratoren können über das Backend globale Vorgaben durchsetzen, die für alle verbundenen Clients gelten. Das Modul cptr/routers/admin.py stellt Endpunkte bereit, um System-Prompts, Skill-Verhalten und Web-Streaming zu steuern5.  
Das folgende Snippet zeigt den Aufruf zur automatisierten Setzung eines globalen System-Prompts und der Streaming-Qualität:

Bash  
\# Setzen des globalen System-Prompts über die Admin-API  
curl \-X POST "http://localhost:8000/api/v1/admin/settings/prompt" \\  
  \-H "Authorization: Bearer \<ADMIN\_JWT\_TOKEN\>" \\  
  \-H "Content-Type: application/json" \\  
  \-d '{  
    "global\_system\_prompt": "Du bist ein automatisierter System-Assistent. Führe Befehle präzise aus.",  
    "override\_workspace\_prompts": false  
  }'

\# Konfiguration des Browser-Streams auf Software-Encoding (für Headless-Server)  
curl \-X POST "http://localhost:8000/api/v1/admin/settings/browser" \\  
  \-H "Authorization: Bearer \<ADMIN\_JWT\_TOKEN\>" \\  
  \-H "Content-Type: application/json" \\  
  \-d '{  
    "streaming\_encoder": "software",  
    "display\_quality": "auto"  
  }'

## **System-Konfiguration, Gateway API und Service-Steuerung**

Über die Standard-Chat-Oberfläche hinaus stellt cptr umfassende Schnittstellen für Fernsteuerung, Tool-Einbindung und Monitoring bereit1.

### **Die Gateway-API (/v1/chat/completions & /v1/models)**

cptr fungiert als OpenAI-kompatibler Gateway-Server1. Dadurch kann jede externe Anwendung, die das OpenAI-Protokoll beherrscht (wie Open WebUI, LangChain oder benutzerdefinierte Skripte), einen Workspace von cptr als vollständiges KI-Modell ansteuern1. Der KI-Agent erhält dabei vollen Zugriff auf das Dateisystem, die Shell und Web-Tools1.

* **Modell-Listen-Endpunkt (GET /v1/models)**: Listet alle verfügbaren Workspaces als Arbeitsmodelle auf (z. B. cptr/my-project)4.  
* **Chat-Completions-Endpunkt (POST /v1/chat/completions)**: Führt Agenten-Schleifen im Ziel-Workspace aus1.

Zugriffe auf die Gateway-API werden über dedizierte Schlüssel im Format sk-cptr-... authentifiziert4. Diese Schlüssel werden gehasht in der Tabelle gateway\_key gespeichert9 und über die Endpunkte POST /api/v1/admin/gateway/keys (Erstellung), GET /api/v1/admin/gateway/keys (Auflistung) sowie DELETE /api/v1/admin/gateway/keys/{key\_id} (Löschung) verwaltet9.

### **Steuerung externer Dienste und Werkzeuge**

Die Admin-Schnittstelle in cptr/routers/admin.py erlaubt das dynamische Hinzufügen und Konfigurieren von Drittanbieter-Diensten5:

* **MCP Tool Server (Model Context Protocol)**: Verwaltet externe Werkzeug-Server via cptr/utils/mcp/client.py5. Über POST /api/v1/admin/tools/mcp können neue MCP-Server registriert und verifiziert werden5.  
* **Messaging Bots**: Anbindung an Telegram, Discord, Slack, WhatsApp und Signal1 über den Konfigurations-Endpunkt POST /api/v1/admin/messaging.  
* **Audio & Transkription (Whisper)**: Steuerung von Text-to-Speech (TTS) und Speech-to-Text (STT) Anmeldedaten und Modellen via POST /api/v1/admin/audio9.  
* **Bildgenerierung**: Einbindung OpenAI-kompatibler Image-APIs via POST /api/v1/admin/images8.  
* **Scheduled Tasks (Automatisierungen)**: Geplante wiederkehrende Aufgaben ("Run tests every morning") werden serverseitig verwaltet und ausgeführt1.

### **Audit-Protokollierung und System-Diagnose**

Für den Betrieb in Sicherheits- und Produktionsumgebungen verfügt cptr über zwei integrierte Überwachungsmechanismen1:

> 1. **Audit-Trail (CPTR\_AUDIT\_LOG\_LEVEL)**: Bei Aktivierung schreibt das Backend alle zustandsverändernden HTTP-Aufrufe (POST, PUT, PATCH, DELETE) in eine strukturierte JSON-Datei2. Sensible Daten wie Passwörter oder API-Keys werden automatisch maskiert2.  
> 2. **Upstream Request Logging (CPTR\_LOG\_UPSTREAM\_REQUESTS=true)**: Protokolliert alle ausgehenden Aufrufe an KI-Provider (inklusive Token-Zahlen, Latenzen und Endpunkten) zur Aufwands- und Kostenkontrolle in eine separate Log-Datei2.

### **Übersicht der administrativen API-Endpunkte**

| Endpunkt | Methode | Beschreibung & Payload-Typ | Dateipfad Backend |
| :---- | :---- | :---- | :---- |
| /api/v1/auth/setup | POST | Initiales Erstellen des ersten Admin-Accounts. | cptr/routers/auth.py |
| /api/v1/auth/login | POST | Anmelden und Erhalten des Admin-JWT-Tokens. | cptr/routers/auth.py |
| /api/v1/admin/users | GET / POST | Liste aller Nutzer abrufen oder neue Nutzer anlegen. | cptr/routers/admin.py |
| /api/v1/admin/gateway/keys | POST | Erzeugt einen neuen sk-cptr-... Gateway-Schlüssel4. | cptr/routers/admin.py |
| /api/v1/admin/tools/mcp | POST | Registriert und prüft einen MCP-Server5. | cptr/routers/admin.py |
| /api/v1/admin/audio | POST | Konfiguriert STT/TTS-Provider (Whisper, Base-URL)9. | cptr/routers/admin.py |
| /api/v1/admin/messaging | POST | Einrichtung von Telegram/Discord/Slack-Bots9. | cptr/routers/admin.py |
| /v1/chat/completions | POST | OpenAI Gateway Agenten-Ausführung1. | cptr/routers/gateway.py |

## **Automatisierungskonzept und Implementierungsplan**

Um eine cptr-Instanz ohne manuellen Eingriff vollständig zu provisionieren und zu steuern, empfiehlt sich eine dreistufige Automatisierungsarchitektur, die sequentielle Initialisierungsschritte orchestriert:

### **Phase 1: Pre-Execution Bootstrap (Datenbank & Umgebung)**

In der ersten Phase wird die Umgebung vorbereitet, bevor der Python-Prozess startet. Über Umgebungsvariablen wie CPTR\_DATA\_DIR wird der Pfad zur Datenhaltung definiert2. Ein SQL- oder Python-Skript erzeugt die Verzeichnisstruktur, initialisiert das Tabellenschema in /data/app.db und fügt mindestens ein Administratorkonto direkt in die Tabelle user ein2. Damit entfällt die Notwendigkeit, den einmaligen Setup-Token aus den Anwendungslogs auszulesen.

### **Phase 2: Daemon-Initialisierung (CLI / Docker)**

Anschließend wird der Dienst im Headless-Modus gestartet (z. B. via cptr run \--host 0.0.0.0 \--port 8000 \--headless oder über einen entsprechenden Docker-Container)1. Der Uvicorn-Server greift beim Start direkt auf die bereits präparierte Datenbank app.db zu1.

### **Phase 3: Runtime API Orchestration (REST API Calls)**

Nach dem Start führt ein Orchestrierungsskript HTTP-Anfragen gegen die lokalen REST-Schnittstellen aus:

> 1. Authentifizierung an POST /api/v1/auth/login mit den injizierten Anmeldedaten zur Anforderung eines JWT-Tokens2.  
> 2. Erzeugung eines Gateway-API-Schlüssels über POST /api/v1/admin/gateway/keys4.  
> 3. Injektion von Modell-Providern, MCP-Server-Verbindungen und Messaging-Bots über die Admin-Endpunkte in cptr/routers/admin.py5.

### **End-to-End Automatisierungsskript**

Das folgende Skript setzt dieses dreistufige Konzept in einem eigenständigen Python-Skript um:

Python  
import os  
import time  
import sqlite3  
import uuid  
import requests  
from datetime import datetime  
from passlib.hash import bcrypt

\# \--- KONFIGURATION \---  
BASE\_URL \= "http://localhost:8000"  
DB\_PATH \= os.path.expanduser("\~/.cptr/app.db")  
ADMIN\_USER \= "admin\_auto"  
ADMIN\_EMAIL \= "admin@automation.local"  
ADMIN\_PASS \= "ComplexAutoPass2026\!"

def bootstrap\_sqlite\_admin():  
    """Injiziert den Administrator-Account direkt in die SQLite-Datenbank."""  
    os.makedirs(os.path.dirname(DB\_PATH), exist\_ok=True)  
    conn \= sqlite3.connect(DB\_PATH)  
    cursor \= conn.cursor()

    cursor.execute("""  
        CREATE TABLE IF NOT EXISTS user (  
            id TEXT PRIMARY KEY,  
            username TEXT UNIQUE,  
            email TEXT,  
            password\_hash TEXT,  
            role TEXT,  
            is\_active INTEGER,  
            created\_at TEXT  
        )  
    """)

    cursor.execute("SELECT id FROM user WHERE username \= ?", (ADMIN\_USER,))  
    if not cursor.fetchone():  
        user\_id \= str(uuid.uuid4())  
        pwd\_hash \= bcrypt.hash(ADMIN\_PASS)  
        now \= datetime.utcnow().isoformat()  
        cursor.execute("""  
            INSERT INTO user (id, username, email, password\_hash, role, is\_active, created\_at)  
            VALUES (?, ?, ?, ?, 'admin', 1, ?)  
        """, (user\_id, ADMIN\_USER, ADMIN\_EMAIL, pwd\_hash, now))  
        conn.commit()  
        print("\[Bootstrap\] Admin-Konto in SQLite injiziert.")  
    else:  
        print("\[Bootstrap\] Admin-Konto existiert bereits.")  
    conn.close()

def wait\_for\_server():  
    """Wartet, bis das cptr-Backend erreichbar ist."""  
    print("\[Network\] Warte auf Server-Start...")  
    for \_ in range(30):  
        try:  
            r \= requests.get(f"{BASE\_URL}/", timeout=2)  
            if r.status\_code in \[200, 404, 401\]:  
                print("\[Network\] Backend ist erreichbar.")  
                return True  
        except requests.exceptions.ConnectionError:  
            time.sleep(1)  
    raise RuntimeError("Server konnte nicht innerhalb des Timeouts erreicht werden.")

def configure\_system\_via\_api():  
    """Meldet sich an und sendet administrative Mutationen über REST."""  
    session \= requests.Session()  
      
    \# 1\. Login  
    login\_resp \= session.post(f"{BASE\_URL}/api/v1/auth/login", json={  
        "username": ADMIN\_USER,  
        "password": ADMIN\_PASS  
    })  
    login\_resp.raise\_for\_status()  
    jwt\_token \= login\_resp.json().get("token")  
    headers \= {"Authorization": f"Bearer {jwt\_token}"}  
    print("\[API\] Erfolgreich authentifiziert. JWT-Token erhalten.")

    \# 2\. Gateway API-Key generieren  
    gw\_resp \= session.post(  
        f"{BASE\_URL}/api/v1/admin/gateway/keys",   
        json={"name": "AutomationKey"},   
        headers=headers  
    )  
    if gw\_resp.status\_code \== 200:  
        api\_key \= gw\_resp.json().get("key")  
        print(f"\[API\] Generierter Gateway-Key: {api\_key}")

    \# 3\. Audio & Transkription (Whisper) einstellen  
    audio\_config \= {  
        "stt\_enabled": True,  
        "stt\_provider": "openai",  
        "stt\_base\_url": "https://api.openai.com/v1",  
        "stt\_model": "whisper-1"  
    }  
    audio\_resp \= session.post(  
        f"{BASE\_URL}/api/v1/admin/audio",   
        json=audio\_config,   
        headers=headers  
    )  
    print(f"\[API\] Audio-Konfiguration angewendet: Status {audio\_resp.status\_code}")

if \_\_name\_\_ \== "\_\_main\_\_":  
    bootstrap\_sqlite\_admin()  
    wait\_for\_server()  
    configure\_system\_via\_api()

## **Fazit und Sicherheitshinweise**

Die Architektur von Open WebUI Computer ermöglicht eine vollständige Automatisierung ohne manuellen Einrichtungsaufwand über die Kombination von SQLite-Bootstrapping, CLI-Startparametern und administrativen REST-Endpunkten2.  
Da ein authentifizierter Benutzer auf einer cptr-Instanz dieselben Systemrechte wie ein lokaler Benutzer an der Konsole besitzt (Zugriff auf Dateisystem, Shell und Prozessumgebung)6, sollten automatisierte Instanzen grundsätzlich in isolierten Containern ausgeführt werden1. Zur Einhaltung von Compliance-Vorgaben empfiehlt sich die strikte Aktivierung des Audit-Loggings (CPTR\_AUDIT\_LOG\_LEVEL), um alle verändernden API-Zugriffe nachvollziehbar zu protokollieren2.

#### **Referenzen**

> 1. open-webui/computer: Your Computer. Anywhere. \- GitHub, [https://github.com/open-webui/computer](https://github.com/open-webui/computer)  
> 2. docs/docs/features/computer/index.md at main · open-webui/docs \- GitHub, [https://github.com/open-webui/docs/blob/main/docs/features/computer/index.md](https://github.com/open-webui/docs/blob/main/docs/features/computer/index.md)  
> 3. bug: cryptography 49.0.0 Rust bindings fail at runtime on Python 3.14 (Termux/Android) · Issue \#150 · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/issues/150](https://github.com/open-webui/computer/issues/150)  
> 4. cptr.mdx \- Open WebUI Computer \- GitHub, [https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx](https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx)  
> 5. MCP optional extra not installed in Docker image — MCP tool servers fail silently out of the box · Issue \#62 · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/issues/62](https://github.com/open-webui/computer/issues/62)  
> 6. Open WebUI Computer, [https://docs.openwebui.com/ecosystem/computer/](https://docs.openwebui.com/ecosystem/computer/)  
> 7. Releases · open-webui/open-webui \- GitHub, [https://github.com/open-webui/open-webui/releases](https://github.com/open-webui/open-webui/releases)  
> 8. Releases · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/releases](https://github.com/open-webui/computer/releases)  
> 9. computer/CHANGELOG.md at main · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/CHANGELOG.md](https://github.com/open-webui/computer/blob/main/CHANGELOG.md)