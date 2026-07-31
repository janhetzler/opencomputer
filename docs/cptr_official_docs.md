# Use your coding agent subscription

Already paying for Codex, Claude Code, Cursor, Grok, OpenCode, Cline, or Pi? Use that subscription as a native chat backend; no API key is needed. Install and log in to the agent's CLI on the machine running Computer, then go to **Settings ��� Admin ��� Agents** and add a profile. Its models appear in the model selector like any other provider, with ids like `agent:<profile-id>/<model>`.

A profile has: **Name**, **Type** (which agent), **Profile ID** (slug used in model ids), **Command** (name or absolute path; `~` works), and optional **Home** (see below). Some types add fields: Claude Code has **Launch args**, Cursor has an **API endpoint**, OpenCode has **Server URL** and password.

## Per-agent setup

The CLI must be installed **and logged in on the host running Computer**, not on the phone or laptop you browse from.

### Codex

Command: `codex`. Sign in with `codex login`. Needs a recent CLI with app-server support; if detection reports an unsupported capability, update the CLI.

### Claude Code

Command: `claude`. Sign in with the CLI's normal login flow. Also requires the Python package `claude-agent-sdk` in the environment Computer runs in; without it the profile shows **missing dependency**:

```
pip install claude-agent-sdk
```

The available model list depends on the installed CLI version.

### Cursor

Command: `agent`. Run `agent login` on the host.

### Grok

Command: `grok`. Log in with the CLI, or set the `XAI_API_KEY` environment variable.

### OpenCode

Command: `opencode`. Computer spawns `opencode serve` automatically, or set **Server URL** (and password) in the profile to connect to a server you already run. Models come from the providers connected in OpenCode.

### Cline

Command: `cline`. Run `cline auth` on the host.

### Pi

Command: `pi`. Models are namespaced `provider/id`.

## Detection statuses

Each profile shows a live status (results cached for ~30 seconds):
 | Status | Meaning | Fix
 | **ready** | Command found, dependencies present, models discoverable | Nothing; pick a model and chat
 | **not found** | Command isn't on `PATH` | Install the CLI, or set Command to the absolute path
 | **missing dependency** | A required local package is absent (Claude Code: `claude-agent-sdk`) | Install the named dependency in Computer's environment
 | **auth unknown** | CLI found but login state couldn't be confirmed | Run the agent's login on the host, then re-detect

Profile mode: **auto** (selectable only when ready), **enabled** (force), or **disabled**.

## Models, sessions, and the Home field

- **Models:** leave the profile's model list empty to auto-detect from the CLI, or pin a manual list. Model ids look like `agent:claude/claude-sonnet-4-5`.
- **Sessions resume automatically.** Each backend returns a session or thread id that is stored on the chat and passed back next turn (Claude Code SDK session, Codex thread resume, Cursor/Grok/Cline session load). Close the tab, open the chat on your phone, and the agent continues where it left off.
- **Home:** point the profile at an alternate agent config/login directory. This is useful for a second account or an isolated login kept apart from your default `~` config.

## Any other agent still works

Gemini CLI, Kilo Code, or any other terminal agent runs fine in a [terminal tab]; it just isn't a native chat backend with model selection and session resume.

---

# Connect a model (API keys and Ollama)

Go to **Settings ��� Admin ��� Connections** and add a connection. There are exactly two provider types: **OpenAI** and **Anthropic**. There is no separate "Ollama" or "OpenAI-compatible" type: anything that speaks the OpenAI API (Ollama, OpenRouter, vLLM, LM Studio, Groq, ...) is added as provider **OpenAI** with a custom Base URL.

