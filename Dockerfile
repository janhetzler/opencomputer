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

# Modell Stack 1 (Granite-Tiny) herunterladen
RUN mkdir -p /data/models && curl -L \
    "https://huggingface.co/unsloth/granite-4.0-h-tiny-GGUF/resolve/main/granite-4.0-h-tiny-UD-Q4_K_XL.gguf" \
    -o /data/models/granite-4.0-h-tiny-UD-Q4_K_XL.gguf

# LA Stack -- Repo klonen
RUN git clone https://github.com/janhetzler/la /home/la_build

# LA Stack -- virtualenv anlegen + requirements installieren
RUN python3 -m venv /home/varxdev/la_env && \
    /home/varxdev/la_env/bin/pip install --quiet \
    -r /home/la_build/requirements.txt

# LA Stack -- Modelle herunterladen (oeffentliche GitHub Releases)
RUN curl -L \
    "https://github.com/janhetzler/la/releases/download/granite-models/granite-4.0-h-350m-Q4_K_M.gguf" \
    -o /data/models/granite-350m-Q4_K_M.gguf

RUN curl -L \
    "https://github.com/janhetzler/la/releases/download/granite-models/granite-embedding-30m-english-Q4_0.gguf" \
    -o /data/models/granite-embedding-30m-Q4_0.gguf

# LA Stack -- Repo an finale Position + Verzeichnisse anlegen
RUN cp -r /home/la_build /home/varxdev/la && \
    mkdir -p /tmp/logs /tmp/chroma_la /tmp/traces

# Benutzer und Arbeitsverzeichnis einrichten
RUN useradd -m -u 1000 varxdev && \
    mkdir -p /home/varxdev/workspace && \
    chown -R varxdev:varxdev /home/varxdev /data

# Start-Skript fuer cptr + Llama + LA Stack
RUN cat > /usr/local/bin/start.sh <<'SH'
#!/bin/sh

# Stack 1: Llama-Server (Granite-Tiny) auf Port 8080
/opt/llama/llama-server \
  --model /data/models/granite-4.0-h-tiny-UD-Q4_K_XL.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --ctx-size 8192 \
  --threads 2 \
  --jinja \
  -ngl 0 &

# Stack 1: cptr auf Port 7860
cptr run --host 0.0.0.0 --port 7860 &

# Stack 2: LA Agent Stack starten
curl -sL "https://raw.githubusercontent.com/janhetzler/opencomputer/main/scripts/hfspace/start_hfspace.py" \
  -o /tmp/start_hfspace.py
. /home/varxdev/la_env/bin/activate && \
LA_REPO=/home/varxdev/la \
MODEL_PATH=/data/models/granite-350m-Q4_K_M.gguf \
EMBED_MODEL_PATH=/data/models/granite-embedding-30m-Q4_0.gguf \
LLAMA_SERVER_BIN=/opt/llama/llama-server \
python3 /tmp/start_hfspace.py &

wait
SH
RUN chmod +x /usr/local/bin/start.sh

USER varxdev
WORKDIR /home/varxdev/workspace

EXPOSE 7860 8080 8090 8081 4000 6006 8002
CMD ["/usr/local/bin/start.sh"]
