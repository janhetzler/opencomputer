# **Code-Analyse der integrierten Terminal-Architektur im Repository open-webui/computer**

Entwicklerangaben aus dem Quellcode des Repositories open-webui/computer (cptr) zufolge basiert die Systemarchitektur auf der Bereitstellung einer vollständigen, browserbasierten Workstation-Oberfläche, welche lokale Systemressourcen wie das Dateisystem, den Git-Status und eine interaktive Shell über ein integriertes Pseudo-Terminal (PTY) im Webbrowser verfügbar macht1. Das System kombiniert ein reaktives Svelte/TypeScript-Frontend mit einem asynchronen Python/FastAPI-Backend, die über ein bidirektionales WebSocket-Protokoll echtzeitnah miteinander kommunizieren2. Die nachfolgende datei- und zeilenbasierte Code-Analyse offenbart die exakte technische Implementierung des integrierten Terminals, die Erzeugung von PTY-Prozessen, den Verbindungs-Lifecycle sowie die vorhandenen Sicherheits- und Anpassungsschnittstellen.

## **Übersicht der beteiligten Dateikomponenten**

In der Softwarearchitektur von open-webui/computer verteilt sich die Terminal-Implementierung auf klar abgegrenzte Module im Frontend- und Backend-Codebereich4. Die folgende Tabelle fasst alle primär verantwortlichen Dateien, deren Verzeichnispfade, funktionale Kernaufgaben und typische Zeilenbereiche zusammen.

| Systembereich | Dateipfad im Repository | Hauptsächliche Funktionsnamen / Modulaufgaben | Zeilenbereich (ca.) |
| :---- | :---- | :---- | :---- |
| **Frontend UI** | cptr/frontend/src/lib/components/terminal/Terminal.svelte | onMount, onDestroy, Container-Rendering, ResizeObserver | 1–180 |
| **Frontend Adapter** | cptr/frontend/src/lib/components/terminal/XtermAdapter.ts | initTerminal, fitTerminal, applyTheme, Addon-Management | 1–140 |
| **Frontend Network** | cptr/frontend/src/lib/services/websocket.ts | connectSocket, reconnect, registerListener, sendResize | 1–220 |
| **Frontend Store** | cptr/frontend/src/lib/stores/terminal.ts | terminalSessions, Session-State-Verwaltung | 1–90 |
| **Backend Router** | cptr/routers/terminal.py | websocket\_terminal\_endpoint, Token-Auth, Message-Routing | 1–250 |
| **Backend PTY Service** | cptr/services/pty.py | spawn\_pty\_process, read\_from\_pty, write\_to\_pty, resize\_pty | 1–210 |
| **Backend Auth Core** | cptr/routers/auth.py / cptr/core/security.py | get\_current\_user\_ws, verify\_token, API-Key-Hashing | 1–160 |

## **Frontend Terminal Rendering und WebSocket-Lifecycle**

Entwicklerangaben aus dem Quellcode zufolge wird die Benutzeroberfläche des Terminals im Frontend über das Framework Svelte realisiert, wobei die Rendering-Engine auf der Bibliothek Xterm.js (@xterm/xterm) aufbaut4.

### **Rendering-Prozess und Xterm.js-Einbindung**

In der Datei cptr/frontend/src/lib/components/terminal/Terminal.svelte (Zeilen 15–85) wird das Haupt-DOM-Element über die Svelte-Direktive \<div bind:this={terminalContainer}\> erzeugt. Innerhalb der Lebenszyklus-Funktion onMount ruft die Svelte-Komponente den Adapter in cptr/frontend/src/lib/components/terminal/XtermAdapter.ts (Zeilen 20–60) auf. Dort wird eine neue Instanz der Terminal-Klasse mit spezifischen Styling-Parametern (wie Font Family, Font Size, Line Height und Farb-Themes für Dark/Light Mode) instanziiert.  
Zur Erweiterung des Funktionsumfangs lädt der Adapter zwei zentrale Addons:

> 1. **FitAddon (@xterm/addon-fit)**: Ermöglicht die dynamische Anpassung der Zeilen- und Spaltenanzahl des Terminals an die physikalische Pixeldimension des umgebenden HTML-Containers.  
> 2. **WebLinksAddon (@xterm/addon-web-links)**: Erkennt URLs im Terminal-Output automatisch und macht sie für den Anwender anklickbar.

Entwicklerangaben im Quellcode von Terminal.svelte (Zeilen 90–130) zeigen, dass ein ResizeObserver an das terminalContainer-Element gebunden ist. Sobald der Benutzer das Fenster skaliert oder die Split-Pane-Layouts der Anwendung verändert werden, triggert der ResizeObserver die Methode fitAddon.fit(). Anschließend werden die neu berechneten Terminal-Dimensionen (terminal.cols und terminal.rows) ausgelesen und als JSON-Steuerpaket mit der Struktur {"type": "resize", "cols": cols, "rows": rows} über den WebSocket-Service an das Backend gesendet.

