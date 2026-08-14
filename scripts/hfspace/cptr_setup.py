"""
cptr_setup.py -- cptr fuer LA Stack konfigurieren.

Fuehrt folgende Schritte aus:
1. Connection auf LiteLLM :4000 umbiegen
2. MCP Server konfigurieren (mcp_git, mcp_fetch)
3. Konfiguration verifizieren

Verwendung:
    python3 scripts/hfspace/cptr_setup.py

Voraussetzung:
    cptr laeuft auf :7860
    LA Stack laeuft (LiteLLM :4000, Agent Server :8002)
"""

import urllib.request, json, http.cookiejar

BASE = "http://localhost:7860"
CONN_ID = "33597f72-5ec3-4c56-9e00-e28b7884cb44"
LITELLM_KEY = "sk-cos-local-dev"
LA_REPO = "/home/varxdev/la"
LA_ENV_PYTHON = "/home/varxdev/la_env/bin/python3"

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

# 1. Connection auf LiteLLM umbiegen
print("\n=== Connection auf LiteLLM :4000 ===", flush=True)
update = {
    "name": "LA Agent Stack",
    "base_url": f"http://127.0.0.1:4000/v1",
    "api_key": LITELLM_KEY,
    "provider_type": "default"
}
req = urllib.request.Request(
    f"{BASE}/api/admin/connections/{CONN_ID}",
    data=json.dumps(update).encode(),
    headers={"Content-Type": "application/json"},
    method="PUT"
)
resp = opener.open(req)
print(f"Connection: {resp.status} {resp.read().decode()}")

# Verifikation
resp2 = opener.open(urllib.request.Request(
    f"{BASE}/api/admin/connections"))
conns = json.loads(resp2.read())
for c in conns["connections"]:
    print(f"  {c['name']} -> {c['base_url']}")

# 2. MCP Server konfigurieren
print("\n=== MCP Server konfigurieren ===", flush=True)
servers = [
    {
        "id": "mcp_git",
        "type": "mcp_stdio",
        "name": "Git Tools",
        "description": "git log, status, diff, commit",
        "command": LA_ENV_PYTHON,
        "args": [
            "-m", "mcp_server_git",
            "--repository", LA_REPO
        ],
        "enabled": True
    },
    {
        "id": "mcp_fetch",
        "type": "mcp_stdio",
        "name": "Web Fetch",
        "description": "Web Content Fetching",
        "command": LA_ENV_PYTHON,
        "args": ["-m", "mcp_server_fetch"],
        "enabled": True
    }
]

for server in servers:
    try:
        req = urllib.request.Request(
            f"{BASE}/api/admin/tools/servers",
            data=json.dumps(server).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = opener.open(req)
        print(f"  {server['id']}: {resp.status} {resp.read().decode()[:60]}")
    except Exception as e:
        print(f"  {server['id']}: {e}")

# 3. Verifikation Tool Server
print("\n=== Verifikation ===", flush=True)
resp3 = opener.open(urllib.request.Request(
    f"{BASE}/api/admin/tools/servers"))
servers_list = json.loads(resp3.read())
for s in servers_list.get("servers", []):
    print(f"  {s['id']}: {s['name']} [{s['type']}] enabled={s['enabled']}")

print("\ncptr Setup abgeschlossen.", flush=True)
