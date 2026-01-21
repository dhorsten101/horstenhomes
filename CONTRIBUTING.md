---

# 📕 `CONTRIBUTING.md`

```md
# Contributing to Horsten Homes

This project is a multi-tenant SaaS system with strict architectural and operational rules.
Contributions must preserve tenant isolation and deployment safety.

---

## Development Rules

- Docker is mandatory
- No local virtualenvs
- No docker-compose
- Do not run manage.py directly on your host
- All operations go through `./bin/dev`

If Docker is not running, you cannot contribute.

---

## Branching Strategy

- `main` → stable and deployable
- Feature branches:


