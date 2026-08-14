---
title: "cptr Admin Config API: Konfigurierbare Settings"
type: Reference
status: current
updated_at: 2026-08-14
stale_after: 2027-08-14
tags: [cptr, admin, config, api, rest, sqlite]
---

# cptr Admin Config API: Konfigurierbare Settings

Alle Settings werden über `PUT /api/admin/config` gesetzt und über
`GET /api/admin/config` ausgelesen. Werte sind JSON. Keys verwenden
Dot-Notation.

Verwandte Dokumentation: [HFSPACE.md](../HFSPACE.md) · [OPERATIONS_HFSPACE.md](OPERATIONS_HFSPACE.md)

---

## Zugriff via Python

```python
import urllib.request, json, http.cookiejar

BASE = "http://localhost:7860"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
opener.open(urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"username":"user","password":"12345678"}).encode(),
    headers={"Content-Type":"application/json"}
))

# Alle gesetzten Settings lesen
resp = opener.open(urllib.request.Request(f"{BASE}/api/admin/config"))
print(json.dumps(json.loads(resp.read()), indent=2))

# Setting setzen
def set_config(updates: dict):
    req = urllib.request.Request(
        f"{BASE}/api/admin/config",
        data=json.dumps({"config": updates}).encode(),
        headers={"Content-Type":"application/json"},
        method="PUT"
    )
    resp = opener.open(req)
    return json.loads(resp.read())
```

---

## Alle konfigurierbaren Keys (Config-API)

### agents
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `agents.profiles` | list | Konfigurierte Agent-Profile |

### audio
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `audio.recording_quality` | string | Aufnahmequalität |
| `audio.stt_api_key` | string | STT API Key |
| `audio.stt_base_url` | string | STT Base URL |
| `audio.stt_model` | string | STT Modell |
| `audio.transcribe_enabled` | bool | Transkription aktiv |
| `audio.tts_api_key` | string | TTS API Key |
| `audio.tts_auto_stream_enabled` | bool | TTS Auto-Stream |
| `audio.tts_base_url` | string | TTS Base URL |
| `audio.tts_enabled` | bool | TTS aktiv |
| `audio.tts_format` | string | TTS Format |
| `audio.tts_model` | string | TTS Modell |
| `audio.tts_playback_speed` | number | Wiedergabegeschwindigkeit |
| `audio.tts_voice` | string | TTS Stimme |
| `audio.voice_memos_enabled` | bool | Voice Memos aktiv |
| `audio.voice_mode_stt_mode` | string | STT Modus im Voice Mode |
| `audio.voice_mode_system_prompt` | string | System Prompt im Voice Mode |

### auth
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `auth.signup_enabled` | bool | Registrierung erlaubt |

### browser
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `browser.auto_launch` | bool | Browser automatisch starten |
| `browser.browser_use_api_key` | string | Browser Use API Key |
| `browser.browser_use_base_url` | string | Browser Use Base URL |
| `browser.cdp_url` | string | Chrome DevTools Protocol URL |
| `browser.enabled` | bool | Browser aktiv |
| `browser.encoder.hardware_acceleration` | bool | Hardware-Beschleunigung |
| `browser.firecrawl_api_key` | string | Firecrawl API Key |
| `browser.firecrawl_base_url` | string | Firecrawl Base URL |
| `browser.personal_keep_alive` | bool | Session am Leben halten |
| `browser.provider` | string | Browser Provider |
| `browser.quality.default` | string | Standard-Qualitätsprofil |
| `browser.quality.max_bitrate` | number | Max. Bitrate |
| `browser.quality.max_resolution` | string | Max. Auflösung |
| `browser.quality.profiles` | list | Qualitätsprofile |
| `browser.session_timeout_minutes` | number | Session Timeout (Min.) |
| `browser.tab_chrome_source` | string | Chrome Source |
| `browser.tab_default_mode` | string | Standard Tab-Modus |

### chat
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `chat.compact_token_threshold` | number | Token-Schwelle für Komprimierung |
| `chat.connections` | list | AI-Verbindungen (llama, OpenAI, Anthropic) |
| `chat.default_model` | string | Standard-Modell für neue Chats |
| `chat.models` | dict | Modell-Konfiguration (aktiv/inaktiv, params) |

### gateway
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `gateway.model` | string | Modell für Gateway-Anfragen |

