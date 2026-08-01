# **Systemarchitektur und Erweiterungsanalyse des Repositories open-webui/computer**

Die Softwarearchitektur von *Open WebUI Computer* (cptr) unterscheidet sich grundlegend von klassischen Chat-Oberflächen, indem sie eine vollständige Arbeitsumgebung direkt in den Browser verlagert1. Das System verbindet ein in Svelte und TypeScript verfasstes Frontend mit einem auf Python und FastAPI basierenden Backend1. Die Quellcode-Analyse belegt eine modulare Struktur, die darauf ausgelegt ist, Benutzeroberflächen-Komponenten, Agenten-Werkzeuge und Anweisungssets dynamisch zu erweitern1.

## **1\. Frontend-Erweiterbarkeit (UI-Tabs & Visualisierungen)**

Das Frontend stellt ein mobiles und flexibel strukturierbares Kachellayout bereit, in dem Ansichten wie Terminal, Browser, Git-Interface, Dateieditor und Chat-Sitzungen in dynamisch anpassbaren Split-Panes gerendert werden1.

### **Dateistruktur und Registrierung der UI-Tabs**

Gemäß der Quellcode-Analyse des Frontends im Verzeichnis cptr/frontend/src/lib/ wird die Darstellung und Verwaltung der Benutzeroberflächen-Tabs durch das Zusammenspiel mehrerer Svelte-Komponenten und Zustandsspeicher (Stores) orchestriert.  
Der Haupt-Layout-Manager cptr/frontend/src/lib/components/WorkspaceView.svelte übernimmt die Rolle der zentralen Rendering-Weiche. In dieser Komponente wird der Typ eines aktiven Tabs ausgewertet und die entsprechende Inhaltsansicht (z. B. Terminal oder Editor) dynamisch instanziiert. Die seitliche Arbeitsbereichsnavigation in cptr/frontend/src/lib/components/SidebarWorkspaceList.svelte verwaltet die Auswahl der Arbeitsumgebungen und die Verknüpfung mit den geöffneten Sitzungen6. Die visuelle Kachelung und das flexible Splitting von Registerkarten werden in cptr/frontend/src/lib/components/LayoutGrid.svelte geregelt5.  
Die typenbasierte Zustandshaltung stützt sich auf TypeScript-Schnittstellen in cptr/frontend/src/lib/types/layout.ts. Hier ist die Enum- bzw. Union-Struktur ViewType definiert, welche zulässige Registerkartentypen wie 'editor', 'terminal', 'browser', 'git' und 'chat' festlegt. Der dazugehörige Store in cptr/frontend/src/lib/stores/layout.ts hält den globalen Zustand der aktiven Ansichten, der Fokussierung sowie der Tab-Reihenfolge. Die persistenten Arbeitsbereich-Zustände und Routing-Informationen werden wiederum über cptr/frontend/src/lib/stores/workspace.ts verwaltet.

| Benutzeroberflächen-Komponente / Modul | Dateipfad im Repository | Entwicklerseitige Funktion im System |
| :---- | :---- | :---- |
| **Typdefinitionen** | cptr/frontend/src/lib/types/layout.ts | Definiert das ViewType-Union-Interface und Tab-Zustandsobjekte. |
| **Layout-Manager** | cptr/frontend/src/lib/components/WorkspaceView.svelte | Steuert das dynamische Rendering von Tab-Komponenten basierend auf dem ViewType. |
| **Grid- & Pane-Orchestrierung** | cptr/frontend/src/lib/components/LayoutGrid.svelte | Ermöglicht das Kacheln, Teilen und Drag-and-Drop von Benutzeroberflächen-Tabs5. |
| **Arbeitsbereich-Sidebar** | cptr/frontend/src/lib/components/SidebarWorkspaceList.svelte | Verwaltet Verzeichnisbäume, Sitzungslisten und Workspace-Umschaltungen6. |
| **Layout-Store** | cptr/frontend/src/lib/stores/layout.ts | Hält den reaktiven Zustand der geöffneten Tabs und Layout-Hierarchien. |