## Connection fields

 | Field | What it does
 | **Name** | Optional display name for the connection
 | **Provider** | `OpenAI` or `Anthropic`
 | **API Type** | OpenAI only: Chat Completions or Responses
 | **Base URL** | Required. E.g. `https://api.openai.com/v1`, `http://localhost:11434/v1`
 | **API Key** | Required. Ollama ignores the value, but the field must be non-empty
 | **Prefix ID** | Optional namespace prepended to model ids, e.g. `openrouter/gpt-4o`
 | **Models** | Optional comma-separated list. Leave empty to auto-discover

## Ollama

- **Provider:** OpenAI
- **Base URL:**`http://localhost:11434/v1`
- **API Key:** any text (`ollama` works); Ollama doesn't check it, but the field can't be empty

Your pulled models are auto-discovered and appear in the model selector.

## OpenRouter

- **Provider:** OpenAI
- **Base URL:**`https://openrouter.ai/api/v1`
- **API Key:** your OpenRouter key

OpenRouter exposes many models; set a **Prefix ID** like `openrouter` so its models are namespaced (`openrouter/gpt-4o`) and don't collide with models from other connections.

## Anthropic

- **Provider:** Anthropic
- **Base URL:**`https://api.anthropic.com/v1`
- **API Key:** your Anthropic key

## Model discovery, defaults, enabling

- **Auto-discovery:** with the Models field empty, Computer queries the provider's `/models` endpoint and lists everything it returns.
- **Manual list:** enter a comma-separated list in the Models field to expose only those models. This is useful for providers with huge catalogs or endpoints without a `/models` route.
- **Enable/disable:** individual models can be toggled on or off, so the selector only shows what you actually use.
- **Default model:** set the default for new chats in settings (config key `chat.default_model`).

Prefer a subscription over an API key? See [Use your coding agent subscription].

---

# Message your computer

Connect a bot and your computer answers in Telegram, Discord, Slack, WhatsApp, or Signal: same agent, same workspaces, full tool access. Ask it to check a build, push a fix, or summarize a file, from any phone with the chat app installed. No tunnel or public URL needed for Telegram, Discord, Slack, or Signal.

## Set up any bot

- Open **Settings ��� Admin ��� Bots** and create a bot.
- Choose the platform and paste the credential (per-platform instructions below). Tokens are stored encrypted.
- Click **Verify** to confirm the credential works.
- Pick the workspace and model the bot starts in.
- Set **Allowed senders**: a list of platform user IDs that get replies.
- Start the bot and message it.Set Allowed senders

An empty Allowed senders list means anyone who finds the bot can use it, and a bot message runs the agent with full tool approval on your machine. Add your own platform user ID before starting the bot, and keep the bot out of group channels.

## Commands

Work on every platform:
 | Command | What it does
 | `/new` (also `/reset`) | Start a fresh chat
 | `/stop` | Cancel the running task
 | `/retry` | Re-run your last message
 | `/model [id]` | Show or switch the model (persists)
 | `/workspaces` | List available workspaces
 | `/workspace <name>` | Switch workspace (fuzzy match) and start a new chat
 | `/help` | List commands

## What to expect

- **Streaming**: the bot edits its message roughly every 2 seconds with progress: tool activity lines plus the text so far. The final answer arrives as persistent messages, chunked to the platform's length limit. (WhatsApp and Signal don't support edits; you get the final answer only.)
- **Attachments in**: images and documents you send are attached to the chat.
- **Voice notes**: transcribed and answered when speech-to-text is configured; see [voice and audio]. Otherwise the bot tells you STT isn't set up.
- **Queueing**: messages sent while a task is running are queued and processed in order.
- **Synced**: every bot conversation is a real chat in the selected workspace; it appears in the Computer sidebar, and you can pick it up in the web UI.

## Telegram

- Message [@BotFather] on Telegram, send `/newbot`, and copy the token it gives you.
- Paste the token as the credential, verify, and start.

Telegram uses long-polling, so your Computer needs no public URL. Your sender ID is your numeric Telegram user ID; get it from a bot like @userinfobot. On Bot API 10.1+ you get rich draft streaming; older versions fall back to plain messages in 4096-character chunks.

