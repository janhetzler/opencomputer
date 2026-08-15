## BUG-009: mcp_git -- Agenten uebergeben GitHub-URL statt lokalem Pfad

**Status:** Offen
**Repo:** janhetzler/la (agents/prompts)

**Symptom:** Code Agent ruft mcp_git mit `repo_path=/github.com/janhetzler/la`
auf statt `/home/varxdev/la`. mcp_git verweigert Zugriff:
"Repository path is outside the allowed repository /home/varxdev/la"

**Ursache:** Agenten-Prompt definiert nicht explizit welcher lokale
Repo-Pfad zu verwenden ist. Modell leitet GitHub-URL aus Kontext ab.

**Workaround:** Im Chat explizit angeben:
"git status von /home/varxdev/la"

**Fix:** prompts/agents/code.md und prompts/agents/researcher.md
erwaeitern um: "Lokaler Repo-Pfad ist immer /home/varxdev/la"
(Developer-Chat Aufgabe)

---

## BUG-008: mcp-server-fetch schlägt fehl -- Node.js zu alt

**Status:** Offen
**Umgebung:** HF Space Docker Container

**Symptom:** mcp-server-fetch wirft beim Fetch-Tool-Call:
`Command ExtractArticle.js returned non-zero exit status 1`
LiteLLM meldet daraufhin InternalServerError fuer agent-local.

**Ursache:** readabilipy (Abhaengigkeit von mcp-server-fetch) benoetigt
Node.js 18+ fuer ExtractArticle.js. Im Container laeuft Node v12.22.9
(Ubuntu 22.04 Default) -- zu alt.

**Auswirkung:** Researcher Agent kann keine Web-Inhalte fetchen.
Python-HTML-Fallback liefert schlechte Qualitaet bei JS-heavy Sites.

**Fix:** Node.js 20 ins Dockerfile:

```dockerfile
RUN curl -fsSL https://deb.nodesource.com/setup_20.x \
    | bash - && \
    apt-get install -y nodejs
```

---

## BUG-007: PIDs manuell gestarteter Prozesse schwer auffindbar

**Status:** Offen
**Umgebung:** HF Space Terminal

**Symptom:** Im cptr-Terminal gestartete Prozesse (llama-server, LiteLLM,
Agent Server etc.) sind spaeter schwer zu killen. `ps aux` zeigt viele
Prozesse aber ohne notierte PID ist der richtige schwer zu identifizieren.

**Ursache:** cptr verwendet `os.fork()` fuer Terminal-Sessions
(cptr/utils/terminal.py). Alle im Terminal gestarteten Prozesse sind
direkte Kind- bzw. Enkelprozesse von cptr -- die PPID-Kette macht
gezieltes `kill` ohne bekannte PID schwierig.

**Workaround:** PID nach jedem manuellen Start sofort notieren:

```bash
nohup python3 /tmp/start_hfspace.py > /tmp/logs/la_start.log 2>&1 &
echo $! > /tmp/la_stack.pid
cat /tmp/la_stack.pid
```

Oder PID-Datei pro Prozess ablegen und fuer kill verwenden:

```bash
kill $(cat /tmp/la_stack.pid)
```

**Fix:** PID-Dateien in start_hfspace.py automatisch schreiben.

---

---
type: Log
status: current
updated_at: 2026-07-31
environment: hfspace
---
# BUGS.md -- Fehlerprotokoll opencomputer / HF Space

Neuester Eintrag oben. Format analog zu janhetzler/la BUGS.md.

---

## BUG-001: inspect_phoenix_hfspace.py setzt laufenden Stack voraus

**Status:** Offen
**Umgebung:** HF Space Terminal

**Symptom:** inspect_phoenix_hfspace.py schlaegt fehl wenn Stack nicht
laeuft -- Pre-Flight-Check prueft alle Ports und bricht ab wenn
LiteLLM :4000 nicht antwortet.

**Ursache:** Stack wird von start_hfspace.py nach dem Testlauf gestoppt.
inspect muss waehrend des Testlaufs ausgefuehrt werden -- nicht danach.

**Workaround:** inspect ist inline in start_hfspace.py integriert --
wird automatisch vor dem Cleanup ausgefuehrt. Separates
inspect_phoenix_hfspace.py nur fuer manuelle Diagnose waehrend
der Stack manuell laeuft.

**Fix:** Kein dringender Fix noetig -- Workaround ist produktionstauglich.

---




## BUG-006: LiteLLM Timeout zu kurz fuer HF Space

**Status:** Offen
**Umgebung:** HF Space

**Symptom:** LiteLLM Readiness-Check in start_hfspace.py
laeuft nach 40 Sekunden ab -- LiteLLM braucht auf HF Space
laenger zum Starten.

**Fix:** Timeout in start_hfspace.py von 40 auf 90 Sekunden erhoehen.

**Zustaendig:** scripts/hfspace/start_hfspace.py in opencomputer Repo.

---

## BUG-003: prisma fehlt in requirements.txt (LA)

**Status:** Offen
**Umgebung:** HF Space (la_env)

**Symptom:** LiteLLM wirft ModuleNotFoundError: No module named 'prisma'
beim ersten Request — Internal server error die Folge.

**Workaround:** pip install prisma

**Fix:** prisma in janhetzler/la requirements.txt ergaenzen.
Zustaendig: Developer-Chat im LA Projekt.

**Entdeckt:** 2026-07-31 im HF Space Deployment.

---

## BUG-004: Phoenix stirbt nach Stack-Neustart

**Status:** Offen
**Umgebung:** HF Space

**Symptom:** Nach manuellem pkill + Neustart laeuft Phoenix nicht
mehr zuverlaessig. Traces koennen nicht exportiert werden
(Connection refused :6006).

**Ursache:** Phoenix wird nicht sauber neu gestartet wenn
vorherige Instanz noch Sockets haelt.

**Fix:** Readiness-Check in start_hfspace.py fuer Phoenix
verlaengern + Port-Check vor Start.

**Entdeckt:** 2026-07-31 im HF Space Deployment.

---

## BUG-002: async_timeout fehlt in requirements.txt (LA)

**Status:** Offen
**Umgebung:** HF Space (la_env)

**Symptom:** LiteLLM startet nicht -- ModuleNotFoundError: No module
named 'async_timeout'. Das Paket fehlt in janhetzler/la requirements.txt.

**Workaround:** Manuell installieren:
. /home/varxdev/la_env/bin/activate && pip install async_timeout

**Fix:** async_timeout in janhetzler/la requirements.txt ergaenzen.
Zustaendig: Developer-Chat im LA Projekt.

**Entdeckt:** 2026-07-31 im HF Space Deployment.

---
## Geschlossene Bugs

---

## BUG-000: Python 3.10 inkompatibel mit numpy 2.4.4

**Status:** Geschlossen (2026-07-31)
**Umgebung:** HF Space

**Symptom:** numpy==2.4.4 nicht installierbar unter Python 3.10 --
benoetigt Python 3.11+.

**Fix:** Python 3.11 im Dockerfile als Default gesetzt (Commit 1b6a57c).