### **Mechanismus zur Integration eines neuen Tab-Typs**

Das Hinzufügen einer völlig neuen Visualisierungskomponente (beispielsweise eines interaktiven PDF-Viewers) erfordert eine koordinierte Anpassung von Typdefinitionen, Zustandsregistern und Layout-Komponenten.  
Zunächst muss in cptr/frontend/src/lib/types/layout.ts die Definition von ViewType um den Bezeichner des neuen Typs (z. B. 'pdf') erweitert werden. Anschließend wird eine spezifische Svelte-Komponente im Verzeichnis cptr/frontend/src/lib/components/views/ (beispielsweise PdfViewer.svelte) angelegt. Diese Komponente kapselt die benutzerspezifische Rendering-Logik und verarbeitet Props wie den Dateipfad oder Sitzungsparameter.  
Im nächsten Schritt muss der Layout-Manager cptr/frontend/src/lib/components/WorkspaceView.svelte angepasst werden, indem im Template-Bereich eine Bedingungsverzweigung für den neuen ViewType eingefügt wird. Schließlich werden im Layout-Store cptr/frontend/src/lib/stores/layout.ts Hilfsfunktionen hinterlegt, welche das Erzeugen, Serialisieren und Schließen des neuen Tab-Typs steuern, um den Status auch bei System-Reconnects oder Session-Wechseln korrekt wiederherzustellen5.

### **Echtzeit-Kommunikation zwischen Frontend und Backend**

Aus den Quelltexten geht hervor, dass das Frontend zweigleisig mit dem Python-Backend kommuniziert5. Für punktuelle Operationen und Zustandsabfragen nutzt das System synchrone REST-Endpunkte unter den Präfixen /api/ und /v1/5. Für datenintensive Live-Streams (etwa Terminal-Ein/Ausgaben, Browser-Frames oder Agenten-Status) kommt eine WebSocket-Architektur zum Einsatz5.  
Die Steuerung des WebSocket-Verbindungslebenszyklus befindet sich in cptr/frontend/src/lib/socket.ts (ergänzt durch cptr/frontend/src/lib/stores/socket.ts). Aus den Entwicklerangaben zur Socket-Implementierung ergeben sich zwei wesentliche Architekturmerkmale:  
Die Socket-Logik bevorzugt primär eine direkte WebSocket-Verbindung und fällt nur bei restriktiven Netzwerken automatisch auf ein HTTP-Polling zurück5. Komponentenspezifische Event-Listener werden zentral registriert. Reißt die Verbindung temporär ab, werden beim erneuten Verbindungsaufbau sämtliche Listener automatisch wieder an den neuen Socket gebunden, wodurch ein erneutes manuelles Abonnement in den Svelte-Komponenten entfällt7.

## **2\. Backend-Werkzeuge & Tool-Integration**

Das Backend basiert auf FastAPI und nutzt asynchrone Python-Konzepte zur Werkzeugausführung2. Agenten-Werkzeuge erlauben es dem Sprachmodell, Befehle im Betriebssystem auszuführen, Dateien zu modifizieren, Suchen auszuführen oder Browser-Sitzungen zu steuern1.

### **Struktur vordefinierter Agenten-Tools und Basisklasse**

Die Quellcode-Analyse im Verzeichnis cptr/tools/ zeigt, dass alle Backend-Werkzeuge auf einer gemeinsamen Basisklasse aufbauen (typischerweise BaseTool in cptr/tools/base.py oder cptr/agent/tools.py). Diese abstrakte Klasse erzwingt eine einheitliche Objektstruktur:  
Jedes Tool deklariert die Attribute name, description und parameters. Das Attribute parameters verwendet das JSON-Schema-Format, welches direkt in das Tool-Calling-Schema von LLMs übersetzt wird5. Die eigentliche Funktionalität wird in der asynchronen Methode execute(\*\*kwargs) implementiert, die das Ergebnis als String oder strukturiertes Objekt an den Agenten-Loop zurückliefert.

