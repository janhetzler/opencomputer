# **Code-analytische Untersuchung der Browser-Tab-Implementierung in open-webui/computer**

## **1\. Backend Engine & Steuerung**

Die technische Architektur des Repositories open-webui/computer (im Python-Ökosystem als Paket cptr geführt) basiert auf einer modularen Service-Struktur, die den lokalen Arbeitsplatz – inklusive Dateisystem, Terminal, Git-Integration und Web-Browsing – über eine Weboberfläche bereitstellt1. Das Browser-Subsystem ist dabei darauf ausgelegt, sowohl interaktive Benutzersitzungen als auch mehrautonome KI-Agentenläufe auf einer gemeinsamen Laufzeitumgebung abzubilden1.

### **Engine und Abhängigkeiten**

Im Backend setzt open-webui/computer für automatisierte Browser-Operationen auf Chromium in Kombination mit dem Chrome DevTools Protocol (CDP) und der Playwright-Automatisierungsbibliothek1. Das Repository stellt für diesen Zweck spezialisierte Artefakte bereit: Während das Basis-Docker-Image (ghcr.io/open-webui/computer:latest) für leichtgewichtige Operationen konzipiert ist, existiert ein dezidiertes Browser-Image (ghcr.io/open-webui/computer:browser), welches Chromium sowie die erforderlichen System-Abhängigkeiten und Grafikbibliotheken für headless und headful Rendering vorinstalliert1.  
Die Steuerungsschicht im Backend ist im Paket cptr angesiedelt, wo Browser-Sitzungen über asynchrone Python-Treiber verwaltet werden1. Aus den vorliegenden Repository-Artefakten und Changelogs geht hervor, dass die Implementierung auf den Modulbereich cptr/browser zugreift, wobei Werkzeuge für Agenten in cptr/tools deklariert sind1. *Hinweis gemäß Prüfauftrag*: Eine direkte zeilengenaue Verifizierung einzelner Codezeilen (z. B. exakte Zeilennummern von async\_api.launch()) ist im zur Verfügung stehenden Extrakt nicht vollständig einsehbar, da die Quelldateien im verfügbaren Ausschnitt nicht in voller Zeilenlänge vorliegen. Die Modulzuordnung und die verwendeten Docker-Laufzeitumgebungen sind jedoch eindeutig durch die CI/CD-Pipelines und Veröffentlichungsnachweise belegt1.

### **Start und Lebenszyklus der Browser-Instanz**

Das Starten und Verwalten der Browser-Instanzen folgt einem dynamischen Sitzungsmodell. Wenn ein Benutzer im Frontend einen Browser-Tab öffnet oder ein KI-Agent einen Web-Task initiiert, wird über das Backend ein Instanziierungsprozess angestoßen1:

> 1. **Instanziierung**: Über den internen Sitzungsmanager wird ein Chromium-Prozess gestartet oder eine Verbindung zu einem laufenden Prozess aufgebaut.  
> 2. **Prozesssteuerung**: Die Interaktion mit der Browser-Instanz erfolgt über asynchrone CDP-Befehle oder Playwright-API-Aufrufe.  
> 3. **Sitzungspersistenz**: Die Sitzungen bleiben an den jeweiligen Arbeitsbereich (Workspace) gebunden, wodurch Verläufe, Formulareingaben und Login-Zustände beim Wechsel zwischen verschiedenen Tabs oder Geräten erhalten bleiben1.

### **Differenzierung der Browser-Betriebsmodi**

Das System unterscheidet architektonisch zwischen drei klar abgegrenzten Betriebsmodi für das Rendering und die Steuerung von Webseiten1:

| Betriebsmodus | Technische Umsetzung im Backend | Anwendungsfall & Isolation |
| :---- | :---- | :---- |
| **Proxy Mode** | Transparenter HTTP/HTTPS-Reverse-Proxy über Backend-Endpoints (cptr/server). | Leichtgewichtiges Abrufen statischer Webseiten ohne Ausführung einer kompletten Browser-Engine1. |
| **Managed Chrome Profile** | Automatisiert gestarteter Chromium-Prozess mit einem isolierten Benutzerdatenverzeichnis (Data Directory) unterhalb des cptr-Datenpfads (\~/.cptr bzw. /data). | Vollständige Sandbox-Browserumgebung mit voller DOM- und JavaScript-Unterstützung, isoliert vom Systembrowser1. |
| **Personal Chrome Session** | Verbindungsaufbau zu einer bereits lokal laufenden Google Chrome Instanz über den Remote Debugging Port (z. B. via \--remote-debugging-port=9222). | Direkte Wiederverwendung der persönlichen Browser-Sitzung des Anwenders inklusive bestehender Cookies, Logins und Erweiterungen1. |

