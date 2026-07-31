"""
inspect_phoenix_hfspace.py -- Phoenix Trace Auswertung fuer HF Space.

Local Agent (LA) -- HF Space Edition

Voraussetzung: Stack laeuft bereits (start_hfspace.py ausgefuehrt).
  - llama-server :8090
  - Embedding-Server :8081
  - LiteLLM :4000
  - Phoenix :6006
  - Agent Server :8002

Ablauf:
  1. Stack-Bereitschaft pruefen
  2. Alle 6 Agenten testen
  3. Phoenix Traces auslesen
  4. Trace-Report nach /tmp/traces/ speichern

Verwendung:
  . /home/varxdev/la_env/bin/activate
  cd /home/varxdev/la && python3 /tmp/inspect_phoenix_hfspace.py

Umgebungsvariablen (optional):
  LA_REPO     (default: /home/varxdev/la)
  LITELLM_KEY (default: sk-cos-local-dev)
  LLAMA_PORT  (default: 8090)
"""
import time, urllib.request, json, sys, os
from datetime import datetime, timedelta
from pathlib import Path

# Konfiguration
LA_REPO     = os.getenv("LA_REPO",     "/home/varxdev/la")
LITELLM_KEY = os.getenv("LITELLM_KEY", "sk-cos-local-dev")
LLAMA_PORT  = int(os.getenv("LLAMA_PORT", "8090"))
PHOENIX_URL = "http://127.0.0.1:6006"
AGENT_URL   = "http://127.0.0.1:8002/v1/chat/completions"
AUTH        = f"Bearer {LITELLM_KEY}"
TRACE_DIR   = Path("/tmp/traces")
TRACE_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, LA_REPO)
sys.path.insert(0, os.path.join(LA_REPO, "agents", "server"))
sys.path.insert(0, os.path.join(LA_REPO, "agents", "ingestion"))

# Stack-Bereitschaft pruefen
print("=== PRE-FLIGHT: Stack-Check ===", flush=True)

def check_url(url, label, headers=None):
    try:
        req = urllib.request.Request(url)
        if headers:
            for k, v in headers.items(): req.add_header(k, v)
        urllib.request.urlopen(req, timeout=3)
        print(f"OK: {label}", flush=True)
        return True
    except Exception as e:
        print(f"FAIL: {label} -- {e}", flush=True)
        return False

ok = True
ok &= check_url(f"http://127.0.0.1:{LLAMA_PORT}/v1/models", f"llama-server :{LLAMA_PORT}")
ok &= check_url("http://127.0.0.1:4000/health", "LiteLLM :4000",
                headers={"Authorization": AUTH})
ok &= check_url(f"{PHOENIX_URL}/v1/projects", "Phoenix :6006")
ok &= check_url("http://127.0.0.1:8002/health", "Agent Server :8002")

if not ok:
    print("FAIL: Stack nicht vollstaendig bereit -- start_hfspace.py zuerst ausfuehren", flush=True)
    sys.exit(1)

print("Stack bereit.\n", flush=True)

# 6-Agenten-Testlauf
print("=== 6-AGENTEN-TESTLAUF ===", flush=True)
print(f"Start: {datetime.now().isoformat()}", flush=True)

results = []

def chat(frage, max_tokens=300):
    t0 = time.time()
    payload = {"model": "agent-local",
               "messages": [{"role": "user", "content": frage}]}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    req = urllib.request.Request(
        AGENT_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": AUTH},
        method="POST"
    )
    try:
        r = urllib.request.urlopen(req, timeout=120)
        resp = json.loads(r.read())
        text = resp["choices"][0]["message"]["content"]
        return text, round(time.time()-t0, 1), 200
    except Exception as e:
        return str(e), round(time.time()-t0, 1), 0

def test_agent(name, frage, max_tokens=300):
    print(f"\n--- {name} ---", flush=True)
    text, elapsed, status = chat(frage, max_tokens)
    ok = status == 200 and len(text.strip()) >= 10
    print(f"Antwort: {text[:200]}", flush=True)
    print(f"Zeit: {elapsed}s | HTTP: {status} | {'OK' if ok else 'FAIL'}", flush=True)
    results.append({"agent": name, "status": "OK" if ok else "FAIL",
                    "http": status, "zeit": elapsed,
                    "laenge": len(text.strip()), "antwort": text[:500]})
    return text

# Tests
text_supervisor, t_sup, s_sup = chat("Can you help me?", max_tokens=None)
sup_ok = s_sup == 200 and len(text_supervisor.strip()) >= 10
results.append({"agent": "Supervisor Routing", "status": "OK" if sup_ok else "FAIL",
                "http": s_sup, "zeit": t_sup,
                "laenge": len(text_supervisor.strip()), "antwort": text_supervisor[:500]})
print(f"\n--- Supervisor Routing ---", flush=True)
print(f"Antwort: {text_supervisor[:200]}", flush=True)
print(f"Zeit: {t_sup}s | {'OK' if sup_ok else 'FAIL'}", flush=True)

test_agent("Comms Agent",
    "Write a short professional email to the team about the project status.")
test_agent("Code Agent",
    "Write a Python function with type hints and docstring that sorts a list.")
test_agent("Researcher Agent",
    "What is LangGraph and how do multi-agent systems work with it?")
test_agent("Notes Agent",
    "Save this note: LA Stack mit Phoenix Tracing laeuft auf HF Space Free Tier.")
test_agent("Handoff Agent",
    "Prepare a prompt for Claude.ai: analyse local LLMs vs Cloud APIs.")

print(f"\nEnde: {datetime.now().isoformat()}", flush=True)
ok_count = sum(1 for r in results if r["status"] == "OK")
print(f"Tests: {ok_count}/{len(results)} OK", flush=True)

# Warten auf Trace-Delivery
print("\nWarte 8s auf Trace-Delivery...", flush=True)
time.sleep(8)

# Phoenix Traces auslesen
print("\n=== PHOENIX TRACES ===", flush=True)
span_output = ""
try:
    from phoenix.client import Client

    client = Client(base_url=PHOENIX_URL)
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

report_lines = [f"# HF Space Trace Report -- {date_str}\n"]
report_lines.append(f"**Tests:** {ok_count}/{len(results)} OK\n")
report_lines.append("\n## Testergebnisse\n")
for r in results:
    report_lines.append(
        f"- {'OK' if r['status'] == 'OK' else 'FAIL'} **{r['agent']}**: "
        f"{r['laenge']} Zeichen | {r['zeit']}s | HTTP {r['http']}\n"
    )
report_lines.append("\n## Phoenix Spans\n")
report_lines.append(f"```\n{span_output}\n```\n")

trace_path.write_text("".join(report_lines), encoding="utf-8")
print(f"\nTrace-Report: {trace_path}", flush=True)
print(f"Groesse: {trace_path.stat().st_size} Bytes", flush=True)