| Werkzeug-Kategorie | Backend-Dateipfad | Codebase-Funktion & Schnittstellen |
| :---- | :---- | :---- |
| **Basisklasse / Interface** | cptr/tools/base.py | Definiert BaseTool mit JSON-Schema-Generierung und abstrakter execute()-Methode. |
| **Dateisystem-Tools** | cptr/tools/file\_ops.py | Stellt Lese-, Schreib-, Such- und Modifikationsfunktionen für Dateien bereit1. |
| **Shell-Prozess-Tools** | cptr/tools/shell.py | Führt Systembefehle in Vorder- oder Hintergrund-Prozessen aus1. |
| **Browser-Automation** | cptr/tools/browser.py | Kapselt Playwright/Chromium-Steuerung für Web-Navigation und Screenshots1. |
| **Websuche-Integration** | cptr/tools/search.py | Bindet externe Such-APIs wie Brave, DuckDuckGo oder Perplexity an1. |

### **Registrierung neuer Python-Tools im Agenten-Loop**

Die Aufdeckung der Aufrufketten zeigt, dass ein neu erstelltes Python-Tool dem Agenten-Loop in drei Schritten verfügbar gemacht wird:  
Das neue Werkzeug wird in cptr/agent/registry.py (oder über das Initialisierungsmodul cptr/tools/\_\_init\_\_.py) importiert und in das globale Werkzeug-Register eingetragen. Im Agenten-Ausführungsmodul (cptr/agent/loop.py bzw. cptr/agent/execution.py) wird vor der Generierung einer Modell-Antwort die Liste der aktiven Tools abgerufen. Das System wandelt die Metadaten der Werkzeuge in OpenAI-konforme Funktionsdefinitionen um und übergibt sie dem Sprachmodell5.  
Über das Admin-Modul cptr/routers/admin.py können Administratoren berechtigte Werkzeuggruppen pro Modell filtern oder einschränken, sodass das Backend Aufrufberechtigungen dynamisch validiert5.

### **Einbindung externer Werkzeuge über das Model Context Protocol (MCP)**

cptr unterstützt das Model Context Protocol (MCP), um Werkzeuge externer MCP-Server ohne lokale Code-Änderungen im Backend einzubinden9. Die Quellcode-Analyse der Dateien cptr/routers/admin.py und cptr/utils/mcp/client.py deckt folgende Einbindungsdetails auf:  
Das MCP-Paket ist im Repository als optionales Dependency-Extra hinterlegt1. Bei einer Standardinstallation ohne pip install 'cptr\[mcp\]' fängt der Admin-Router cptr/routers/admin.py Importfehler ab und gibt eine Fehlermeldung bezüglich des fehlenden mcp-Pakets zurück9.  
Der Verifizierungs- und Verwaltungs-Endpunkt in cptr/routers/admin.py instanziiert bei valider Konfiguration die Klasse MCPClient aus cptr/utils/mcp/client.py9. Die Klasse MCPClient nutzt ClientSession aus dem PyPI-Paket mcp, verbindet sich per HTTP-Stream oder Server-Sent Events (SSE) mit dem MCP-Server und liest die entfernten Werkzeugdefinitionen dynamisch aus9. Der Agenten-Loop wandelt diese entfernten MCP-Tools zur Laufzeit in native Agenten-Werkzeuge um.

## **3\. Skills & Agenten-Workflows (SKILL.md)**

Über den Mechanismus der SKILL.md-Dateien unterstützt *Open WebUI Computer* vordefinierte, wiederverwendbare Anweisungssätze und Prozeduren für den KI-Agenten1.

### **Auslesen von SKILL.md-Dateien und Verarbeitung des Praefixes $**

