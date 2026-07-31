"""
start_hfspace.py -- LA Stack Start fuer HF Space.

Local Agent (LA) -- HF Space Edition

Startet: llama-server (Port 8090), Embedding-Server (Port 8081),
         Phoenix (Port 6006), LiteLLM (Port 4000), Agent Server (Port 8002)

Stack 1 (cptr + Granite-Tiny auf Port 8080/7860) laeuft bereits -- wird
nicht angefasst.

Verwendung:
  . /home/varxdev/la_env/bin/activate
  cd /home/varxdev/la && python3 scripts/hfspace/start_hfspace.py

Umgebungsvariablen (alle optional):
  LLAMA_SERVER_BIN  (default: /opt/llama/llama-server)
  MODEL_PATH        (default: /tmp/granite-350m-Q4_K_M.gguf)
  EMBED_MODEL_PATH  (default: /tmp/granite-embedding-30m-Q4_0.gguf)
  LLAMA_PORT        (default: 8090)
  EMBED_PORT        (default: 8081)
  CHROMA_PATH       (default: /tmp/chroma_la)
  LITELLM_KEY       (default: sk-cos-local-dev)

Logs: /tmp/logs/
"""
import threading, time, urllib.request, json, subprocess, sys, os
import uvicorn
from datetime import datetime

# Konfiguration
LLAMA_BIN        = os.getenv("LLAMA_SERVER_BIN",  "/opt/llama/llama-server")
MODEL_PATH       = os.getenv("MODEL_PATH",        "/tmp/granite-350m-Q4_K_M.gguf")
EMBED_MODEL_PATH = os.getenv("EMBED_MODEL_PATH",  "/tmp/granite-embedding-30m-Q4_0.gguf")
LLAMA_PORT       = int(os.getenv("LLAMA_PORT",    "8090"))
EMBED_PORT       = int(os.getenv("EMBED_PORT",    "8081"))
CHROMA_PATH      = os.getenv("CHROMA_PATH",       "/tmp/chroma_la")
LITELLM_KEY      = os.getenv("LITELLM_KEY",       "sk-cos-local-dev")
AGENT_URL        = "http://127.0.0.1:8002/v1/chat/completions"
LOG_DIR          = "/tmp/logs"
AUTH             = f"Bearer {LITELLM_KEY}"

LA_REPO = os.getenv("LA_REPO", "/home/varxdev/la")
os.makedirs(CHROMA_PATH, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
sys.path.insert(0, LA_REPO)
sys.path.insert(0, os.path.join(LA_REPO, "agents", "server"))
sys.path.insert(0, os.path.join(LA_REPO, "agents", "ingestion"))

# Pre-Flight Checks
print("=== PRE-FLIGHT CHECKS ===", flush=True)
if not os.path.exists(LLAMA_BIN):
    print(f"FAIL: llama-server Binary nicht gefunden: {LLAMA_BIN}", flush=True)
    sys.exit(1)
print(f"OK: llama-server Binary: {LLAMA_BIN}", flush=True)

if not os.path.exists(MODEL_PATH):
    print(f"FAIL: Reasoning-Modell nicht gefunden: {MODEL_PATH}", flush=True)
    sys.exit(1)
print(f"OK: Reasoning-Modell: {MODEL_PATH}", flush=True)

if not os.path.exists(EMBED_MODEL_PATH):
    print(f"FAIL: Embedding-Modell nicht gefunden: {EMBED_MODEL_PATH}", flush=True)
    sys.exit(1)
print(f"OK: Embedding-Modell: {EMBED_MODEL_PATH}", flush=True)

# Port-Check
import socket
for port in [LLAMA_PORT, EMBED_PORT, 4000, 6006, 8002]:
    s = socket.socket()
    try:
        s.connect(("127.0.0.1", port))
        print(f"FAIL: Port {port} bereits belegt!", flush=True)
        sys.exit(1)
    except:
        print(f"OK: Port {port} frei", flush=True)
    finally:
        s.close()

# Hilfsfunktionen
def wait_for(url, label, retries=40, headers=None):
    for i in range(retries):
        try:
            req = urllib.request.Request(url)
            if headers:
                for k, v in headers.items(): req.add_header(k, v)
            urllib.request.urlopen(req, timeout=2)
            print(f"{label} OK", flush=True); return True
        except:
            time.sleep(1); print(f"{i+1}...", end=" ", flush=True)
    print(f"{label} TIMEOUT", flush=True); return False

ERROR_PATTERNS = ["ERROR:", "Exception:", "Traceback", "CRITICAL"]

def check_log(log_file, label):
    if not os.path.exists(log_file):
        print(f"  [{label}] Log nicht gefunden", flush=True); return True
    with open(log_file) as f:
        lines = f.readlines()
    found = [l.strip()[:120] for l in lines if any(p in l for p in ERROR_PATTERNS)]
    if found:
        print(f"  [{label}] Fehler gefunden:", flush=True)
        for line in found[:5]: print(f"    {line}", flush=True)
        return False
    print(f"  [{label}] Log sauber ({len(lines)} Zeilen)", flush=True)
    return True

# 1. llama-server Reasoning (Port 8090)
print("\n=== STARTE llama-server :8090 ===", flush=True)
LLAMA_LOG = os.path.join(LOG_DIR, "llama-server-la.log")
llama_proc = subprocess.Popen(
    [LLAMA_BIN, "-m", MODEL_PATH,
     "--host", "127.0.0.1", "--port", str(LLAMA_PORT),
     "--jinja", "--ctx-size", "32768",
     "--parallel", "1", "--log-disable", "--embeddings", "--pooling", "mean"],
    stdout=open(LLAMA_LOG, "w"), stderr=subprocess.STDOUT
)
wait_for(f"http://127.0.0.1:{LLAMA_PORT}/v1/models", "llama-server :8090", retries=40)

# Inference-Readiness-Check
print("Warte auf Inference-Bereitschaft...", flush=True)
for i in range(20):
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions",
            data=json.dumps({"model": "granite", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}).encode(),
            headers={"Content-Type": "application/json"}, method="POST"
        )
        urllib.request.urlopen(req, timeout=15)
        print("llama-server :8090 Inference OK", flush=True); break
    except:
        time.sleep(2); print(f"{i+1}...", end=" ", flush=True)

