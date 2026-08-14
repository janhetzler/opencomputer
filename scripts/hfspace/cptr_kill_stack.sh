#!/bin/sh
# cptr_kill_stack.sh -- LA Stack sauber stoppen
#
# Stoppt Phoenix, LiteLLM und Agent Server.
# Erst SIGTERM, dann SIGKILL -- bewaehrte Methode (BUG-007).
#
# Verwendung:
#   sh scripts/hfspace/cptr_kill_stack.sh
#
# Hinweis: pkill -f wird verwendet statt PID-Dateien --
# kill via PID hat sich heute als unzuverlaessig erwiesen.

echo "=== Stoppe LA Stack ==="
echo "Schritt 1: SIGTERM..."
pkill -TERM -f "phoenix.server.main" 2>/dev/null \
  && echo "  Phoenix TERM gesendet" \
  || echo "  Phoenix nicht gefunden"
pkill -TERM -f "litellm" 2>/dev/null \
  && echo "  LiteLLM TERM gesendet" \
  || echo "  LiteLLM nicht gefunden"
pkill -TERM -f "uvicorn server:app" 2>/dev/null \
  && echo "  Agent Server TERM gesendet" \
  || echo "  Agent Server nicht gefunden"

echo ""
echo "Warte 3s..."
sleep 3

echo ""
echo "Schritt 2: SIGKILL (falls noch aktiv)..."
pkill -KILL -f "phoenix.server.main" 2>/dev/null
pkill -KILL -f "litellm" 2>/dev/null
pkill -KILL -f "uvicorn server:app" 2>/dev/null
sleep 2

echo ""
echo "PID-Dateien aufraaeumen..."
rm -f /tmp/pids/phoenix.pid \
      /tmp/pids/litellm.pid \
      /tmp/pids/agent-server.pid

echo ""
echo "=== Verifikation ==="
for port in 6006 4000 8002; do
  curl -s http://localhost:${port}/health \
    > /dev/null 2>&1 \
    && echo "WARN :${port} noch aktiv" \
    || echo "OK   :${port} gestoppt"
done

echo ""
pgrep -a -f "phoenix|litellm|uvicorn" \
  || echo "Alle LA Prozesse gestoppt"