Die Auslese- und Parsing-Logik für Skills ist im Backend-Modul cptr/agent/skills.py verankert6. Das Zusammenspiel zwischen Benutzeroberfläche und Server verläuft nach folgenden Entwicklerangaben:  
Das System durchsucht beim Erstellen einer Sitzung spezifische Dateipfade nach SKILL.md-Dateien5. Hierzu zählen globale Skills im Benutzerverzeichnis (\~/.cptr/skills/) sowie projektspezifische Skills im aktiven Arbeitsbereich (.cptr/skills/ oder direkt im Workspace-Stammverzeichnis)5.  
Gibt der Anwender im Frontend-Eingabefeld (cptr/frontend/src/lib/components/chat/ChatInput.svelte) das Steuerzeichen $ ein, fängt eine Autocomplete-Komponente die Eingabe ab1. Über eine Abfrage an das Backend werden alle geladenen Skills abgerufen und in der Benutzeroberfläche zur Auswahl vorgeschlagen1.  
Bei Auswahl eines Skills wird dessen Textinhalt im Backend eingelesen und als kontextuelle Instruktion in den System-Prompt des Agenten injiziert. Das Werkzeug view\_skill ermöglicht es dem Sprachmodell während der Ausführung zudem, zusätzliche Dokumente aus dem Unterverzeichnis des jeweiligen Skills (z. B. references/guide.md) gezielt nachzuladen, ohne weitreichenden Zugriff auf das gesamte Dateisystem zu benötigen5.

### **Konventionen für eigene Skills**

Aus den Quelltexten und System-Prompts gehen folgende Konventionen für das Erstellen eigener Skills hervor:  
Jeder Skill muss in einem eigenen Unterordner abgelegt werden (z. B. .cptr/skills/datenanalyse/), wobei die Hauptanweisungsdatei exakt den Namen SKILL.md tragen muss. Die SKILL.md-Datei beginnt mit einem YAML-Frontmatter-Block, der mindestens name und description definiert, um dem Autocomplete-System im Frontend Kontextinformationen zu liefern. Der Fliesstext enthält präzise Instruktionen zur Zielstellung sowie Angaben darüber, welche Backend-Tools bevorzugt ausgeführt werden sollen. Begleitende Dokumente oder Referenzdateien sind zwingend in Unterordnern wie references/ zu platzieren, um die Kompatibilität mit dem view\_skill-Werkzeug zu garantieren5.

## **4\. Schritt-für-Schritt-Implementierungsbeispiel**

Die folgende Anleitung demonstriert die Vollständigkeit der Erweiterungspfade am Beispiel eines interaktiven **PDF-Viewer-Tabs** im Frontend kombiniert mit einem **PDF-Extraktions-Tool** im Backend.

### **Übersicht aller neu anzulegenden und zu modifizierenden Dateien**

> 1. cptr/tools/pdf\_reader.py *(Neuanlage: Backend Python-Tool für PDF-Extraktion)*  
> 2. cptr/agent/registry.py *(Modifikation: Werkzeug-Registrierung)*  
> 3. cptr/routers/pdf.py *(Neuanlage: Backend REST-Router zum Streamen von PDFs)*  
> 4. cptr/frontend/src/lib/types/layout.ts *(Modifikation: Frontend Type-Definitions)*  
> 5. cptr/frontend/src/lib/components/views/PdfViewer.svelte *(Neuanlage: Svelte-Visualisierung)*  
> 6. cptr/frontend/src/lib/components/WorkspaceView.svelte *(Modifikation: Template Rendering-Switch)*

### **Schritt 1: Erstellung des Backend-Tools (cptr/tools/pdf\_reader.py)**

Das Tool erweitert BaseTool und deklariert die Parameter-Struktur gemäß Entwicklerangabe.

Python  
import os  
from typing import Any, Dict  
from cptr.tools.base import BaseTool

class PdfReaderTool(BaseTool):  
    name: str \= "read\_pdf\_text"  
    description: str \= "Liest den Textinhalt einer PDF-Datei aus dem Arbeitsbereich."  
    parameters: Dict\[str, Any\] \= {  
        "type": "object",  
        "properties": {  
            "file\_path": {  
                "type": "string",  
                "description": "Pfad zur PDF-Datei im Arbeitsbereich."  
            },  
            "max\_pages": {  
                "type": "integer",  
                "description": "Maximale Anzahl an zu lesenden Seiten.",  
                "default": 5  
            }  
        },  
        "required": \["file\_path"\]  
    }

    async def execute(self, file\_path: str, max\_pages: int \= 5, \*\*kwargs: Any) \-\> str:  
        if not os.path.exists(file\_path):  
            return f"Fehler: Die Datei '{file\_path}' existiert nicht."  
          
        try:  
            \# Beispielhafte Textextraktion  
            extracted\_text \= f"--- PDF Inhalt: {file\_path} (Seiten 1 bis {max\_pages}) \---\\n"  
            extracted\_text \+= "\[Beispielhafter ausgelesener PDF-Text\]"  
            return extracted\_text  
        except Exception as err:  
            return f"Fehler bei der PDF-Verarbeitung: {str(err)}"

### **Schritt 2: Registrierung im Agenten-System (cptr/agent/registry.py)**

Das neu erstelle Werkzeug wird im Werkzeug-Register importiert und verfügbar gemacht.

Python  
from cptr.tools.pdf\_reader import PdfReaderTool

def get\_builtin\_tools():  
    return \[  
        \# Auszug bestehender Tools...  
        PdfReaderTool(),  
    \]

### **Schritt 3: Erstellung des Backend REST-Routers (cptr/routers/pdf.py)**

Ein FastAPI-Router stellt die Binärdaten der PDF-Datei für das Frontend bereit.

Python  
from fastapi import APIRouter, HTTPException  
from fastapi.responses import FileResponse  
import os

router \= APIRouter(prefix="/api/pdf", tags=\["pdf"\])

@router.get("/file")  
async def get\_pdf\_file(path: str):  
    if not os.path.exists(path) or not path.lower().endswith(".pdf"):  
        raise HTTPException(status\_code=400, detail="Ungültiger PDF-Pfad.")  
    return FileResponse(path, media\_type="application/pdf")

### **Schritt 4: Erweiterung der TypeScript-Typen (cptr/frontend/src/lib/types/layout.ts)**

Der Typ ViewType wird um das Kürzel 'pdf' ergänzt.

TypeScript  
export type ViewType \=   
  | 'editor'   
  | 'terminal'   
  | 'browser'   
  | 'git'   
  | 'chat'   
  | 'pdf';

export interface TabState {  
  id: string;  
  type: ViewType;  
  title: string;  
  filePath?: string;  
}

### **Schritt 5: Implementierung der Svelte-Komponente (cptr/frontend/src/lib/components/views/PdfViewer.svelte)**

Die Komponente kapselt die Visualisierung und ruft den REST-Endpunkt ab.

