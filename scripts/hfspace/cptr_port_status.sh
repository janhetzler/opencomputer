#!/bin/sh
# cptr_port_status.sh -- Status aller LA Stack Ports pruefen
#
# Zeigt welche Ports aktiv oder frei sind.
# Zeigt PID-Dateien und laufende Prozesse.
#
# Verwendung:
#   sh scripts/hfspace/cptr_port_status.sh

echo "=== Port Status ==="
for port in 7860 8080 8090 8081 6006 4000 8002; do
  curl -s --max-time 2 http://localhost:${port}/health \
    > /dev/null 2>&1 \
    || curl -s --max-time 2 http://localhost:${port}/healthz \
    > /dev/null 2>&1 \
    && echo "AKTIV :${port}" \
    || echo "FREI  :${port}"
done

echo ""
echo "=== PID Dateien ==="
ls /tmp/pids/*.pid 2>/dev/null \
  | while read f; do
      echo "  $(basename $f): $(cat $f)"
    done \
  || echo "  Keine PID-Dateien"

echo ""
echo "=== Laufende LA Prozesse ==="
pgrep -a -f "phoenix|litellm|uvicorn|llama-server" \
  || echo "  Keine gefunden"
