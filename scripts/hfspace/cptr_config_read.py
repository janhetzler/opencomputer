"""
cptr_config_read.py -- cptr Konfiguration auslesen.

Liest alle gesetzten Config-Keys, Connections und
Tool-Server aus der cptr Admin API.

Verwendung:
    python3 scripts/hfspace/cptr_config_read.py

Voraussetzung:
    cptr laeuft auf :7860
"""

import urllib.request, json, http.cookiejar

BASE = "http://localhost:7860"

# Login
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj))
opener.open(urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({
        "username": "user",
        "password": "12345678"
    }).encode(),
    headers={"Content-Type": "application/json"}
))
print("Login OK", flush=True)

# Config
print("\n=== App Config ===", flush=True)
resp = opener.open(urllib.request.Request(
    f"{BASE}/api/admin/config"))
config = json.loads(resp.read())
print(json.dumps(config, indent=2))

# Connections
print("\n=== Connections ===", flush=True)
resp2 = opener.open(urllib.request.Request(
    f"{BASE}/api/admin/connections"))
conns = json.loads(resp2.read())
for c in conns["connections"]:
    print(f"  {c['name']}")
    print(f"    base_url:      {c['base_url']}")
    print(f"    provider:      {c['provider']}")
    print(f"    provider_type: {c['provider_type']}")
    print(f"    enabled:       {c['enabled']}")

# Tool Server
print("\n=== Tool Server ===", flush=True)
resp3 = opener.open(urllib.request.Request(
    f"{BASE}/api/admin/tools/servers"))
servers = json.loads(resp3.read())
for s in servers.get("servers", []):
    print(f"  {s['id']}: {s['name']} [{s['type']}]")
    print(f"    command: {s.get('command')} {s.get('args')}")
    print(f"    enabled: {s['enabled']}")