# 2. Embedding-Server (Port 8081)
print("\n=== STARTE Embedding-Server :8081 ===", flush=True)
EMBED_LOG = os.path.join(LOG_DIR, "llama-server-embed-la.log")
embed_proc = subprocess.Popen(
    [LLAMA_BIN, "-m", EMBED_MODEL_PATH,
     "--host", "127.0.0.1", "--port", str(EMBED_PORT),
     "--embeddings", "--pooling", "mean",
     "--parallel", "1", "--log-disable"],
    stdout=open(EMBED_LOG, "w"), stderr=subprocess.STDOUT
)
wait_for(f"http://127.0.0.1:{EMBED_PORT}/v1/models", "Embedding-Server :8081")

# 3. Phoenix (Port 6006)
print("\n=== STARTE Phoenix :6006 ===", flush=True)
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://127.0.0.1:6006/v1/traces"
os.environ["PHOENIX_CLIENT_HEADERS"]     = "api_key=not-needed"
phoenix_proc = subprocess.Popen(
    ["python3", "-m", "phoenix.server.main", "serve", "--host", "127.0.0.1", "--port", "6006"],
    stdout=open(os.path.join(LOG_DIR, "phoenix-la.log"), "w"), stderr=subprocess.STDOUT
)
wait_for("http://127.0.0.1:6006/healthz", "Phoenix :6006")

# 4. LiteLLM (Port 4000)
print("\n=== STARTE LiteLLM :4000 ===", flush=True)
litellm_cfg = f"""
model_list:
  - model_name: granite-tiny
    litellm_params:
      model: openai/granite
      api_base: http://127.0.0.1:{LLAMA_PORT}/v1
      api_key: not-needed
  - model_name: granite-embed
    litellm_params:
      model: openai/granite-embed
      api_base: http://127.0.0.1:{EMBED_PORT}/v1
      api_key: not-needed
  - model_name: agent-local
    litellm_params:
      model: openai/agent-local
      api_base: http://127.0.0.1:8002/v1
      api_key: not-needed
general_settings:
  master_key: {LITELLM_KEY}
litellm_settings:
  drop_params: true
  set_verbose: false
  success_callback: ["arize_phoenix"]
  failure_callback: ["arize_phoenix"]
"""
with open("/tmp/litellm_hfspace.yaml", "w") as f: f.write(litellm_cfg)
litellm_proc = subprocess.Popen(
    ["litellm", "--config", "/tmp/litellm_hfspace.yaml", "--host", "127.0.0.1", "--port", "4000"],
    env=os.environ.copy(),
    stdout=open(os.path.join(LOG_DIR, "litellm-la.log"), "w"), stderr=subprocess.STDOUT
)
wait_for("http://127.0.0.1:4000/health", "LiteLLM :4000", retries=90,
         headers={"Authorization": f"Bearer {LITELLM_KEY}"})

