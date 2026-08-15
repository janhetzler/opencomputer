"""
phoenix_inspect.py -- Phoenix Traces auslesen und anzeigen.

Liest Spans aus dem 'local-agent' Projekt in Phoenix.
Zeigt Status, Span-Kind, Fehler und LLM-Calls.

Verwendung:
    python3 scripts/hfspace/phoenix_inspect.py
    python3 scripts/hfspace/phoenix_inspect.py --limit 20
    python3 scripts/hfspace/phoenix_inspect.py --errors-only

Voraussetzung:
    Phoenix laeuft auf :6006
"""

import sys, json, urllib.request
from datetime import datetime

PHOENIX_BASE = "http://localhost:6006"

# Argumente
limit = 10
errors_only = False
for i, arg in enumerate(sys.argv[1:]):
    if arg == "--limit" and i+2 <= len(sys.argv)-1:
        limit = int(sys.argv[i+2])
    if arg == "--errors-only":
        errors_only = True

# 1. Projekte auflisten
print("=== Phoenix Projekte ===", flush=True)
resp = urllib.request.urlopen(f"{PHOENIX_BASE}/v1/projects")
projects = json.loads(resp.read())["data"]
for p in projects:
    print(f"  {p['name']} -- ID: {p['id']}")

# 2. local-agent Projekt finden
project_id = None
for p in projects:
    if p["name"] == "local-agent":
        project_id = p["id"]
        break

if not project_id:
    print("\nFAIL: Projekt 'local-agent' nicht gefunden")
    print("Wurde init_phoenix() aufgerufen?")
    sys.exit(1)

print(f"\n=== Spans (Projekt: local-agent, limit={limit}) ===")

# 3. Spans auslesen
resp = urllib.request.urlopen(
    f"{PHOENIX_BASE}/v1/projects/{project_id}/spans?limit={limit}"
)
data = json.loads(resp.read())
spans = data.get("data", [])
print(f"Gesamt: {len(spans)} Spans\n")

# 4. Anzeigen
ok_count = 0
error_count = 0

for s in spans:
    status = s.get("status_code", "?")
    name = s.get("name", "?")
    kind = s.get("span_kind", "?")

    if errors_only and status != "ERROR":
        continue

    if status == "OK":
        ok_count += 1
        icon = "✓"
    elif status == "ERROR":
        error_count += 1
        icon = "✗"
    else:
        icon = "?"

    print(f"{icon} [{kind:10}] {name[:40]:40} | {status}")

    # Fehler-Detail anzeigen
    if status == "ERROR":
        msg = s.get("status_message", "")
        if msg:
            print(f"    Fehler: {msg[:120]}")

    # LLM Token-Verbrauch anzeigen
    attrs = s.get("attributes", {})
    if kind == "LLM" and attrs:
        tokens_in  = attrs.get("llm.token_count.prompt", 0)
        tokens_out = attrs.get("llm.token_count.completion", 0)
        if tokens_in or tokens_out:
            print(f"    Tokens: {tokens_in} in / {tokens_out} out")

print(f"\nSummary: {ok_count} OK, {error_count} ERROR")