## Discord

- In the [Discord Developer Portal], create an application, open **Bot**, and copy the token.
- On the same Bot page, enable the **Message Content** intent.
- Invite the bot to your server (OAuth2 URL generator with the `bot` scope).
- Paste the token as the credential.

Discord connects over the Gateway WebSocket, so no public URL is needed. It requires the `websockets` Python package, which is not installed by default:

```
pip install websockets
```

Messages are chunked to 2000 characters.

## Slack

- Create a Slack app and install it to your workspace to get a bot token (`xoxb-...`).
- Enable **Socket Mode**, which gives you an app-level token (`xapp-...`).
- Enter both, pipe-separated, as the credential:

```
xoxb-your-bot-token|xapp-your-app-token
```

Socket Mode means no public URL. Like Discord, Slack needs `pip install websockets` on the host. Messages are chunked to 4000 characters.

## WhatsApp

Uses the Meta Cloud API. From your Meta app, get the access token and the phone number ID, and enter them pipe-separated:

```
access_token|phone_number_id
```

Inbound messages arrive by webhook only, so your Computer must be publicly reachable (see [security] before exposing it). Configure the webhook URL in the Meta app as:

```
https://<your-host>/api/webhooks/whatsapp/<bot_id>
```

Webhook verification currently accepts any verify token. WhatsApp doesn't support message edits, so there's no streaming; you get the final answer.

## Signal

Requires a signal-cli REST API bridge running next to Computer:

```
docker run -p 8080:8080 bbernhard/signal-cli-rest-api
```

Register your Signal number with the bridge, then enter the bridge URL and number pipe-separated as the credential:

```
http://localhost:8080|+15551234567
```

The bot polls the bridge every 2 seconds. No message edits, so no streaming.

---

# Scheduled tasks

Run a prompt on a schedule: "run the tests every weekday at 9", "summarize new files every Monday", "check the deploy hourly". Each run is a real chat in the workspace you choose, so you can read exactly what happened.

## Create a task

The fastest way is to ask. In any chat, in the workspace where the work should happen:

Schedule a task that runs the test suite every weekday at 9 and reports failures with the error output.

The agent has a tool for this; approve the tool call and the task exists, workspace and model already set from the chat. Then open the **Scheduled** page to check the next-run time and click **Run now** once before trusting the schedule.

The Scheduled page is also where you create and manage tasks by hand: name, prompt, model, workspace, and a schedule from the frequency builder (hourly, daily, weekly, ...) or a raw RRULE. Schedules are iCalendar RRULEs; the raw field takes anything RRULE supports:
 | Schedule | RRULE
 | Every day at 09:00 | `RRULE:FREQ=DAILY;BYHOUR=9;BYMINUTE=0`
 | Every Monday | `RRULE:FREQ=WEEKLY;BYDAY=MO`
 | Every hour | `RRULE:FREQ=HOURLY;INTERVAL=1`
 | Once, then never again | `RRULE:FREQ=DAILY;COUNT=1`Runs are unattended

Scheduled runs execute with full tool approval: nobody is there to click Allow. Give the task a workspace you're comfortable with and a prompt that says exactly what to do (and what not to).

## What a run produces

Every run creates:
- a **real chat** in the selected workspace, visible in the sidebar with the full task activity, and
- a **run-history entry** on the task showing success or error (with the error text).

Want a ping? Add a notification target once, then just put the condition in the task's prompt ("notify me only if it fails"): the agent has a notify tool and decides when to use it. Blanket event pings on every finished/failed run exist too. See [notifications and webhooks].

## Trigger a task with a webhook

Any scheduled task can also be started from outside (CI, a cron job, another service) without a browser session:
- On the task, generate its webhook URL. It contains a secret token.
- `POST` to that URL to run the task immediately.
- Revoke or regenerate the URL anytime if it leaks.

