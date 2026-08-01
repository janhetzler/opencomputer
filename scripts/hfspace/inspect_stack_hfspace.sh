#!/bin/sh
# inspect_stack_hfspace.sh -- Stack-Diagnose fuer HF Space
# Aufruf: bash /home/varxdev/la/scripts/hfspace/inspect_stack_hfspace.sh

echo "=== PORTS ==="
nc -z localhost 8090 && echo "8090 llama-server (reasoning) OK" || echo "8090 llama-server (reasoning) TOT"
nc -z localhost 8081 && echo "8081 llama-server (embedding) OK" || echo "8081 llama-server (embedding) TOT"
nc -z localhost 4000 && echo "4000 litellm OK"                  || echo "4000 litellm TOT"
nc -z localhost 6006 && echo "6006 phoenix OK"                  || echo "6006 phoenix TOT"
nc -z localhost 8002 && echo "8002 agent-server OK"             || echo "8002 agent-server TOT"

echo ""
echo "=== PROZESSE ==="
ps aux | grep -E "llama-server|litellm|phoenix|uvicorn" | grep -v grep

echo ""
echo "=== LOG: llama-server-la.log (letzte 20 Zeilen) ==="
tail -20 /tmp/logs/llama-server-la.log 2>/dev/null || echo "(kein Log)"

echo ""
echo "=== LOG: llama-server-embed-la.log (letzte 10 Zeilen) ==="
tail -10 /tmp/logs/llama-server-embed-la.log 2>/dev/null || echo "(kein Log)"

echo ""
echo "=== LOG: litellm-la.log (letzte 30 Zeilen) ==="
tail -30 /tmp/logs/litellm-la.log 2>/dev/null || echo "(kein Log)"

echo ""
echo "=== LOG: phoenix-la.log (letzte 10 Zeilen) ==="
tail -10 /tmp/logs/phoenix-la.log 2>/dev/null || echo "(kein Log)"

echo ""
echo "=== HEALTH CHECK: Agent Server ==="
curl -s http://localhost:8002/health 2>/dev/null || echo "Agent Server nicht erreichbar"

echo ""
echo "=== HEALTH CHECK: LiteLLM ==="
curl -s http://localhost:4000/health   -H "Authorization: Bearer sk-cos-local-dev" 2>/dev/null || echo "LiteLLM nicht erreichbar"
