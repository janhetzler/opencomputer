"""
chroma_inspect.py -- ChromaDB Inhalte auslesen und anzeigen.

Liest alle Collections und Dokumente aus ChromaDB.
Nützlich um zu pruefen ob Notes Agent korrekt gespeichert hat.

Verwendung:
    python3 scripts/hfspace/chroma_inspect.py

Voraussetzung:
    . /home/varxdev/la_env/bin/activate
    ChromaDB unter /tmp/chroma_la
"""

import chromadb
from pathlib import Path

CHROMA_PATH = "/tmp/chroma_la"

if not Path(CHROMA_PATH).exists():
    print(f"FAIL: ChromaDB Pfad nicht gefunden: {CHROMA_PATH}")
    exit(1)

client = chromadb.PersistentClient(path=CHROMA_PATH)
conn = client._client
conn.execute("PRAGMA wal_checkpoint(PASSIVE)")

collections = client.list_collections()
print(f"=== ChromaDB: {CHROMA_PATH} ===")
print(f"Collections: {len(collections)}")

for col in collections:
    print(f"\n--- Collection: {col.name} ---")
    c = client.get_collection(col.name)
    result = c.get()
    print(f"Eintraege: {len(result['ids'])}")
    for i, (doc_id, doc, meta) in enumerate(zip(
        result['ids'],
        result['documents'],
        result['metadatas']
    )):
        print(f"\n[{i+1}] ID: {doc_id}")
        print(f"     Meta: {meta}")
        print(f"     Text: {doc[:200]}")