If the POST has a JSON body, the prompt can use it via the `{{webhook_payload}}` placeholder, so a CI failure payload, form submission, or alert can flow straight into the task's instructions.

## A good first task

Name: `Morning test check`. Schedule: `RRULE:FREQ=DAILY;BYHOUR=9;BYMINUTE=0`. Prompt:

```
Run the test suite in this workspace. Don't change any files.
Report pass or fail; if it failed, include the failing test and error output.
```

Click **Run now**, read the chat it creates, and leave it enabled once the output is something you can judge in a few seconds.

---

# Use a workspace from Open WebUI

Computer's gateway exposes each workspace as an OpenAI-compatible model, so you can select `cptr/<workspace>` in Open WebUI's model picker and chat with a real machine (files, terminal, git, tools) from the Open WebUI interface you already use.

## Connect it

- 

In Computer, open **Settings ��� Admin ��� Gateway** and create a gateway API key. Copy it immediately; it's shown once and stored hashed.
- 

In Open WebUI, go to **Admin Settings ��� Connections** and add an **OpenAI API** connection:
- Base URL: `http(s)://<computer-host>/v1`
- API key: the `sk-cptr-...` key from step 1
- 

Add these custom headers to the connection so Computer can track chat lineage and filter Open WebUI's utility requests:

```
{
  "X-OpenWebUI-Chat-Id": "{{CHAT_ID}}",
  "X-OpenWebUI-Message-Id": "{{MESSAGE_ID}}",
  "X-OpenWebUI-User-Message-Id": "{{USER_MESSAGE_ID}}",
  "X-OpenWebUI-User-Message-Parent-Id": "{{USER_MESSAGE_PARENT_ID}}",
  "X-OpenWebUI-Task": "{{TASK}}"
}
```

`{{USER_MESSAGE_ID}}`, `{{USER_MESSAGE_PARENT_ID}}`, and `{{TASK}}` require Open WebUI 0.10.0 or newer. Without them, basic chat works, but edit/regeneration branches and background-task filtering do not.
- 

Save. Each of your Computer workspaces now appears in Open WebUI's model picker as `cptr/<workspace-name>`. Pick one and chat.

Which underlying model actually runs is decided in Computer, in priority order: the Settings ��� Gateway model, a `<workspace>/.cptr/model` override file, the default chat model, then the first enabled connection's first model.Gateway requests are unattended

Gateway tasks run the full agent loop (file edits, shell commands, web, tools) with full tool approval. Open WebUI can't pause for a per-action confirmation. Use it with workspaces you're comfortable letting an agent act in, and keep the key private.

## What the headers buy you

- **Conversation continuity**: follow-up messages land in the same Computer chat instead of creating a new one.
- **Branch mirroring**: edits and regenerations in Open WebUI show up as branches of the right chat in Computer.
- **Utility-task filtering**: Open WebUI's title, tag, and follow-up-suggestion requests are answered by the plain LLM instead of spinning up an agent task in your workspace.

Every gateway conversation is a real chat in the Computer sidebar, so you can open Computer and see exactly what the agent did.

## What does not carry over

The gateway is a model endpoint, not a sync. Open WebUI knowledge bases, tools, prompts, system prompts, and users are not forwarded into Computer; configure equivalent capabilities in Computer if the workspace needs them.

## If it doesn't work

Call `GET /v1/models` with the same bearer key to separate connectivity/auth problems from model selection. Check the base URL ends in `/v1`, the key belongs to the right Computer user, and the workspace exists. If chat works but branching doesn't, recopy the headers and check your Open WebUI version.

For the raw endpoint details (`/v1/models`, `/v1/chat/completions`, streaming, header reference), see the [gateway API reference].

---

# Docker

Run Open WebUI Computer from the official image:

```
docker run --rm -it \
  -p 8000:8000 \
  -v cptr-data:/data \
  -v "$PWD:/workspace" \
  -w /workspace \
  ghcr.io/open-webui/computer:latest
```

Then open the URL printed in the logs, usually `http://localhost:8000/?token=...`. The token works once, while no user exists, and creates your admin account.
- `-v cptr-data:/data`: app state (database, config, uploads) in a named volume. Keep this mount or you lose your account and settings on every restart.
- `-v "$PWD:/workspace"`: mounts your current project into the container so Open WebUI Computer can work on it.

## docker-compose.yaml

For a host that should keep running:

```
services:
  cptr:
    image: ghcr.io/open-webui/computer:latest
    container_name: cptr
    ports:
      - "8000:8000"
    volumes:
      - cptr-data:/data
      - ~/projects:/projects
      # Mount as many directories as you like; each mounted
      # path can be added as a workspace in the UI:
      # - ~/notes:/notes
      # - /srv/sites:/sites
    restart: unless-stopped

volumes:
  cptr-data:
```

```
docker compose up -d
docker compose logs cptr
```

The first-run setup URL with its token is in the logs (`docker logs cptr` works too). Inside the app, add `/projects` (or any other mounted path) as a workspace.

## How the image works

The container runs `cptr run --host 0.0.0.0 --headless` and sets `CPTR_DATA_DIR=/data`, so it listens on all container interfaces, never tries to open a browser, and keeps everything stateful (SQLite database, `config.toml`, uploads, logs) under `/data`. The image includes all optional feature groups, so no extras are needed.

The `:dev` tag tracks the `main` branch if you want the latest changes; pin `:latest` or a release tag for stability.Bind-mounting `/data`

If you bind-mount a host directory to `/data` instead of using a named volume, that directory must be writable by the container user: SQLite has to create and update `/data/app.db`, and host directory permissions override the image's built-in `/data` ownership. A named volume avoids the problem entirely.

## Upgrading

Pull the new image and recreate the container with the same `/data` volume:

```
docker compose pull
docker compose up -d
```

Or for plain `docker run`: stop the container, `docker pull ghcr.io/open-webui/computer:latest`, then start it again with the same `-v cptr-data:/data` flag. Database migrations run automatically at startup; no manual step is needed. Back up the volume first for major upgrades: see [data and backups].

---

# Data and backups

Everything Computer needs to survive a reinstall lives in one data directory: `~/.cptr` by default, `/data` in Docker, or wherever `CPTR_DATA_DIR` points. The one exception is chats: they live inside each workspace folder and travel with the project.

## What lives where

Inside the data directory:
 | Path | What it holds
 | `app.db` | SQLite database in WAL mode (`app.db-wal` and `app.db-shm` sit next to it). Users and auth, instance config, automations, chat/message records, upload metadata.
 | `config.toml` | The server secret plus a mirror of app config. On startup the file is re-seeded into the database (**the file wins**), so it's safe to hand-edit while stopped, and config survives a lost database. See [config.toml].
 | `uploads/` | Uploaded file blobs.
 | `logs/` | Audit and upstream-request logs, when enabled.
 | `memory/` | Per-user AI memory.
 | `skills/` | Managed global skills.

Inside each workspace, Computer keeps a `.cptr/` folder:
 | Path | What it holds
 | `<workspace>/.cptr/chats/<chat_id>.json` | Every chat for that workspace; move the folder and the chats come with it.
 | `<workspace>/.cptr/artifacts/` | Artifacts produced in that workspace.
 | `<workspace>/.cptr/task_logs/` | Logs from task runs.

A data-directory backup does **not** include your workspaces. Project folders need their own backup (git remote, Time Machine, whatever you already use), and because chats live in `<workspace>/.cptr/`, that backup covers them too.

## Back up the data directory

Stop the server first

`app.db` uses SQLite WAL mode. Copying it while the server is writing can produce a corrupt or inconsistent backup. Stop Computer, copy, then start it again.

For a Python install, archive `~/.cptr`:

```
tar -C "$HOME" -czf cptr-data-backup.tgz .cptr
```

For Docker, archive the stopped `cptr-data` volume into the current directory:

```
docker run --rm \
  -v cptr-data:/data:ro \
  -v "$PWD:/backup" \
  alpine tar -C /data -czf /backup/cptr-data-backup.tgz .
```

Confirm the archive contains the two files that matter most:

```
tar -tzf cptr-data-backup.tgz | grep -E '(^|/)app\.db$|(^|/)config\.toml$'
```

## Test a restore

Don't wait for a disaster to find out the backup works. Unpack into a fresh directory and start a second instance on another port with `CPTR_DATA_DIR` pointing at it:

```
mkdir -p /tmp/cptr-restore
tar -C /tmp/cptr-restore -xzf cptr-data-backup.tgz
CPTR_DATA_DIR=/tmp/cptr-restore/.cptr cptr run --port 8001
```

Sign in at `http://localhost:8001` and check that your account and settings are there.

For Docker, restore into a **new** volume rather than overwriting production:

```
docker volume create cptr-data-restore
docker run --rm \
  -v cptr-data-restore:/data \
  -v "$PWD:/backup:ro" \
  alpine tar -C /data -xzf /backup/cptr-data-backup.tgz
```

Then start a test container with `-v cptr-data-restore:/data` and sign in. Remember that workspaces are restored separately: the data backup gets you accounts, config, and settings, not project files.

---

# Reference

Exact flags, variables, config keys, and API behavior, for when you know what you're looking for.
 | Need | Page
 | `cptr run` flags, install extras, what the CLI doesn't have | [CLI]
 | Every environment variable with defaults | [Environment variables]
 | Server secret, auth modes, the config file format | [config.toml]
 | OpenAI-compatible endpoints, keys, headers, limits | [Gateway API]

---

# Troubleshooting

Find your symptom below (Ctrl+F works). First check for anything odd: `curl http://127.0.0.1:8000/api/health` tells you whether the server is up at all.

## "cptr: command not found"

The package landed in a different Python environment than the one on your PATH. Install it into the Python you actually run:

```
python -m pip install cptr
```

If you installed with pipx or inside a virtualenv, activate that environment first (or use `pipx run cptr run` / `uvx cptr@latest run`). Then start it with `cptr run`.

## "Port 8000 already in use"

Something else owns the port. Either run on another one:

```
cptr run --port 8001
```

or find and stop the owner: `lsof -i :8000` (macOS/Linux) or `netstat -ano | findstr :8000` (Windows).

## The setup URL doesn't work / I lost the setup token

The setup token is printed once when `cptr run` starts, and the setup URL only works while **no account exists yet**. If you lost it, just restart `cptr run`: a fresh token is printed. If an account already exists, the setup URL is dead by design; go to `http://localhost:8000` and log in normally.

## I forgot my password / I'm locked out

If another admin exists, they can reset your password in **Settings ��� Admin ��� Users**. Two things that trip people up first:
- Login is rate-limited to **5 attempts per minute per IP**. If you're getting `429`, wait a minute and try again.
- Rotating `[server] secret` in `config.toml` signs out every session; it does **not** reset any password.

If you're the sole admin, stop the server. There is no CLI password reset. Your options, in order:
- Restore a backup of `app.db` from when the password still worked.
- Last resort: open `app.db` with a SQLite client and delete the user rows (the account and auth tables), then restart. First-run setup triggers again and you create a new admin. Your config (`config.toml`) and workspace chats (`<workspace>/.cptr/chats/`) survive; only the accounts are recreated.

## My phone can't reach it

`localhost` on your phone means the phone itself. It will never reach your computer.
- **Same Wi-Fi:** restart with `cptr run --host 0.0.0.0`, open `http://<your-computer-ip>:8000` on the phone, and allow the port through the host firewall.
- **Away from home:** you need Tailscale or a tunnel; see [phone and remote access].
- **Host asleep:** nothing can serve a sleeping machine; see [keep it running].