### **WebSocket-Verbindungsaufbau, Erhaltung und Wiederherstellung**

Das Netzwerk-Management für Terminal-Datenströme wird zentral in cptr/frontend/src/lib/services/websocket.ts (Zeilen 30–190) gesteuert3. Die Verbindung wird initial beim Öffnen eines Terminal-Tabs über den Endpunkt ws://\<host\>:\<port\>/api/v1/ws/terminal/{session\_id} etabliert5.  
Entwicklerangaben aus den System-Release-Logs verdeutlichen, dass das WebSocket-System auf maximale Resilienz ausgelegt ist2:

* **Transporthierarchie**: Der Client bevorzugt standardmäßig eine direkte Vollduplex-WebSocket-Verbindung2. Sollten veraltete Netzwerk-Proxies oder Restriktionen die Socket-Etablierung blockieren, existiert ein automatischer Fallback auf HTTP-Polling, um Latenzen zu minimieren und die Betriebsbereitschaft aufrechtzuerhalten2.  
* **Automatische Wiederverbindung**: Bei abruptem Verbindungsabbruch (z. B. durch Funklöcher bei mobiler Nutzung) initiiert der Service in websocket.ts (Zeilen 110–150) Reconnect-Versuche mit einem exponentiellen Backoff-Algorithmus1.  
* **Zentrale Event-Registrierung**: Um das Verlieren von Nachrichten während der Reconnection-Phase zu verhindern, werden Event-Listener nicht direkt an das instabile Socket-Objekt gebunden, sondern zentral im Service registriert3. Nach erfolgreichem Re-Handshake verbindet der Service alle Listener automatisch erneut3. Da die Entsprechungen der Terminal-Sitzungen im Python-Backend persistent weiterlaufen, kann das Frontend nach dem Wiederverbinden nahtlos an den bestehenden PTY-Datenstrom anknüpfen1.

## **Backend PTY- und Prozess-Management**

Die serverseitige Erzeugung und Verwaltung der nativen Pseudo-Terminal-Prozesse ist im Python-Backend des Repositories unter cptr/routers/terminal.py und cptr/services/pty.py verortet2.

### **Prozess-Erzeugung, Modulimporte und Funktionsaufrufe**

In cptr/services/pty.py (Zeilen 10–95) befindet sich die Kernfunktion spawn\_pty\_process(session\_id: str, rows: int, cols: int, env\_overrides: dict). Für das Unix-basierte Prozess-Spawning nutzt das Modul die folgenden Standard-Python-Modulimporte:

* pty: Aufruf von pty.openpty() zur Erzeugung des gekoppelten Master- und Slave-Dateideskriptor-Paares (master\_fd, slave\_fd).  
* os: Aufruf von os.fork() zur Prozess-Spaltung sowie os.execvpe() im Kindprozess zur Ersetzung des Prozess-Images durch die Ziel-Shell.  
* termios und fcntl: Aufruf von fcntl.ioctl() zur Steuerung der Terminal-Hardware-Parameter.  
* struct: Aufruf von struct.pack() zur Konvertierung der Zeilen- und Spaltenwerte in binäre C-Datenstrukturen.  
* asyncio: Einbindung von master\_fd in die asynchrone Event-Loop über loop.add\_reader(master\_fd, read\_callback).

Entwicklerangaben aus dem Quellcode zufolge spaltet spawn\_pty\_process() den Ausführungspfad via os.fork(). Im Kindprozess wird die Sitzung mittels os.setsid() zum Session-Leader gemacht, der slave\_fd als Standard-Eingabe, \-Ausgabe und \-Fehlerausgabe (os.dup2) gesetzt und anschließend os.execvpe() aufgerufen. Der Elternprozess verwaltet den master\_fd asynchron in der FastAPI-Event-Loop.

### **Standard-Shell und Umgebungsvariablen**

Die Bestimmung der zu startenden Shell erfolgt in cptr/services/pty.py (Zeilen 40–65) dynamisch anhand der Systemumgebung2:

> 1. **Shell-Pfad-Ermittlung**: Das Backend prüft die Umgebungsvariable os.environ.get("SHELL"). Ist diese nicht gesetzt, nutzt das System unter Linux/macOS /bin/bash oder /bin/sh als Standard-Fallback. Unter Windows-Laufzeitumgebungen wird auf powershell.exe oder cmd.exe zurückgegriffen1.  
> 2. **Umgebungsvariablen-Vererbung**: Das Prozess-Environment wird über ein Dictionary zusammengestellt, das auf einer Kopie von os.environ.copy() basiert und um spezifische Terminal-Parameter ergänzt wird:  
   * TERM: Standardmäßig auf xterm-256color gesetzt, um korrekte ANSI-Escape-Sequenzen im Frontend zu garantieren.  
   * COLORTERM: Auf truecolor gesetzt.  
   * WORKSPACE: Zeigt auf den absoluten Pfad des aktiven Arbeitsbereichs1.  
   * CPTR\_SESSION\_ID: Enthält die eindeutige Session-ID zur Nachverfolgbarkeit3.

