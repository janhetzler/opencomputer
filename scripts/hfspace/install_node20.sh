#!/bin/sh
# install_node20.sh -- Node.js 20 ohne Root via nodeenv installieren
#
# Benoetigt: pip, nodeenv bereits installiert (in la_env)
# Output: Node 20 unter /tmp/node20/bin/node
# PATH muss manuell erweitert werden:
#   export PATH=/tmp/node20/bin:$PATH
#
# Hintergrund: Docker Container laeuft als varxdev (kein sudo).
# Ubuntu 22.04 hat nur Node 12 -- zu alt fuer mcp-server-fetch
# (readabilipy braucht Node 18+ fuer ExtractArticle.js).
# Siehe BUG-008 in BUGS.md.
#
# Verwendung:
#   . /home/varxdev/la_env/bin/activate
#   sh scripts/hfspace/install_node20.sh
#   export PATH=/tmp/node20/bin:$PATH

echo "=== Node.js 20 Installation via nodeenv ==="
echo ""

# 1. Aktuelle Version pruefen
echo "=== Aktuell installiert ==="
node --version 2>/dev/null \
  && echo "node: $(node --version)" \
  || echo "node: nicht gefunden"
echo ""

# 2. Bereits installiert?
if [ -f /tmp/node20/bin/node ]; then
  echo "Node 20 bereits unter /tmp/node20 -- pruefe Version..."
  /tmp/node20/bin/node --version
  echo "Nichts zu tun. PATH erweitern mit:"
  echo "  export PATH=/tmp/node20/bin:\$PATH"
  exit 0
fi

# 3. nodeenv pruefen
echo "=== nodeenv pruefen ==="
python3 -m nodeenv --version 2>/dev/null \
  && echo "nodeenv: OK" \
  || { echo "FAIL: nodeenv nicht gefunden"
       echo "Installieren: pip install nodeenv"
       exit 1; }
echo ""

# 4. Node 20 installieren
echo "=== Installiere Node 20.19.0 ==="
echo "Das dauert ca. 1-2 Minuten..."
nodeenv --node=20.19.0 /tmp/node20 2>&1 | tail -3
echo ""

# 5. Verifikation
echo "=== Verifikation ==="
/tmp/node20/bin/node --version \
  && echo "Node 20 OK" \
  || { echo "FAIL: Installation fehlgeschlagen"
       exit 1; }
/tmp/node20/bin/npm --version \
  && echo "npm OK" \
  || echo "WARN: npm nicht gefunden"
echo ""

# 6. Test ExtractArticle.js
echo "=== ExtractArticle.js Test ==="
EXTRACT=$(find /home/varxdev/la_env -name "ExtractArticle.js" 2>/dev/null | head -1)
if [ -n "$EXTRACT" ]; then
  echo "Gefunden: $EXTRACT"
  PATH=/tmp/node20/bin:$PATH \
  node "$EXTRACT" --version 2>/dev/null \
    && echo "ExtractArticle.js OK" \
    || echo "WARN: ExtractArticle.js Test fehlgeschlagen"
else
  echo "WARN: ExtractArticle.js nicht gefunden"
fi
echo ""

echo "=== Fertig ==="
echo "PATH erweitern mit:"
echo "  export PATH=/tmp/node20/bin:\$PATH"
echo ""
echo "Dann Agent Server neu starten mit:"
echo "  sh /tmp/la_stack.sh stop"
echo "  PATH=/tmp/node20/bin:\$PATH sh /tmp/la_stack.sh start"
