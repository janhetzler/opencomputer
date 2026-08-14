"""
cptr_db_export.py -- cptr SQLite Datenbank vollstaendig auslesen.

Liest alle Tabellen aus app.db (WAL-sicher) und exportiert sie
als JSON nach /tmp/cptr_export/.

Verwendung:
    python3 scripts/hfspace/cptr_db_export.py

Output:
    /tmp/cptr_export/app.db          -- Kopie der DB
    /tmp/cptr_export/config.json     -- App-Config
    /tmp/cptr_export/users.json      -- User-Profile
    /tmp/cptr_export/user_states.json -- UI-Settings pro User
    /tmp/cptr_export/chats.json      -- Chat-Metadaten
    /tmp/cptr_export/chat_messages.json -- Alle Nachrichten
    /tmp/cptr_export/workspaces.json -- Workspace-Zustand
    /tmp/cptr_export/automations.json -- Scheduled Tasks
    /tmp/cptr_export/files.json      -- Hochgeladene Dateien
"""

import sqlite3, json, shutil
from pathlib import Path

DB = "/home/varxdev/.cptr/app.db"
OUT = Path("/tmp/cptr_export")
OUT.mkdir(exist_ok=True)

# DB kopieren (WAL-safe)
shutil.copy2(DB, OUT / "app.db")
try:
    shutil.copy2(DB + "-shm", OUT / "app.db-shm")
    shutil.copy2(DB + "-wal", OUT / "app.db-wal")
except FileNotFoundError:
    pass

conn = sqlite3.connect(str(OUT / "app.db"))
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA wal_checkpoint(PASSIVE)")

def export_table(table: str) -> list:
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    return [dict(row) for row in rows]

# Config
rows = conn.execute("SELECT key, value FROM config").fetchall()
config = {}
for k, v in rows:
    try:
        config[k] = json.loads(v) if isinstance(v, str) else v
    except Exception:
        config[k] = v
with open(OUT / "config.json", "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
print(f"✓ config.json -- {len(config)} Keys")

# Users (ohne Passwort-Hash)
users = export_table("users")
with open(OUT / "users.json", "w") as f:
    json.dump(users, f, indent=2, ensure_ascii=False)
print(f"✓ users.json -- {len(users)} User")

# User States (UI-Settings)
states = export_table("user_states")
for s in states:
    if isinstance(s.get("data"), str):
        try:
            s["data"] = json.loads(s["data"])
        except Exception:
            pass
with open(OUT / "user_states.json", "w") as f:
    json.dump(states, f, indent=2, ensure_ascii=False)
print(f"✓ user_states.json -- {len(states)} Eintraege")

# Chats
chats = export_table("chats")
for c in chats:
    if isinstance(c.get("meta"), str):
        try:
            c["meta"] = json.loads(c["meta"])
        except Exception:
            pass
with open(OUT / "chats.json", "w") as f:
    json.dump(chats, f, indent=2, ensure_ascii=False)
print(f"✓ chats.json -- {len(chats)} Chats")

# Chat Messages
msgs = export_table("chat_messages")
for m in msgs:
    for field in ("output", "usage", "meta"):
        if isinstance(m.get(field), str):
            try:
                m[field] = json.loads(m[field])
            except Exception:
                pass
with open(OUT / "chat_messages.json", "w") as f:
    json.dump(msgs, f, indent=2, ensure_ascii=False)
print(f"✓ chat_messages.json -- {len(msgs)} Nachrichten")

# Workspaces
workspaces = export_table("workspaces")
for w in workspaces:
    if isinstance(w.get("data"), str):
        try:
            w["data"] = json.loads(w["data"])
        except Exception:
            pass
with open(OUT / "workspaces.json", "w") as f:
    json.dump(workspaces, f, indent=2, ensure_ascii=False)
print(f"✓ workspaces.json -- {len(workspaces)} Workspaces")

# Automations
automations = export_table("automations")
with open(OUT / "automations.json", "w") as f:
    json.dump(automations, f, indent=2, ensure_ascii=False)
print(f"✓ automations.json -- {len(automations)} Tasks")

# Files
files = export_table("files")
with open(OUT / "files.json", "w") as f:
    json.dump(files, f, indent=2, ensure_ascii=False)
print(f"✓ files.json -- {len(files)} Dateien")

conn.close()
print(f"\nAlle Exports in: {OUT}/")