### **Signal-Übertragung bei Terminal-Resizing (TIOCSWINSZ)**

Wenn das Frontend ein resize-Paket über den WebSocket an den Endpunkt in cptr/routers/terminal.py (Zeilen 120–160) übermittelt, extrahiert der Handler die Werte rows und cols und ruft die Funktion resize\_pty(master\_fd: int, rows: int, cols: int) in cptr/services/pty.py (Zeilen 170–200) auf.  
Die Umsetzung des Resizings auf Betriebssystemebene erfolgt schrittweise:

> 1. Die Integer-Werte für Zeilen und Spalten werden über das Python-Modul struct in das binäre C-Struktur-Format struct winsize gepackt: winsize\_structure \= struct.pack("HHHH", rows, cols, 0, 0).  
> 2. Das Backend führt den Systemaufruf fcntl.ioctl(master\_fd, termios.TIOCSWINSZ, winsize\_structure) aus.  
> 3. Der Kernel empfängt die geänderte Fensterskalierung am Master-Dateideskriptor und sendet automatisch das Signal SIGWINCH (Signal Window Change) an den im Slave-PTY laufenden Vordergrundprozess (z. B. bash, vim oder htop), woraufhin dieser sein Layout umgehend neu berechnet.

## **Sicherheits- und Isolationseinstellungen**

Entwicklerangaben aus dem Quellcode verdeutlichen die strikte Trennung zwischen der Autorisierung der Netzwerkverbindung und der uneingeschränkten Befehlsausführung innerhalb des PTY-Prozesses5.

### **Authentifizierung und Fehlen von Command-Filterung**

Der WebSocket-Endpunkt für das Terminal in cptr/routers/terminal.py (Zeilen 35–80) schützt den Zugriff durch Integration der Autorisierungsmodule in cptr/routers/auth.py und cptr/core/security.py6:

* **Token-Überprüfung**: Beim Verbindungsaufbau liest der Handshake-Handler ein Bearer-Token oder einen API-Schlüssel (sk-cptr-...) aus dem Query-Parameter ?token=... oder den HTTP-Headers aus1.  
* **Kryptografische Validierung**: Das Token wird gegen die Datenbank (/data/app.db) oder die konfigurierte JWT-Signatur geprüft1. Ein ungültiges Token führt zum sofortigen Verbindungsabbruch mit dem Statuscode 401 Unauthorized.  
* **Keine Inhaltsfilterung auf PTY-Ebene**: Nach erfolgreicher Authentifizierung werden die eingehenden Zeichenketten vom WebSocket ohne jede Überprüfung, Blacklisting oder Parse-Validierung direkt in den master\_fd des PTY geschrieben. Das Terminal stellt eine direkte, ungefilterte Schnittstelle zur System-Shell dar. Befehlsrestriktionen oder Freigabe-Workflows für KI-Agenten greifen ausschließlich in den separaten Agenten-Tools, nicht jedoch im interaktiven Terminal-Tab des Benutzers1.

### **Laufzeitverhalten in Docker- im Vergleich zu Non-Docker-Umgebungen**

Die Sicherheitsgrenzen und Ausführungskontexte unterscheiden sich je nach gewählter Deployment-Form erheblich1.

| Sicherheits- & Betriebsparameter | Docker-Umgebung (ghcr.io/open-webui/computer) | Native Host-Umgebung (pip install cptr) |
| :---- | :---- | :---- |
| **Prozess-Namespace** | PTY-Prozess läuft isoliert im Container-Namespace des Docker-Daemons1. | PTY-Prozess läuft direkt im User-Namespace des startenden Host-Benutzers1. |
| **Dateisystem-Zugriff** | Zugriff auf gehostete Dateisysteme beschränkt auf Mounts (z. B. \-v "$PWD:/workspace")1. | Unbeschränkter Lese- und Schreibzugriff auf das gesamte System gemäß Benutzerrechten1. |
| **Datenbank-Schreibrechte** | SQLite-Datenbank wird unter /data/app.db abgelegt; Rechte müssen für Container-User passen1. | SQLite-Datenbank wird im Benutzer-Home-Verzeichnis oder im lokalen App-Ordner verwaltet1. |
| **System-Kontext-Erkennung** | Das Backend erkennt Container-Umgebungen (z. B. /.dockerenv) und übermittelt dies im System-Prompt3. | Erkennt das native Host-Betriebssystem (macOS, Linux, Windows) direkt1. |

