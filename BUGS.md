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
