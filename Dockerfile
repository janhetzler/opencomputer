FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    curl python3 python3-pip libmagic1 git git-lfs wget unzip \
    software-properties-common npm \
    python3.11 python3.11-venv && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    rm -rf /var/lib/apt/lists/*

# cptr (Open WebUI Computer) installieren
RUN pip3 install --no-cache-dir 'cptr[all]'

# Llama-Engine installieren
RUN curl -L https://github.com/ggml-org/llama.cpp/releases/download/b9895/llama-b9895-bin-ubuntu-x64.tar.gz \
    -o /tmp/llama.tar.gz && mkdir -p /opt/llama && \
    tar -xzf /tmp/llama.tar.gz -C /opt/llama --strip-components=1 && \
    chmod +x /opt/llama/llama-server && rm /tmp/llama.tar.gz

# Modell (granite-4.0-h-tiny-UD-Q4_K_XL.gguf) herunterladen
RUN mkdir -p /data/models && curl -L \
    "https://huggingface.co/unsloth/granite-4.0-h-tiny-GGUF/resolve/main/granite-4.0-h-tiny-UD-Q4_K_XL.gguf" \
    -o /data/models/granite-4.0-h-tiny-UD-Q4_K_XL.gguf

# Benutzer und Arbeitsverzeichnis einrichten
RUN useradd -m -u 1000 varxdev && \
    mkdir -p /home/varxdev/workspace && \
    chown -R varxdev:varxdev /home/varxdev /data

# Start-Skript fuer cptr + Llama
RUN cat > /usr/local/bin/start.sh <<'SH'
#!/bin/sh

# Llama-Server intern auf Port 8080 mit 2 Threads und --jinja Flag starten
/opt/llama/llama-server \
  --model /data/models/granite-4.0-h-tiny-UD-Q4_K_XL.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --ctx-size 8192 \
  --threads 2 \
  --jinja \
  -ngl 0 &

# cptr auf Port 7860 fuer HF Spaces starten
cptr run --host 0.0.0.0 --port 7860 &

wait
SH
RUN chmod +x /usr/local/bin/start.sh

USER varxdev
WORKDIR /home/varxdev/workspace

EXPOSE 7860 8080
CMD ["/usr/local/bin/start.sh"]
