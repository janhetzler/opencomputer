#!/bin/sh
# la_stack_start.sh -- LA Stack starten (Stack 1 laeuft bereits)
#
# Startet: Phoenix :6006, LiteLLM :4000, Agent Server :8002
# Voraussetzung: llama-server :8090 und :8081 laufen (via Docker start.sh)
#
# Verwendung:
#   . /home/varxdev/la_env/bin/activate
#   sh /home/varxdev/la/scripts/hfspace/la_stack_start.sh
#
# PIDs: /tmp/pids/phoenix.pid, /tmp/pids/litellm.pid
# Logs: /tmp/logs/phoenix.log, /tmp/logs/litellm.log, /tmp/logs/agent-server.log

LA_REPO=/home/varxdev/la
LITELLM_KEY=sk-cos-local-dev
LLAMA_PORT=8090
EMBED_PORT=8081

# Verzeichnisse anlegen
mkdir -p /tmp/pids /tmp/logs /tmp/chroma_la

echo "=== Voraussetzungen ==="
curl -s http://localhost:${LLAMA_PORT}/health > /dev/null \
  && echo "OK llama-server :${LLAMA_PORT}" \
  || { echo "FAIL llama-server :${LLAMA_PORT} -- Abbruch"; exit 1; }
curl -s http://localhost:${EMBED_PORT}/health > /dev/null \
  && echo "OK Embedding :${EMBED_PORT}" \
  || { echo "FAIL Embedding :${EMBED_PORT} -- Abbruch"; exit 1; }

# Phoenix
echo "=== Phoenix :6006 ==="
if curl -s http://localhost:6006/healthz > /dev/null 2>&1; then
  echo "Bereits aktiv"
else
  nohup python3 -m phoenix.server.main serve \
    --host 127.0.0.1 \
    --port 6006 \
    > /tmp/logs/phoenix.log 2>&1 &
  pgrep -f "phoenix.server.main" > /tmp/pids/phoenix.pid
  echo "PID: $(cat /tmp/pids/phoenix.pid)"
  sleep 5
  curl -s http://localhost:6006/healthz > /dev/null \
    && echo "OK" \
    || echo "WARN: Timeout -- Log pruefen"
  tail -3 /tmp/logs/phoenix.log
fi

# LiteLLM
echo "=== LiteLLM :4000 ==="
if curl -s -H "Authorization: Bearer ${LITELLM_KEY}" \
    http://localhost:4000/health > /dev/null 2>&1; then
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
  pgrep -f "litellm" > /tmp/pids/litellm.pid
  echo "PID: $(cat /tmp/pids/litellm.pid)"
  echo "Warte 15s..."
  sleep 15
  curl -s -H "Authorization: Bearer ${LITELLM_KEY}" \
    http://localhost:4000/health > /dev/null \
    && echo "OK" \
    || echo "FAIL -- Log pruefen"
  tail -3 /tmp/logs/litellm.log
fi

# Agent Server
echo "=== Agent Server :8002 ==="
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
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
  cd ${LA_REPO} && \
  MCP_CONFIG_PATH=/tmp/mcp_hfspace.json \
  OPENAI_API_KEY=${LITELLM_KEY} \
  PYTHONPATH=${LA_REPO}/agents/server \
  nohup uvicorn server:app \
    --host 127.0.0.1 \
    --port 8002 \
    > /tmp/logs/agent-server.log 2>&1 &
  pgrep -f "uvicorn server:app" > /tmp/pids/agent-server.pid
  echo "PID: $(cat /tmp/pids/agent-server.pid)"
  sleep 10
  curl -s http://localhost:8002/health \
    && echo "Agent Server OK" \
    || echo "FAIL -- Log pruefen"
  tail -5 /tmp/logs/agent-server.log
fi

# Status
echo ""
echo "=== STATUS ==="
for port in 8090 8081 6006 4000 8002 7860; do
  curl -s http://localhost:${port}/health > /dev/null 2>&1 \
    || curl -s http://localhost:${port}/healthz > /dev/null 2>&1 \
    && echo "OK :${port}" \
    || echo "DOWN :${port}"
done
echo ""
echo "PIDs:"
ls /tmp/pids/*.pid 2>/dev/null | while read f; do
  echo "  $(basename $f): $(cat $f)"
done