# LiteLLM Readiness-Check
print("Warte auf LiteLLM -> llama-server...", flush=True)
for i in range(30):
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:4000/v1/chat/completions",
            data=json.dumps({"model": "granite-tiny",
                "messages": [{"role": "user", "content": "hi"}], "max_tokens": 3}).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {LITELLM_KEY}"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=30)
        print("LiteLLM -> llama-server OK", flush=True); break
    except:
        time.sleep(2); print(f"{i+1}...", end=" ", flush=True)

# 5. Agent Config + Phoenix Init
print("\n=== KONFIGURIERE AGENT SERVER ===", flush=True)

# mcp.json zur Laufzeit generieren -- LA_REPO statt hardkodiertem /home/claude/la
MCP_JSON_PATH = "/tmp/mcp_hfspace.json"
mcp_config = {
    "mcpServers": {
        "git": {
            "command": "python3",
            "args": ["-m", "mcp_server_git", "--repository", LA_REPO],
            "transport": "stdio",
            "description": "Git Repository Tools"
        },
        "fetch": {
            "command": "python3",
            "args": ["-m", "mcp_server_fetch"],
            "transport": "stdio",
            "description": "Web Content Fetching"
        }
    }
}
with open(MCP_JSON_PATH, "w") as f:
    json.dump(mcp_config, f, indent=2)
os.environ["MCP_CONFIG_PATH"] = MCP_JSON_PATH
print(f"mcp.json generiert: {MCP_JSON_PATH} (repo: {LA_REPO})", flush=True)

import config
config.LITELLM_URL = "http://127.0.0.1:4000"
config.LITELLM_KEY = LITELLM_KEY
config.DEFAULT_LLM = "granite-tiny"
config.CHROMA_PATH = CHROMA_PATH
os.environ["OPENAI_API_KEY"] = LITELLM_KEY

try:
    from telemetry import init_phoenix
    init_phoenix()
    print("Phoenix Tracing OK", flush=True)
except Exception as e:
    print(f"Phoenix Tracing: {e}", flush=True)

# 6. Agent Server (Port 8002)
print("\n=== STARTE Agent Server :8002 ===", flush=True)
AGENT_LOG = os.path.join(LOG_DIR, "agent-server-la.log")
import server as agent_server

def run_agent_server():
    uvicorn.Server(uvicorn.Config(
        agent_server.app, host="127.0.0.1", port=8002,
        log_level="error"
    )).run()

threading.Thread(target=run_agent_server, daemon=True).start()
wait_for("http://127.0.0.1:8002/health", "Agent Server :8002")

# ChromaDB initialisieren
import chromadb as _chromadb
_chroma_client = _chromadb.PersistentClient(path=CHROMA_PATH)
_chroma_client.get_or_create_collection(name="notes", metadata={"hnsw:space": "cosine"})
print("ChromaDB notes-Collection OK (cosine)", flush=True)

# Test Suite
print("\n=== STACK BEREIT - STARTE TEST SUITE ===\n", flush=True)
print(f"Start: {datetime.now().isoformat()}", flush=True)
print(f"llama-server: Port {LLAMA_PORT}", flush=True)
print(f"Embedding:    Port {EMBED_PORT}", flush=True)
print(f"LiteLLM:      Port 4000", flush=True)
print(f"Phoenix:      Port 6006", flush=True)
print(f"Agent Server: Port 8002", flush=True)

results = []

def api_call(url, data=None, method="GET"):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", AUTH)
    if data:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    try:
        r = urllib.request.urlopen(req, timeout=120)
        return json.loads(r.read()), r.status
    except Exception as e:
        return {"error": str(e)}, 0

def chat(frage, max_tokens=300):
    t0 = time.time()
    payload = {"model": "agent-local", "messages": [{"role": "user", "content": frage}]}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    resp, status = api_call(AGENT_URL, data=payload, method="POST")
    elapsed = time.time() - t0
    if "choices" in resp:
        return resp["choices"][0]["message"]["content"], elapsed, status
    return str(resp), elapsed, status

def validate_response(text, min_length=10):
    if not text or text.strip() == "": return False, "Antwort leer"
    if len(text.strip()) < min_length: return False, f"Zu kurz ({len(text.strip())} Zeichen)"
    return True, f"OK ({len(text.strip())} Zeichen)"

def test_agent(name, frage, notes_check=False):
    print("\n" + "="*55, flush=True)
    print(f"TEST: {name}", flush=True)
    text, elapsed, status = chat(frage)
    print(f"Antwort: {text[:200]}", flush=True)
    print(f"Zeit: {elapsed:.1f}s | HTTP: {status}", flush=True)
    content_ok, content_reason = validate_response(text)
    overall_ok = (status == 200) and content_ok
    print(f"Ergebnis: {'OK' if overall_ok else 'FAIL'} - {content_reason}", flush=True)
    results.append({"agent": name, "status": "OK" if overall_ok else "FAIL",
                    "http": status, "reason": content_reason, "zeit": round(elapsed, 1)})

