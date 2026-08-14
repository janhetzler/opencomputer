"""
cptr_litellm_switch.py -- LiteLLM Modell-Backend wechseln.

Stoppt LiteLLM, schreibt neue Config und startet neu.
Unterstuetzt Wechsel zwischen:
  - Granite-350m (:8090) -- leicht, kein Tool-Calling
  - Granite-Tiny  (:8080) -- 4B, Tool-Calling, empfohlen

Verwendung:
  python3 scripts/hfspace/cptr_litellm_switch.py 8080
  python3 scripts/hfspace/cptr_litellm_switch.py 8090

Voraussetzung:
  . /home/varxdev/la_env/bin/activate
  llama-server laeuft auf dem Ziel-Port
"""

import sys, os, subprocess, time, urllib.request

LITELLM_KEY = "sk-cos-local-dev"
EMBED_PORT  = 8081
CONFIG_PATH = "/tmp/litellm_hfspace.yaml"
LOG_PATH    = "/tmp/logs/litellm.log"
PID_PATH    = "/tmp/pids/litellm.pid"

if len(sys.argv) < 2 or sys.argv[1] not in ("8080", "8090"):
    print("Verwendung: python3 cptr_litellm_switch.py 8080|8090")
    sys.exit(1)

LLAMA_PORT = int(sys.argv[1])
MODEL_NAME = "Granite-Tiny (4B)" if LLAMA_PORT == 8080 \
             else "Granite-350m"

print(f"=== Wechsel auf {MODEL_NAME} (:${LLAMA_PORT}) ===",
      flush=True)

# 1. Ziel-Port pruefen
def port_active(port):
    try:
        urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=2)
        return True
    except:
        return False

if not port_active(LLAMA_PORT):
    print(f"FAIL: llama-server :{LLAMA_PORT} nicht erreichbar",
          flush=True)
    sys.exit(1)
print(f"OK: llama-server :{LLAMA_PORT} erreichbar", flush=True)

# 2. LiteLLM stoppen
print("\n=== Stoppe LiteLLM ===", flush=True)
subprocess.run(["pkill", "-TERM", "-f", "litellm"],
               capture_output=True)
time.sleep(3)
subprocess.run(["pkill", "-KILL", "-f", "litellm"],
               capture_output=True)
time.sleep(1)
print("LiteLLM gestoppt", flush=True)

# 3. Neue Config schreiben
print("\n=== Schreibe neue Config ===", flush=True)
config = f"""model_list:
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
"""
with open(CONFIG_PATH, "w") as f:
    f.write(config)
print(f"Config: {CONFIG_PATH}", flush=True)
print(f"  granite-tiny -> :${LLAMA_PORT}", flush=True)

# 4. LiteLLM starten
print("\n=== Starte LiteLLM ===", flush=True)
os.makedirs("/tmp/pids", exist_ok=True)
os.makedirs("/tmp/logs", exist_ok=True)
proc = subprocess.Popen(
    ["litellm", "--config", CONFIG_PATH,
     "--host", "127.0.0.1", "--port", "4000"],
    stdout=open(LOG_PATH, "w"),
    stderr=subprocess.STDOUT
)
with open(PID_PATH, "w") as f:
    f.write(str(proc.pid))
print(f"PID: {proc.pid}", flush=True)

# 5. Warten bis bereit
print("Warte auf LiteLLM...", end=" ", flush=True)
for i in range(90):
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:4000/health")
        req.add_header("Authorization", f"Bearer {LITELLM_KEY}")
        urllib.request.urlopen(req, timeout=3)
        print(f"OK ({i+1}s)", flush=True)
        break
    except:
        time.sleep(1)
        if (i+1) % 10 == 0:
            print(f"{i+1}s...", end=" ", flush=True)
else:
    print("TIMEOUT", flush=True)
    sys.exit(1)

# 6. Status
print(f"\n=== Fertig ===", flush=True)
print(f"LiteLLM laeuft mit {MODEL_NAME} (:${LLAMA_PORT})",
      flush=True)
print(f"Log: {LOG_PATH}", flush=True)
