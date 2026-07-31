FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    curl python3 python3-pip libmagic1 git git-lfs wget unzip \
    software-properties-common npm tini \
    python3.11 python3.11-venv && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    rm -rf /var/lib/apt/lists/*

# cptr zuerst -- zieht viele Abhaengigkeiten mit die LA Stack benoetigt
RUN pip3 install --no-cache-dir 'cptr[all]'

# Llama-Engine installieren
RUN curl -L https://github.com/ggml-org/llama.cpp/releases/download/b9895/llama-b9895-bin-ubuntu-x64.tar.gz \
    -o /tmp/llama.tar.gz && mkdir -p /opt/llama && \
    tar -xzf /tmp/llama.tar.gz -C /opt/llama --strip-components=1 && \
    chmod +x /opt/llama/llama-server && rm /tmp/llama.tar.gz

# Modelle Stack 1 (Granite-Tiny) + Stack 2 (350m + Embedding)
RUN mkdir -p /data/models && curl -L \
    "https://huggingface.co/unsloth/granite-4.0-h-tiny-GGUF/resolve/main/granite-4.0-h-tiny-UD-Q4_K_XL.gguf" \
    -o /data/models/granite-4.0-h-tiny-UD-Q4_K_XL.gguf

RUN curl -L \
    "https://github.com/janhetzler/la/releases/download/granite-models/granite-4.0-h-350m-Q4_K_M.gguf" \
    -o /data/models/granite-350m-Q4_K_M.gguf

RUN curl -L \
    "https://github.com/janhetzler/la/releases/download/granite-models/granite-embedding-30m-english-Q4_0.gguf" \
    -o /data/models/granite-embedding-30m-Q4_0.gguf

# Benutzer anlegen
RUN useradd -m -u 1000 varxdev && \
    mkdir -p /home/varxdev/workspace

# LA Stack -- Repo klonen + requirements nach cptr installieren
RUN git clone https://github.com/janhetzler/la /home/la_build

RUN python3 -m venv /home/varxdev/la_env && \
    /home/varxdev/la_env/bin/pip install --quiet \
    -r /home/la_build/requirements.txt

# LA Repo + Verzeichnisse
RUN cp -r /home/la_build /home/varxdev/la && \
    mkdir -p /tmp/logs /tmp/chroma_la /tmp/traces

# Berechtigungen
RUN chown -R varxdev:varxdev /home/varxdev /data /tmp/logs /tmp/chroma_la /tmp/traces

USER varxdev
WORKDIR /home/varxdev/workspace

RUN cat > /home/varxdev/start.sh <<'SH'
#!/bin/sh

# Stack 1: cptr zuerst
cptr run --host 0.0.0.0 --port 7860 &

# Stack 2: LA Agent Stack
curl -sL "https://raw.githubusercontent.com/janhetzler/opencomputer/main/scripts/hfspace/start_hfspace.py" \
  -o /tmp/start_hfspace.py
. /home/varxdev/la_env/bin/activate && \
LA_REPO=/home/varxdev/la \
MODEL_PATH=/data/models/granite-350m-Q4_K_M.gguf \
EMBED_MODEL_PATH=/data/models/granite-embedding-30m-Q4_0.gguf \
LLAMA_SERVER_BIN=/opt/llama/llama-server \
python3 /tmp/start_hfspace.py &

# Stack 1: Granite-Tiny zuletzt -- nach LA Stack
/opt/llama/llama-server \
  --model /data/models/granite-4.0-h-tiny-UD-Q4_K_XL.gguf \
  --host 127.0.0.1 --port 8080 \
  --ctx-size 8192 --threads 2 --jinja -ngl 0 &

wait
SH
RUN chmod +x /home/varxdev/start.sh

EXPOSE 7860 8080 8090 8081 4000 6006 8002
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/home/varxdev/start.sh"]