### images
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `images.edit_api_key` | string | Bildbearbeitung API Key |
| `images.edit_base_url` | string | Bildbearbeitung Base URL |
| `images.edit_enabled` | bool | Bildbearbeitung aktiv |
| `images.edit_model` | string | Bildbearbeitung Modell |
| `images.edit_size` | string | Bildgröße (Bearbeitung) |
| `images.generation_api_key` | string | Bildgenerierung API Key |
| `images.generation_base_url` | string | Bildgenerierung Base URL |
| `images.generation_enabled` | bool | Bildgenerierung aktiv |
| `images.generation_model` | string | Bildgenerierung Modell |
| `images.generation_size` | string | Bildgröße (Generierung) |

### memory
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `memory.enabled` | bool | AI Memory aktiv |

### skills
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `skills.enabled` | bool | Skills aktiv |
| `skills.tool_enabled` | bool | Skills als Tool aktiv |

### subagents
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `subagents.background_enabled` | bool | Hintergrund-Subagenten aktiv |
| `subagents.enabled` | bool | Subagenten aktiv |
| `subagents.max_async` | number | Max. async Subagenten |
| `subagents.max_concurrent` | number | Max. gleichzeitige Subagenten |
| `subagents.max_iterations` | number | Max. Iterationen |
| `subagents.max_output` | number | Max. Output-Länge |
| `subagents.system_prompt` | string | System Prompt für Subagenten |

### web
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `web.brave_api_key` | string | Brave Search API Key |
| `web.chat_completions_api_key` | string | Chat Completions API Key |
| `web.chat_completions_base_url` | string | Chat Completions Base URL |
| `web.chat_completions_model` | string | Chat Completions Modell |
| `web.enabled` | bool | Web-Suche aktiv |
| `web.exa_api_key` | string | Exa API Key |
| `web.firecrawl_api_key` | string | Firecrawl API Key |
| `web.firecrawl_base_url` | string | Firecrawl Base URL |
| `web.perplexity_api_key` | string | Perplexity API Key |
| `web.perplexity_base_url` | string | Perplexity Base URL |
| `web.search_provider` | string | Such-Provider |
| `web.searxng_base_url` | string | SearXNG Base URL |
| `web.tavily_api_key` | string | Tavily API Key |

### workspace
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `workspace.auto_gitignore_dot_cptr` | bool | .cptr automatisch in .gitignore |

### xai
| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `xai.api_key` | string | xAI (Grok) API Key |

---

## Logging -- Umgebungsvariablen (nicht Config-API)

Logging wird ausschliesslich über Umgebungsvariablen konfiguriert,
nicht über die Admin-Config-API. Diese müssen vor dem cptr-Start
gesetzt werden (z.B. in start.sh).

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `CPTR_LOG_LEVEL` | `INFO` | Log-Level: DEBUG, INFO, WARNING, ERROR |
| `CPTR_LOG_FORMAT` | `text` | Format: `text` oder `json` |
| `CPTR_AUDIT_LOG_LEVEL` | `NONE` | Audit-Level: `NONE`, `METADATA`, `REQUEST`, `REQUEST_RESPONSE` |
| `CPTR_AUDIT_LOG_PATH` | `~/.cptr/logs/audit.jsonl` | Pfad zur Audit-Log-Datei |
| `CPTR_AUDIT_LOG_ROTATION` | `10 MB` | Rotation bei Dateigrösse |
| `CPTR_AUDIT_MAX_BODY_SIZE` | `2048` | Max. Body-Grösse im Log (Bytes) |
| `CPTR_AUDIT_EXCLUDED_PATHS` | `/api/chats,/v1/chat` | Pfade die nicht geloggt werden |
| `CPTR_LOG_UPSTREAM_REQUESTS` | `false` | Upstream-Requests (an Modell) loggen |
| `CPTR_UPSTREAM_REQUEST_LOG_PATH` | `~/.cptr/logs/upstream-requests.jsonl` | Pfad dazu |
| `CPTR_UPSTREAM_REQUEST_LOG_ROTATION` | `50 MB` | Rotation dazu |

### Audit-Logging aktivieren (in start.sh)

```sh
CPTR_AUDIT_LOG_LEVEL=METADATA cptr run --host 0.0.0.0 --port 7860
```

Audit-Level Bedeutung:
- `NONE` -- kein Logging (Default)
- `METADATA` -- Method, Path, Status, User, IP
- `REQUEST` -- + Request Body (sensitive Felder werden redaktiert)
- `REQUEST_RESPONSE` -- + Response Body

---

## SQLite Datenbank -- Schema

