## Self-hosted Sentry (local dev on macOS via Docker)

This project integrates with Sentry via the Python SDK (`sentry-sdk`).
For local development, the easiest path is **Sentry Self-Hosted** running in Docker.

### 1) Run Sentry Self-Hosted

Sentry maintains an official self-hosted repo which includes an installer and a Docker Compose stack.

#### macOS prerequisites

- **Docker Desktop RAM**: Sentry self-hosted needs a lot of memory. Increase Docker Desktop to **14GB+**:
  - Docker Desktop → Settings → Resources → Memory → set **14GB+** → Apply & Restart
- **Bash**: macOS ships **bash 3.2** by default; Sentry self-hosted requires **bash >= 4.4**:

```bash
brew install bash
```

- Clone the self-hosted repo (outside this repo, or under `ops/sentry/`):

```bash
mkdir -p ops/sentry
cd ops/sentry
git clone https://github.com/getsentry/self-hosted.git
cd self-hosted
```

- Run the installer and start the stack:

```bash
./install.sh
docker compose up -d
```

Sentry should be available at `http://localhost:9000`.

### 2) Create a Sentry project and get the DSN

In the Sentry UI:
- Create a project (Django)
- Copy the **DSN**

### 3) Configure the Django app to send events to local Sentry

Because your Django app runs inside Docker, **`localhost` inside the container is not your Mac**.

Use Docker Desktop's host gateway name:

- Replace `localhost` with `host.docker.internal` in the DSN.

Example:

```bash
export SENTRY_DSN="http://<public_key>@host.docker.internal:9000/<project_id>"
export SENTRY_ENVIRONMENT="local"
export SENTRY_TRACES_SAMPLE_RATE="0.1"
```

### 4) Rebuild your app container (to install `sentry-sdk`)

After adding the dependency, rebuild:

```bash
./bin/dev-down
./bin/dev-up --build
```

### Notes

- The Platform Test Runner is **DEBUG-only**; Sentry in production should use HTTPS and secure settings.
- We tag Sentry events with `tenant_schema` and `request_id` (when available), to keep multi-tenant triage clean.