## Terminal won't open on Windows (VCRUNTIME140.dll)

The terminal backend needs the Microsoft Visual C++ Redistributable. Install the x64 version from Microsoft, restart your machine, and start `cptr run` again.

## Docker: setup wizard reappeared / my state is gone

The container started without its `/data` volume, so it looks like a fresh install. Your data is almost certainly still in the volume; never remove it while diagnosing. Recreate the container with the volume attached:

```
docker run -d -p 8000:8000 -v cptr-data:/data ghcr.io/open-webui/computer:latest
```

Your account, workspaces, and settings come back with it.

## Docker: SQLite can't write /data

You bind-mounted a host directory that the container user can't write to. Fix the ownership of the host directory, or (simpler and more robust) use a named volume (`-v cptr-data:/data`) instead of a bind mount. Don't run the container privileged as a shortcut.

## My project folder isn't visible in Docker

The container only sees what you mount into it. Add your project as a bind mount and use the **container** path as the workspace path:

```
docker run -d -p 8000:8000 -v cptr-data:/data -v ~/code/myproject:/workspace/myproject ghcr.io/open-webui/computer:latest
```

Then add `/workspace/myproject` as the workspace.

## Agent model missing from the selector / detection not ready

Check the profile status in **Settings ��� Admin ��� Agents**; each status has a specific fix:
- **not found**: the agent CLI isn't on the server's PATH. Install it, or put the absolute path in the profile's Command field.
- **missing dependency**: Claude Code also needs the `claude-agent-sdk` Python package in cptr's environment: `pip install claude-agent-sdk`.
- **auth unknown**: run the agent's own login on the host machine (`claude`, `codex login`, `agent login`, `cline auth`, ���).

Detection results are cached for about 30 seconds, so give it a moment after fixing. Full setup per agent: [coding agents].

## My bot doesn't answer

Work down this list:
- Is the server running, and is the bot's **active** toggle on in **Settings ��� Admin ��� Bots**?
- Did the token pass the **verify** check when you saved it?
- Is your platform user ID actually in **Allowed senders**? A non-empty list silently ignores everyone else.
- Discord and Slack need the `websockets` Python package: `pip install websockets`.
- WhatsApp is webhook-only; the Meta webhook URL must point at a publicly reachable `https://<your-host>/api/webhooks/whatsapp/<bot_id>`.

Full setup per platform: [messaging bots].

## Terminal or chat disconnects behind my reverse proxy

Computer uses Socket.IO: terminals and streaming die if your proxy doesn't forward WebSocket upgrade headers (`Upgrade` / `Connection`). Add them to your proxy config; see [reverse proxy] for nginx/Caddy/Traefik snippets.

## Is the server healthy?

```
curl http://127.0.0.1:8000/api/health
```

Returns `{status, uptime_seconds, pid}` and needs no login. If this fails on the host itself, the server isn't running; check the terminal where you started `cptr run`.

---

# FAQ

## Basics

### Do I need an AI provider or API key?

No. Files, editor, terminal, and git work with zero AI configuration. Add a model whenever you want chat; an API key, Ollama, or a coding-agent subscription all work: [connect a model].

### What do I need to run it?

Python 3.10+ on macOS, Linux, or Windows (`pip install cptr`), or Docker (`ghcr.io/open-webui/computer:latest`). See the [quickstart].

### How is this different from Open WebUI or Open Terminal?

Open WebUI is a chat interface for models; Open Terminal shares a terminal; Computer serves your whole machine to any browser: files, editor, terminal, git, AI, agents. Full comparison: [which tool do I need?]

### What's the license? Does it cost anything?

Computer is source-available under the Open Use License and free to self-host; commercial and enterprise licenses are available at openwebui.com.

### How do I update?