Pfad: `/home/varxdev/.cptr/app.db` (WAL-Modus)
Zusatzdateien: `app.db-shm`, `app.db-wal` (WAL-Dateien, immer zusammen lesen)

### Tabellen

| Tabelle | Inhalt |
|---------|--------|
| `users` | User-Profil: id, display_name, profile_image_url, role, settings, created_at, updated_at, last_seen_at |
| `auths` | Login-Daten: user_id, username, password (bcrypt) |
| `user_states` | UI-Zustand pro User: theme, keybindings, workspaceOrder, toolApprovalMode, locale, homeState |
| `config` | App-Config: key, value (JSON), updated_at |
| `files` | Hochgeladene Dateien: id, user_id, filename, path, hash, meta, data, created_at, updated_at |
| `chats` | Chat-Metadaten: id, user_id, title, summary, current_message_id, meta, created_at, updated_at, last_read_at |
| `chat_messages` | Nachrichten: id, chat_id, parent_id, role, content, model, done, output, usage, meta, created_at, chat_summary |
| `workspaces` | Workspace-Zustand: id, user_id, path, name, data, created_at, updated_at |
| `automations` | Scheduled Tasks: id, user_id, name, prompt, model_id, workspace, rrule, is_active, last_run_at, next_run_at, meta, created_at, updated_at |
| `automation_runs` | Task-Läufe: id, automation_id, chat_id, status, error, created_at |

### user_states -- UI-Settings (nicht über Config-API)

Theme, Keybindings und UI-Zustand liegen in `user_states.data` (JSON).
Diese sind **nicht** über die Admin-Config-API erreichbar, sondern nur
direkt in der DB oder über die cptr-UI.

Bekannte Felder in `data`:
- `theme` -- `light` oder `dark`
- `appearance.theme`, `appearance.themeConfig`, `appearance.textScale`, `appearance.borderContrast`
- `locale` -- z.B. `de-DE`
- `toolApprovalMode` -- `auto`, `ask`, `full`
- `sidebarOpen`, `sidebarWidth`
- `widescreenMode`, `expandToolDetails`
- `workspaceOrder` -- Liste der Workspace-Pfade
- `keybindings` -- alle Tastenkürzel
- `version` -- cptr-Version beim letzten Login

DB-Abfrage (read-only, WAL-sicher):

```python
import sqlite3, json
conn = sqlite3.connect("/home/varxdev/.cptr/app.db")
conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
rows = conn.execute("SELECT user_id, data FROM user_states").fetchall()
for user_id, data in rows:
    print(user_id, json.loads(data) if isinstance(data, str) else data)
conn.close()
```

---

## Hinweis

Theme- und UI-Einstellungen (Farben, Schrift) sind nicht über die
Config-API konfigurierbar -- diese liegen in `user_states` in der
SQLite-Datenbank und werden über die cptr-UI gesetzt.

Skript zum vollständigen DB-Export: [scripts/hfspace/cptr_db_export.py](../scripts/hfspace/cptr_db_export.py)
---

## Laufzeit & Ressourcen

### Installation

| Was | Wo | Wie |
|-----|----|-----|
| cptr Binary + Pakete | systemweit (Python) | `pip install cptr[all]` |
| cptr Daten (DB, Config, Logs) | `/home/varxdev/.cptr/` | automatisch beim ersten Start |
| cptr Start | `/home/varxdev/start.sh` | via tini als PID 1 |

### RAM-Verbrauch (gemessen, HF Space)

| Prozess | RSS |
|---------|-----|
| cptr (:7860, Python) | ~98 MB |

### Prozess-Hierarchie

cptr laeuft als direkter Kind-Prozess von tini (PID 1).
Alle Terminal-Sessions sind Kindprozesse von cptr (`os.fork()`).
Alle im Terminal gestarteten Prozesse sind damit Enkelprozesse von cptr.
Siehe BUG-007 fuer Konsequenzen beim Killen von Prozessen.

### Datei-Locations

| Datei | Pfad |
|-------|------|
| SQLite DB | `/home/varxdev/.cptr/app.db` |
| WAL Dateien | `/home/varxdev/.cptr/app.db-shm`, `app.db-wal` |
| Config Mirror | `/home/varxdev/.cptr/config.toml` |
| Audit Log (wenn aktiv) | `/home/varxdev/.cptr/logs/audit.jsonl` |
| Upstream Log (wenn aktiv) | `/home/varxdev/.cptr/logs/upstream-requests.jsonl` |

