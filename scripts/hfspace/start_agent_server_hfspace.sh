#!/bin/sh
# start_agent_server_hfspace.sh -- Agent Server starten und verifizieren
# Aufruf: curl -sL "https://raw.githubusercontent.com/janhetzler/opencomputer/main/scripts/hfspace/start_agent_server_hfspace.sh" | bash

cd /home/varxdev/la
. /home/varxdev/la_env/bin/activate

echo "=== PORT CHECK VOR START ==="
nc -z localhost 8002 && kill $(lsof -t -i:8002) 2>/dev/null && sleep 1 || true

echo "=== SERVER START ==="
PYTHONPATH=/home/varxdev/la/agents/server \
uvicorn server:app --host 0.0.0.0 --port 8002 > /tmp/logs/agent-server-la.log 2>&1 &
sleep 3

echo "=== PORT CHECK NACH START ==="
nc -z localhost 8002 && echo "8002 agent-server OK" || echo "8002 agent-server TOT"

echo "=== LOG ==="
cat /tmp/logs/agent-server-la.log