`pip install --upgrade cptr` (or pull the new Docker image and reuse the same `/data` volume). Database migrations run automatically on startup; no manual step. Details: [updating].

### How do I uninstall?

`pip uninstall cptr`. If you want everything gone, also delete `~/.cptr` (accounts, settings, uploads) and the `.cptr/` folder inside each workspace (chats, artifacts). Your project files are untouched either way.

## Phone and remote

### How do I reach it away from home?

Tailscale is the recommended path: your computer gets a stable private address that works from anywhere. Cloudflare Tunnel and ngrok work too, with their own auth layer in front. Start here: [phone and remote access].

### Does work keep running when I close the tab?

Yes. Chats, agent tasks, terminals, and scheduled runs all live on the server, not in your browser. Close the tab on the train, reopen from your desk, and everything is where you left it. Only stopping or restarting the server itself ends running terminals and in-flight background sub-agents.

### Does my computer have to stay on?

Yes. Computer serves *your* machine, so a sleeping or powered-off host serves nothing. Stop it from sleeping and start it on boot: [keep it running].

### Is there a mobile app?

It's a PWA: open it in your phone browser and add it to your home screen for a full-screen, app-like experience. See [use it from your phone].

### Is it safe to put on the internet?

Treat it like SSH: anyone who signs in gets full filesystem and shell access to the host. Don't expose the raw port publicly. Use Tailscale or a tunnel with its own access control in front, and read the [security model].

## AI and agents

### Can I use my Claude Code or Codex subscription?

Yes. Install and log in to the agent CLI on the machine running Computer, add it in **Settings ��� Admin ��� Agents**, and it appears as a chat model. No API key needed, and sessions resume across devices. Setup: [coding agents].

### Does it work with Ollama?

Yes. Add a connection with provider **OpenAI**, base URL `http://localhost:11434/v1`, and any non-empty API key; your local models are auto-discovered. See [connect a model].

### Can I approve what the agent does from my phone?

Yes. Approval prompts appear inline in the chat, and the same **ask**/**auto**/**full** modes and plan mode work from any device. See [approvals and plan mode].

### Can I message my computer from Telegram or WhatsApp?

Yes. Telegram, Discord, Slack, WhatsApp, and Signal bots all run the full agent in a workspace you choose, and the conversations show up in your sidebar. Setup per platform: [messaging bots].

### Can it run tasks on a schedule?

Yes. The **Scheduled** page runs any prompt on a recurring schedule (daily, weekly, hourly), with run history and an optional webhook trigger for CI or cron. See [scheduled tasks].

### Is there an API?

Yes: an OpenAI-compatible gateway at `/v1`. Each workspace appears as a model (`cptr/<name>`), authenticated with `sk-cptr-...` keys, so any OpenAI client can drive the full agent. Reference: [gateway API].

### Can I use a workspace from Open WebUI?

Yes. Add the gateway as an OpenAI connection in Open WebUI and your workspaces appear in its model picker. See [use a workspace from Open WebUI].

## Data and privacy

### Where is my data, and what leaves my machine?

Everything is local: accounts, settings, and uploads in `~/.cptr`, chats inside each workspace's `.cptr/` folder. Nothing leaves your machine except the requests you send to providers you configure yourself (model APIs, search providers, bot platforms). Details: [data and backups].

### How do I back up?

Copy the data directory (at minimum `app.db`, `config.toml`, and `uploads/`) plus your workspaces; chats travel with them in `.cptr/`. Recipes: [data and backups].

## Limits

### Can multiple people use it?

Accounts and admin roles exist, but there is no isolation between users: every signed-in user gets full filesystem and shell access within the boundary you installed it with (the whole host bare, or the mounted folders in Docker). It's one trust domain, so share it only with people you'd give SSH access to.

### Is HTTPS built in?

No. `cptr run` serves plain HTTP with no TLS flags. Get HTTPS from Tailscale, a tunnel, or a reverse proxy in front: [reverse proxy].