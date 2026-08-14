---
title: "cptr Admin Config API: Konfigurierbare Settings"
type: Reference
status: current
updated_at: 2026-08-14
stale_after: 2027-08-14
tags: [cptr, admin, config, api, rest]
---

# cptr Admin Config API: Konfigurierbare Settings

Alle Settings werden über `PUT /api/admin/config` gesetzt und über
`GET /api/admin/config` ausgelesen. Werte sind JSON. Keys verwenden
Dot-Notation.

Verwandte Dokumentation: [HFSPACE.md](../HFSPACE.md)

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

## Alle konfigurierbaren Keys

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

## Hinweis

Theme- und UI-Einstellungen (Farben, Schrift) sind nicht über die
Config-API konfigurierbar — diese sind clientseitig im CSS/Svelte
Frontend hardcoded.
