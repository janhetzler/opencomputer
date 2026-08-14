#!/bin/sh
# la_stack.sh -- LA Stack starten und stoppen
#
# Verwendung:
#   sh la_stack.sh start   -- Stack starten + Chat
#   sh la_stack.sh stop    -- Stack sauber stoppen
#   sh la_stack.sh status  -- Status aller Ports
#
# Voraussetzung fuer start:
#   . /home/varxdev/la_env/bin/activate
#   llama-server :8090 und :8081 laufen (via Docker start.sh)
#
# PIDs: /tmp/pids/
# Logs: /tmp/logs/

LA_REPO=/home/varxdev/la
LITELLM_KEY=sk-cos-local-dev
LLAMA_PORT=8090
EMBED_PORT=8081

# ── Hilfsfunktionen ────────────────────────────────────────

port_active() {
  curl -s http://localhost:$1/health > /dev/null 2>&1 \
    || curl -s http://localhost:$1/healthz > /dev/null 2>&1
}

wait_for_port() {
  PORT=$1
  LABEL=$2
  RETRIES=${3:-30}
  i=0
  while [ $i -lt $RETRIES ]; do
    port_active $PORT && echo "OK $LABEL :$PORT" && return 0
    i=$((i+1))
    sleep 1
  done
  echo "TIMEOUT $LABEL :$PORT"
  return 1
}

# ── Stop ───────────────────────────────────────────────────

do_stop() {
  echo "=== Stoppe LA Stack ==="
  pkill -TERM -f "phoenix.server.main" 2>/dev/null
  pkill -TERM -f "litellm" 2>/dev/null
  pkill -TERM -f "uvicorn server:app" 2>/dev/null
  sleep 3
  pkill -KILL -f "phoenix.server.main" 2>/dev/null
  pkill -KILL -f "litellm" 2>/dev/null
  pkill -KILL -f "uvicorn server:app" 2>/dev/null
  rm -f /tmp/pids/phoenix.pid \
        /tmp/pids/litellm.pid \
        /tmp/pids/agent-server.pid
  sleep 2
  echo "=== Verifikation ==="
  for port in 6006 4000 8002; do
    port_active $port \
      && echo "WARN :$port noch aktiv" \
      || echo "OK   :$port gestoppt"
  done
  pgrep -a -f "phoenix|litellm|uvicorn" \
    || echo "Alle LA Prozesse gestoppt"
}

# ── Status ─────────────────────────────────────────────────

do_status() {
  echo "=== Stack Status ==="
  for port in 8090 8081 6006 4000 8002 7860; do
    port_active $port \
      && echo "AKTIV :$port" \
      || echo "FREI  :$port"
  done
  echo ""
  echo "=== PIDs ==="
  ls /tmp/pids/*.pid 2>/dev/null | while read f; do
    echo "  $(basename $f): $(cat $f)"
  done || echo "  Keine PID-Dateien"
}

# ── Start ──────────────────────────────────────────────────

do_start() {
  mkdir -p /tmp/pids /tmp/logs /tmp/chroma_la

  echo "=== Voraussetzungen ==="
  port_active $LLAMA_PORT \
    && echo "OK llama-server :$LLAMA_PORT" \
    || { echo "FAIL :$LLAMA_PORT -- Abbruch"; exit 1; }
  port_active $EMBED_PORT \
    && echo "OK Embedding :$EMBED_PORT" \
    || { echo "FAIL :$EMBED_PORT -- Abbruch"; exit 1; }

  # Phoenix
  echo ""
  echo "=== Phoenix :6006 ==="
  if port_active 6006; then
    echo "Bereits aktiv"
  else
    nohup python3 -m phoenix.server.main serve \
      --host 127.0.0.1 \
      --port 6006 \
      > /tmp/logs/phoenix.log 2>&1 &
    sleep 2
    pgrep -f "phoenix.server.main" \
      > /tmp/pids/phoenix.pid
    echo "PID: $(cat /tmp/pids/phoenix.pid)"
    wait_for_port 6006 "Phoenix" 30 \
      || { echo "FAIL Phoenix -- Log:"; \
           tail -5 /tmp/logs/phoenix.log; exit 1; }
  fi

  # LiteLLM
  echo ""
  echo "=== LiteLLM :4000 ==="
  if port_active 4000; then
    echo "Bereits aktiv"
  else
    cat > /tmp/litellm_hfspace.yaml << EOF
model_list:
  - model_name: granite-tiny
    litellm_params:
      model: openai/granite
      api_base: http://127.0.0.1:${LLAMA_PORT}/v1
      api_key: not-needed
  - model_name: granite-embed
    litellm_params:
      model: openai/granite-embed
      api_base: http://127.0.0.1:${EMBED_PORT}/v1
      api_key: not-needed
  - model_name: agent-local
    litellm_params:
      model: openai/agent-local
      api_base: http://127.0.0.1:8002/v1
      api_key: not-needed
general_settings:
  master_key: ${LITELLM_KEY}
litellm_settings:
  drop_params: true
  set_verbose: false
EOF
    nohup litellm \
      --config /tmp/litellm_hfspace.yaml \
      --host 127.0.0.1 \
      --port 4000 \
      > /tmp/logs/litellm.log 2>&1 &
    sleep 2
    pgrep -f "litellm" \
      > /tmp/pids/litellm.pid
    echo "PID: $(cat /tmp/pids/litellm.pid)"
    wait_for_port 4000 "LiteLLM" 90 \
      || { echo "FAIL LiteLLM -- Log:"; \
           tail -5 /tmp/logs/litellm.log; exit 1; }
  fi

  # Agent Server
  echo ""
  echo "=== Agent Server :8002 ==="
  if port_active 8002; then
    echo "Bereits aktiv"
  else
    cat > /tmp/mcp_hfspace.json << EOF
{
  "mcpServers": {
    "git": {
      "command": "/home/varxdev/la_env/bin/python3",
      "args": ["-m", "mcp_server_git",
               "--repository", "${LA_REPO}"],
      "transport": "stdio"
    },
    "fetch": {
      "command": "/home/varxdev/la_env/bin/python3",
      "args": ["-m", "mcp_server_fetch"],
      "transport": "stdio"
    }
  }
}
EOF
    cd ${LA_REPO}
    MCP_CONFIG_PATH=/tmp/mcp_hfspace.json \
    OPENAI_API_KEY=${LITELLM_KEY} \
    PYTHONPATH=${LA_REPO}/agents/server \
    nohup uvicorn server:app \
      --host 127.0.0.1 \
      --port 8002 \
      > /tmp/logs/agent-server.log 2>&1 &
    sleep 2
    pgrep -f "uvicorn server:app" \
      > /tmp/pids/agent-server.pid
    echo "PID: $(cat /tmp/pids/agent-server.pid)"
    wait_for_port 8002 "Agent Server" 30 \
      || { echo "FAIL Agent Server -- Log:"; \
           tail -5 /tmp/logs/agent-server.log; exit 1; }
  fi

  # Status
  echo ""
  do_status

  # Chat starten
  echo ""
  echo "=== Chat Interface ==="
  echo "Stack bereit. Starte Chat..."
  echo ""
  cd ${LA_REPO}
  LITELLM_URL=http://127.0.0.1:4000 \
  LITELLM_KEY=${LITELLM_KEY} \
  python3 scripts/chat.py
}

# ── Main ───────────────────────────────────────────────────

case "$1" in
  start)  do_start ;;
  stop)   do_stop ;;
  status) do_status ;;
  *)
    echo "Verwendung: sh la_stack.sh start|stop|status"
    exit 1
    ;;
esac