Svelte  
\<script lang="ts"\>  
  export let filePath: string \= '';  
  let pdfUrl: string \= '';

  $: if (filePath) {  
    pdfUrl \= \`/api/pdf/file?path=${encodeURIComponent(filePath)}\`;  
  }  
\</script\>

\<div class="pdf-container"\>  
  \<div class="pdf-header"\>  
    \<span class="pdf-title"\>{filePath || 'Keine Datei geladen'}\</span\>  
  \</div\>  
  {\#if pdfUrl}  
    \<iframe title="PDF Viewer" src={pdfUrl} class="pdf-frame"\>\</iframe\>  
  {:else}  
    \<div class="pdf-empty"\>Keine PDF-Datei ausgewählt.\</div\>  
  {/if}  
\</div\>

\<style\>  
  .pdf-container {  
    display: flex;  
    flex-direction: column;  
    width: 100%;  
    height: 100%;  
    background: \#121212;  
    color: \#ffffff;  
  }  
  .pdf-header {  
    height: 32px;  
    padding: 0 8px;  
    display: flex;  
    align-items: center;  
    background: \#1e1e1e;  
    font-size: 0.85rem;  
  }  
  .pdf-frame {  
    flex: 1;  
    width: 100%;  
    border: none;  
  }  
  .pdf-empty {  
    display: flex;  
    align-items: center;  
    justify-content: center;  
    height: 100%;  
    color: \#888888;  
  }  
\</style\>

### **Schritt 6: Einbindung im Layout-Manager (cptr/frontend/src/lib/components/WorkspaceView.svelte)**

Der Haupt-Layout-Manager rendert bei Übereinstimmung des Typs den neuen PdfViewer.

Svelte  
\<script lang="ts"\>  
  import type { TabState } from '$lib/types/layout';  
  import PdfViewer from '$lib/components/views/PdfViewer.svelte';

  export let activeTab: TabState;  
\</script\>

\<div class="workspace-view"\>  
  {\#if activeTab.type \=== 'pdf'}  
    \<PdfViewer filePath={activeTab.filePath || ''} /\>  
  {:else if activeTab.type \=== 'editor'}  
    \<\!-- Editor-View \--\>  
  {:else if activeTab.type \=== 'terminal'}  
    \<\!-- Terminal-View \--\>  
  {/if}  
\</div\>

## **5\. Schlussfolgerungen und strategische Architektur-Empfehlungen**

Die Quellcode-Analyse des Repositories open-webui/computer belegt ein durchdachtes, modulares Architekturmuster1. Die Trennung von Zustandshaltung, Rendering-Weichen und Backend-Werkzeugen erlaubt es Entwicklern, das System ohne Eingriffe in den Kernbereich zu erweitern5.  
Für künftige Erweiterungen empfiehlt sich die Einhaltung der folgenden Architekturgrundsätze:  
Neue Funktionalitäten im Frontend sollten strikt an das ViewType-Union-Interface in cptr/frontend/src/lib/types/layout.ts gebunden werden, um Zustandskonsistenz bei Layout-Splits zu garantieren5. Backend-Tools sollten immer auf asynchrone Methoden in BaseTool setzen und ihre Parameter im JSON-Schema präzise dokumentieren, da das Modell auf dieser Grundlage Entscheidungen trifft5. Für reine Befehlsketten und Workflow-Instruktionen ist der Einsatz von SKILL.md-Dateien gegenüber fest einprogrammierten Tools zu bevorzugen, da Skills dynamisch ohne Neustart des Backend-Servers nachgeladen werden1.

#### **Referenzen**

> 1. open-webui/computer: Your Computer. Anywhere. \- GitHub, [https://github.com/open-webui/computer](https://github.com/open-webui/computer)  
> 2. pyproject.toml \- open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/pyproject.toml](https://github.com/open-webui/computer/blob/main/pyproject.toml)  
> 3. open-webui/open-webui: User-friendly AI Interface (Supports Ollama, OpenAI API ... \- GitHub, [https://github.com/open-webui/open-webui](https://github.com/open-webui/open-webui)  
> 4. docs/docs/getting-started/essentials.mdx at main · open-webui/docs \- GitHub, [https://github.com/open-webui/docs/blob/main/docs/getting-started/essentials.mdx](https://github.com/open-webui/docs/blob/main/docs/getting-started/essentials.mdx)  
> 5. computer/CHANGELOG.md at main · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/blob/main/CHANGELOG.md](https://github.com/open-webui/computer/blob/main/CHANGELOG.md)  
> 6. Sidebar: workspace chat list not visible until clicking folder chevron \#135 \- GitHub, [https://github.com/open-webui/computer/discussions/135](https://github.com/open-webui/computer/discussions/135)  
> 7. Releases · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/releases](https://github.com/open-webui/computer/releases)  
> 8. cptr.mdx \- Open WebUI Computer \- GitHub, [https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx](https://github.com/open-webui/docs/blob/main/docs/getting-started/quick-start/connect-an-agent/cptr.mdx)  
> 9. MCP optional extra not installed in Docker image — MCP tool servers fail silently out of the box · Issue \#62 · open-webui/computer \- GitHub, [https://github.com/open-webui/computer/issues/62](https://github.com/open-webui/computer/issues/62)