# Tests
text_meta, elapsed_meta, status_meta = chat("Can you help me?", max_tokens=None)
content_ok, content_reason = validate_response(text_meta)
results.append({"agent": "Supervisor Routing", "status": "OK" if (status_meta == 200 and content_ok) else "FAIL",
                "http": status_meta, "reason": content_reason, "zeit": round(elapsed_meta, 1)})
print(f"\nSupervisor Routing: {'OK' if (status_meta == 200 and content_ok) else 'FAIL'}", flush=True)

test_agent("Comms Agent",      "Write a short professional email to the team about the project status.")
test_agent("Code Agent",       "Write a Python function with type hints and docstring that sorts a list.")
test_agent("Researcher Agent", "What is LangGraph and how do multi-agent systems work with it?")
test_agent("Notes Agent",      "Save this note: LA Stack laeuft auf HF Space Free Tier.")
test_agent("Handoff Agent",    "Prepare a prompt for Claude.ai: analyse local LLMs vs Cloud APIs.")

# Zusammenfassung
print("\n" + "="*55, flush=True)
print("ZUSAMMENFASSUNG", flush=True)
print(f"Ende: {datetime.now().isoformat()}", flush=True)
ok = sum(1 for r in results if r["status"] == "OK")
print(f"Tests: {ok}/{len(results)} OK", flush=True)
for r in results:
    print(f"  {'OK' if r['status'] == 'OK' else 'FAIL'} {r['agent']}: {r['reason']}", flush=True)

report = {"timestamp": datetime.now().isoformat(), "results": results,
          "summary": {"total": len(results), "ok": ok},
          "environment": {"llama_port": LLAMA_PORT, "embed_port": EMBED_PORT}}
with open("/tmp/test_results_hfspace.json", "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print("\nReport: /tmp/test_results_hfspace.json", flush=True)

# Phoenix Inspect -- laeuft waehrend Stack noch aktiv
print("\n=== PHOENIX INSPECT ===", flush=True)
from pathlib import Path
from datetime import datetime, timedelta

TRACE_DIR = Path("/tmp/traces")
TRACE_DIR.mkdir(parents=True, exist_ok=True)

print("Warte 5s auf Trace-Delivery...", flush=True)
time.sleep(5)

span_output = ""
try:
    from phoenix.client import Client
    client = Client(base_url="http://127.0.0.1:6006")
    spans_df = client.spans.get_spans_dataframe(
        project_identifier="local-agent",
        limit=100,
        root_spans_only=True,
        start_time=datetime.now() - timedelta(minutes=15)
    )
    if spans_df is not None and not spans_df.empty:
        print(f"{len(spans_df)} Spans gefunden:", flush=True)
        cols = [c for c in [
            "name", "span_kind",
            "attributes.llm.model_name",
            "attributes.llm.token_count.prompt",
            "attributes.llm.token_count.completion",
            "status_code", "latency_ms"
        ] if c in spans_df.columns]
        for _, row in spans_df[cols].iterrows():
            line = f"  {row.get('name','?')} | {row.get('status_code','?')} | {row.get('latency_ms','?')}ms"
            print(line, flush=True)
            span_output += line + "\n"
    else:
        print("Keine Spans gefunden.", flush=True)
        span_output = "Keine Spans gefunden."
except Exception as e:
    print(f"Phoenix Client Fehler: {e}", flush=True)
    span_output = f"Fehler: {e}"

# Trace-Report speichern
date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
trace_path = TRACE_DIR / f"hfspace_{date_str}.md"
ok_count = sum(1 for r in results if r["status"] == "OK")
report_lines = [f"# HF Space Trace Report -- {date_str}\n\n"]
report_lines.append(f"**Tests:** {ok_count}/{len(results)} OK\n\n")
report_lines.append("## Testergebnisse\n\n")
for r in results:
    report_lines.append(
        f"- {'OK' if r['status'] == 'OK' else 'FAIL'} **{r['agent']}**: "
        f"{r['reason']} | {r['zeit']}s | HTTP {r['http']}\n"
    )
report_lines.append("\n## Phoenix Spans\n\n```\n")
report_lines.append(span_output)
report_lines.append("\n```\n")
trace_path.write_text("".join(report_lines), encoding="utf-8")
print(f"Trace-Report: {trace_path}", flush=True)

print("Stack laeuft.", flush=True)
litellm_proc.wait()