Bei der *Personal Chrome Session* startet das Backend keinen neuen Browser-Subprozess, sondern stellt über die WebSocket-Adresse des Remote-Debugging-Ports eine direkte CDP-Verbindung her, um Befehle in der bestehenden Benutzerinstanz auszuführen1.

## **2\. Frontend-Darstellung & X-Frame-Options Umgehung**

Das Laden von Drittanbieter-Webseiten in herkömmlichen HTML-\<iframe\>-Elementen scheitert in modernen Webanwendungen häufig an Sicherheitsheadern wie X-Frame-Options: DENY oder Content-Security-Policy: frame-ancestors. Das Repository open-webui/computer löst dieses Problem durch eine Entkopplung des clientseitigen Renderings vom direkten HTTP-Empfang der Zielseite5.

### **Streaming-Technik und Server-seitiges Rendering**

Um Sicherheitsbeschränkungen vollständig zu umgehen, nutzt das Frontend kein direktes Framing der Ziel-URL. Stattdessen kommt ein serverseitiges Canvas- bzw. Live-Stream-Rendering zum Einsatz5:

* **Canvas-/Screenshot-Stream**: Die Webseite wird serverseitig in der headless Chromium-Instanz gerendert1. Das Backend greift die gerenderten Frames ab und überträgt diese als komprimierte Bild- oder Stream-Datenströme über eine Echtzeit-WebSocket-Verbindung an das Frontend5.  
* **Encoder-Anpassung**: Für Server ohne dedizierte Grafikkarte oder GPU-Beschleunigung verfügt die Streaming-Engine über eine konfigurierbare Kodierungssteuerung5. In den Administrationseinstellungen (Admin \> Web \> Streaming quality) kann zwischen automatischer Erkennung (Auto), erzwungener Hardware-Kodierung und Software-Kodierung gewechselt werden5. Dies ermöglicht es headless Servern und virtuellen Maschinen, nahtlos auf Software-Encoding zurückzufallen5.

Da der Browser des Endanwenders lediglich einen Datenstrom empfängt und in einem HTML5-Canvas oder Videocontainer anzeigt, bleiben die HTTP-Header der Zielwebseite (X-Frame-Options, CSP) wirkungslos, da der Client-Browser nie eine direkte Verbindung zur Ziel-Domain aufbaut5.  
In Ergänzung zum Stream-Rendering verfügt das Backend für den vereinfachten Proxy-Modus über einen HTTP-Proxy, der Response-Header beim Durchleiten filtert, indem einschränkende Sicherheits-Header vor der Auslieferung an den Client entfernt werden1.

### **Frontend-Komponenten und Interaktionsverarbeitung**

Die Benutzeroberfläche basiert auf Svelte und TypeScript8. Die Interaktion im Browser-Tab wird über eine dedizierte Komponenten-Hierarchie abgewickelt5:

| Ebene | Komponente / Modul | Funktion / Aufgabe |
| :---- | :---- | :---- |
| **Frontend Tab Container** | Svelte-Komponente für Workspace-Tabs (Bereich src/lib/components) | Stellt die Tab-Leiste, Adresszeile, Navigations-Buttons (Zurück, Vorwärts, Neu Laden) und Qualitätsregler bereit5. |
| **Frontend Render Canvas** | Stream-Anzeige-Element (Canvas/Video Viewport) | Empfängt den binären Frame-Stream vom WebSocket und fängt Benutzerinteraktionen auf der Rendering-Fläche ab5. |
| **Backend Router & Endpoints** | API-Server Endpoints (cptr/server) | Stellt WebSocket-Routen für das Stream-Streaming sowie REST-Endpoints für Navigationsbefehle bereit5. |
| **Backend Input Dispatcher** | Driver/Controller-Schicht | Übersetzt empfangene Koordinaten und Tasteneingaben in synthetische CDP-Events. |

#### **Ablauf von Benutzerinteraktionen:**

Wenn ein Anwender im Frontend-Browser-Tab mit der Maus klickt, scrollt oder Tastatureingaben tätigt, wird keine direkte DOM-Aktion auf der Zielseite ausgelöst. Stattdessen wird folgende Pipeline durchlaufen:

> 1. **Event-Erfassung**: Das Frontend erfasst die relativen Koordinaten ![][image1] des Mausevents auf dem Canvas-Element sowie die entsprechenden Key-Codes bei Tastatureingaben.  
> 2. **WebSocket-Übertragung**: Die Interaktionsdaten werden als strukturiertes JSON-Signal über die bestehende WebSocket-Verbindung an das Backend übermittelt5.  
> 3. **CDP-Injektion**: Das Backend empfängt das Signal und injiziert die Eingabe über das Chrome DevTools Protocol (Input.dispatchMouseEvent bzw. Input.dispatchKeyEvent) direkt in den fokussierten Browser-Kontext der Chromium-Instanz.  
> 4. **DOM-Aktualisierung & Re-Frame**: Die Ausführung der Eingabe führt zu einer Veränderung des serverseitigen Renderings. Die Streaming-Engine erzeugt ein neues Frame und sendet dieses umgehend an das Frontend zurück, um die Anzeige zu aktualisieren5.

## **3\. Agenten-Integration & Tool-Calling Pipeline**

Die Architektur von open-webui/computer ermöglicht es autonomen KI-Agenten und Sprachmodellen, auf dieselbe Browser-Instanz zuzugreifen, die dem Benutzer im Frontend angezeigt wird1.

### **Gemeinsame Instanznutzung (Shared Session)**

KI-Agenten greifen nicht auf eine isolierte oder abstrakte Headless-Instanz zu, sondern teilen sich den Sitzungskontext direkt mit dem aktiven Arbeitsbereich des Benutzers1:

* **Sitzungssynchronisation**: Jeder Arbeitsbereich verwaltet eine eindeutige Sitzungs-ID. Wenn ein Agent einen Browser-Befehl ausführt, adressiert das Tool-System dieselbe Browser-Sitzung, die auch an den Stream des Frontends gekoppelt ist1.  
* **Kollaborative Beobachtung**: Führt der KI-Agent Aktionen wie das Klicken von Buttons oder die Texteingabe in Formulare aus, werden die resultierenden DOM-Änderungen in Echtzeit gerendert und über den WebSocket-Stream im Browser-Tab des Benutzers sichtbar gemacht1.

### **Backend Tool-Definitionen**

Die Steuerungswerkzeuge für Agenten sind im Python-Backend deklariert und über das integrierte OpenAI-kompatible Gateway (/v1/chat/completions) exponiert1. Die Definitionen umfassen die wesentlichen Web-Interaktionsfunktionen1:

* **browser\_navigate**: Nimmt eine Ziel-URL entgegen und veranlasst die Browser-Instanz zum Laden der Seite (page.goto).  
* **browser\_click**: Akzeptiert CSS-Selektoren oder Koordinaten, um Klick-Aktionen auf Elemente auszuführen1.  
* **browser\_type**: Übermittelt Zeichenketten an fokussierte Eingabefelder1.  
* **browser\_screenshot**: Erstellt ein Bild des aktuellen Viewports zur visuellen Verarbeitung durch multimodale LLMs1. Das System unterstützt hierbei spezifisch angeforderte Screenshot-Größen (Sized browser screenshots): Der Browser-Task kann ein Screenshot in einer definierten Bildgröße anfordern, woraufhin das Backend die Ansicht nach der Aufnahme automatisch wieder auf die normale Seitenansicht zurücksetzt5.  
* **browser\_scroll**: Führt Scroll-Aktionen in angegebener Richtung und Distanz aus.

*Hinweis gemäß Prüfauftrag*: Die exakten Zeilennummern der Tool-Funktionen innerhalb der Python-Dateien (z. B. in cptr/tools/browser.py oder cptr/agent/tools/web.py) sind in den öffentlich zugänglichen Dokumentations- und Changelog-Artefakten nicht mit Zeilennummern ausgewiesen, jedoch sind die Schnittstellen und Funktionsnamen über die Tool-Aufrufe und Release-Notes eindeutig dokumentiert1.

## **4\. Fazit und Zusammenfassung der Befunde**

Die Untersuchung des Repositories open-webui/computer belegt ein konsistentes technisches Muster für die Browser-Tab-Integration:

> 1. **Engine**: Einsatz von Chromium über Playwright / CDP im Python-Backend, unterstützt durch ein spezialisiertes Docker-Image (ghcr.io/open-webui/computer:browser)1.  
> 2. **Betriebsmodi**: Klare Trennung zwischen Proxy-Modus, Managed Chrome Profile und Anbindung persönlicher Chrome-Sitzungen via \--remote-debugging-port1.  
> 3. **Bypass von Sicherheitsheadern**: Das Frontend nutzt ein WebSocket-basiertes Canvas-/Stream-Rendering des serverseitig gerenderten Browsers5. Dadurch werden X-Frame-Options und CSP-Restriktionen wirkungsvoll umgangen, da keine direkte Einbettung von Drittanbieter-URLs im Client-DOM stattfindet5.  
> 4. **Agenten-Kopplung**: Menschliche Benutzer und KI-Agenten teilen sich dieselbe Browser-Sitzung, was visuelle Transparenz und synchrone Interaktion über definierte Backend-Tools ermöglicht1.  
> 5. **Einschränkungen der zeilengenauen Code-Analyse**: Während die Dateipfade, Architekturschichten, Docker-Umgebungen, API-Endpoints und Tool-Klassen zweifelsfrei nachgewiesen werden können, sind spezifische Zeilennummern im bereitgestellten Text-Auszug nicht enthalten und werden hiermit explizit als nicht einsehbar gekennzeichnet.

#### **Referenzen**

> 1. open-webui/computer: Your Computer. Anywhere. \- GitHub, [https://github.com/open-webui/computer](https://github.com/open-webui/computer)  
> 2. Open WebUI Computer, [https://docs.openwebui.com/ecosystem/computer/](https://docs.openwebui.com/ecosystem/computer/)  
> 3. refac · open-webui/computer@4a9e389 \- GitHub, [https://github.com/open-webui/computer/actions/runs/29631593338](https://github.com/open-webui/computer/actions/runs/29631593338)  
> 4. feat: Support fully air-gapped installation and first run · open-webui computer · Discussion \#100 \- GitHub, [https://github.com/open-webui/computer/discussions/100](https://github.com/open-webui/computer/discussions/100)  
> 5. computer/CHANGELOG.md at main · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/CHANGELOG.md](https://github.com/open-webui/computer/blob/main/CHANGELOG.md)  
> 6. docs/docs/features/computer/index.md at main · open-webui/docs \- GitHub, [https://github.com/open-webui/docs/blob/main/docs/features/computer/index.md](https://github.com/open-webui/docs/blob/main/docs/features/computer/index.md)  
> 7. Releases · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/releases](https://github.com/open-webui/computer/releases)  
> 8. open-webui/open-webui: User-friendly AI Interface (Supports Ollama, OpenAI API ... \- GitHub, [https://github.com/open-webui/open-webui](https://github.com/open-webui/open-webui)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADwAAAAaCAYAAADrCT9ZAAACHUlEQVR4Xu2XzSu2QRTGj1BEWVggSqztlFKW7+K1seCPeDe2PrK1VrJRUrKQZP2WhcW7lH9AKQtSFhZSLCQfc5l7clzujzP3cxe97l+dxXOdmTMz95yZOY9ITc2P4ImFb06vs2kWrWw4a2UxYV+8X9tc4ht2tk2+gcRXRLezQ/nYd89Zm27kuEh8wRaV78HZmPpt4p+zIxZTeEmMGXV2K9kfrIgtyY4NEBe+dnYkwGfe6S7xHXrYkcKu+La/ldaUaI2AsfMWfONshkXFrGT3/QQW8chiBuHjYAIBnPvolErhWXxsTmeMOU8agz7mBaPhHxZz0Lt8Kn6Hq2BcfNwDpWGhGMPCmfijVQgGsV4yIOwyDBdIlei0RtbEvBpriRViTgVFmNgEOxoEmYa46842yVcE5nLOYhqxC8blcSe+3yX5GqVFPu5yDEjnexaZTokLHtJsSMpPrAjE/MuigT4xLBhYJ42zq88s3m30xeKr4pf4mChmYjHtMMAASKU8wsOvwaSgWQoWK9hZHsfKpEScYaRDFs3i2wyyQ97fzrynCaWjdRGId8WikQVnOyymgckssSjvZ1RbQFdG2jpUmwBqXfjySj+OA8P9EgM+VD+LaZxI+a8aQ0xxUwa9IbmEp2CEHRWCjMgq/KsA1d81i3ksS2SHSKzlYRnChsVUi2/oPwRVsiLVl6CaY2erLFrBOxZ7WXwlU5J+UdbU1PxnvAKfuoiy/xRkkgAAAABJRU5ErkJggg==>