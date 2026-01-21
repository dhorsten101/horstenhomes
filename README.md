# Horsten Homes

Horsten Homes is a **SaaS platform with schema-per-tenant multi-tenancy**, built on **Django and PostgreSQL**.

It is designed for **strong tenant isolation, operational clarity, and controlled scaling**, intentionally **without Kubernetes or docker-compose**.

This repository is **developer-focused** and optimized for **Docker-based local development**.

---

## Key Characteristics

- Single Django project (modular monolith)
- PostgreSQL **schema-per-tenant** isolation
- Public schema used for control-plane data only
- Tenant-local users and admin
- Docker-first development workflow
- Explicit operational commands via `./bin/dev`

---

## Tech Stack

| Layer | Technology |
|-----|-----------|
| Backend | Django 5.x |
| Multi-tenancy | django-tenants |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis |
| Frontend | Django templates + HTMX |
| Styling | Bootstrap |
| Dev runtime | Docker |
| Prod target | Ubuntu 22.04+ |
| Orchestration | None (intentional) |

---

## Architecture Overview

### Multi-Tenant Model

Horsten Homes uses **schema-per-tenant multi-tenancy**.

#### Public Schema
- Tenant registry
- Domain routing
- No business or user data

#### Tenant Schemas
- Users & authentication
- Business models
- Admin interface
- Fully isolated per tenant

Each incoming request is routed to a tenant schema based on **hostname**.

📌 **Architecture is frozen.**  
See `docs/ADR-0001-architecture-freeze.md`.

---

## Repository Structure

```text
horstenhomes/
├── apps/
│   ├── tenancy/        # Tenant + Domain (public schema)
│   ├── accounts/       # Custom tenant user model
│   └── ...
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   └── local.py
│   └── urls.py
├── bin/                # Dev CLI scripts (single entrypoint)
├── Dockerfile.dev
├── pyproject.toml
├── .env.dev
├── README.md
└── CONTRIBUTING.md