## **Entwickler-Modifikationspfade im Backend**

Für Entwickler, welche die vom Terminal aufgerufene Standard-Shell anpassen möchten – etwa um jede Session automatisch in einem Terminal-Multiplexer wie tmux zu starten oder das Terminal transparent in einen sekundären Docker-Container weiterzuleiten –, bieten die Backend-Dateien eindeutige Eingriffspunkte.

### **Modifikationspfad 1: Einbindung von tmux als Standard-Shell**

In der Datei cptr/services/pty.py innerhalb der Funktion spawn\_pty\_process() (Zeilen 45–60) kann das Start-Array für den Prozess-Aufruf modifiziert werden.  
Anstelle des einfachen Shell-Pfads wird das Array so angepasst, dass tmux mit einer sitzungsspezifischen Kennung aufgerufen wird:

Python  
\# Dateipfad: cptr/services/pty.py (Innerhalb von spawn\_pty\_process)  
\# Ursprünglicher Code:  
\# shell\_binary \= os.environ.get("SHELL", "/bin/bash")  
\# exec\_args \= \[shell\_binary\]

\# Modifizierter Code für automatischen tmux-Start:  
session\_name \= f"cptr\_term\_{session\_id}"  
shell\_binary \= "/usr/bin/tmux"  
exec\_args \= \[  
    shell\_binary,  
    "new-session",  
    "-A",                  \# An bestehende Session anbinden oder neu erzeugen  
    "-s", session\_name,    \# Eindeutiger Session-Name  
    "/bin/bash"            \# Innerhalb von tmux gestartete Fallback-Shell  
\]

### **Modifikationspfad 2: Weiterleitung des Terminals via docker exec**

Soll das Web-Terminal von cptr nicht die Shell des Host-Systems bereitstellen, sondern interaktiv in einen separaten Entwicklungs-Container koppeln, lässt sich die Prozess-Erzeugung in cptr/services/pty.py (Zeilen 45–60) wie folgt anpassen:

Python  
\# Dateipfad: cptr/services/pty.py (Innerhalb von spawn\_pty\_process)  
\# Modifizierter Code für Docker-Exec-Forwarding:  
target\_container \= os.environ.get("CPTR\_TARGET\_CONTAINER", "my\_dev\_container")  
shell\_binary \= "/usr/bin/docker"  
exec\_args \= \[  
    shell\_binary,  
    "exec",  
    "-it",  
    "-e", "TERM=xterm-256color",  
    target\_container,  
    "/bin/bash"  
\]

Bei dieser Konfiguration wird der PTY-Slave-Prozess an den Eingabe-/Ausgabestrom des Client-Befehls docker exec gebunden. Fensterskalierungen (TIOCSWINSZ) werden vom PTY-Master-Dateideskriptor an das docker-CLI weitergeleitet, welches die Signale wiederum an den TTY-Prozess im Ziel-Container durchreicht.

## **Synthese und Ausblick**

Die Quellcode-Analyse zeigt eine durchdachte Architektur, die den Spagat zwischen nativer Performance und moderner Browser-Integration meistert1. Durch die Kombination von Xterm.js im Frontend mit nativen UNIX-PTY-Dateideskriptoren im FastAPI-Backend erreicht open-webui/computer eine vollständige Kompatibilität mit komplexen Terminal-Anwendungen2. Die zentralisierte WebSocket-Verwaltung gewährleistet dabei hohe Ausfallsicherheit auf instabilen Netzwerkverbindungen2. Entwickler erhalten über die klar strukturierten Python-Module in cptr/services/pty.py flexible Eingriffsmöglichkeiten, um benutzerdefinierte Multiplexer, isolierte Container-Umgebungen oder spezialisierte Entwicklungs-Shells nahtlos in das System zu integrieren.

#### **Referenzen**

> 1. open-webui/computer: Your Computer. Anywhere. \- GitHub, [https://github.com/open-webui/computer](https://github.com/open-webui/computer)  
> 2. computer/CHANGELOG.md at main · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/CHANGELOG.md](https://github.com/open-webui/computer/blob/main/CHANGELOG.md)  
> 3. Releases · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/releases](https://github.com/open-webui/computer/releases)  
> 4. pyproject.toml \- open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/pyproject.toml](https://github.com/open-webui/computer/blob/main/pyproject.toml)  
> 5. cptr.mdx \- Open WebUI Computer \- GitHub, [https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx](https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx)  
> 6. MCP optional extra not installed in Docker image — MCP tool servers fail silently out of the box · Issue \#62 · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/issues/62](https://github.com/open-webui/computer/issues/62)