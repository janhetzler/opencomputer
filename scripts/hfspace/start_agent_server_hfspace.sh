#!/bin/sh
# start_agent_server_hfspace.sh -- Agent Server starten und verifizieren
# Aufruf: bash /home/varxdev/la/scripts/hfspace/start_agent_server_hfspace.sh
# Oder:   curl -sL "https://raw.githubusercontent.com/janhetzler/opencomputer/main/scripts/hfspace/start_agent_server_hfspace.sh" | bash

cd /home/varxdev/la
. /home/varxdev/la_env/bin/activate

echo "=== SERVER START ==="
python3 agents/server/server.py > /tmp/logs/agent-server-la.log 2>&1 &
sleep 3

echo "=== PORT CHECK ==="
nc -z localhost 8002 && echo "8002 agent-server OK" || echo "8002 agent-server TOT"

echo "=== LOG ==="
cat /tmp/logs/agent-server-la.log
