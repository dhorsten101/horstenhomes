# Production Deployment Guide

This document describes the **intended production model** for Horsten Homes.

Production is **intentionally simple**.

---

## Target Environment

- Ubuntu 22.04 LTS or newer
- Single-node deployment
- systemd-managed services
- No Docker in production
- No Kubernetes

---

## Runtime Stack

| Component | Tool |
|--------|------|
| App server | Gunicorn |
| Web server | Nginx |
| Database | Managed PostgreSQL |
| Cache / broker | Redis |
| Process manager | systemd |

---

## Application Services

Production runs as **three system services**:

1. `horstenhomes-web` (Gunicorn)
2. `horstenhomes-worker` (Celery)
3. `nginx`

---

## Gunicorn

- WSGI application
- Multiple workers
- Bound to localhost
- Managed via systemd

Example:
```bash
gunicorn config.wsgi:application \
  --workers 4 \
  --bind 127.0.0.1:8000