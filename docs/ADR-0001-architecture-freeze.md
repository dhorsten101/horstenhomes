# ADR-0001: Architecture Freeze

**Status:** Accepted  
**Date:** 2026-01-21  
**Owner:** Horsten Homes Engineering  
**Scope:** Entire application platform

---

## Context

Horsten Homes is a SaaS platform designed around **schema-per-tenant multi-tenancy** using Django and PostgreSQL.

Early architectural decisions have now been implemented and validated in a working development environment, including:

- Schema-per-tenant isolation
- Tenant-local authentication
- Docker-based local development
- Explicit operational tooling via `./bin/dev`

At this stage, **stability, predictability, and operational clarity** are higher priorities than architectural experimentation.

---

## Decision

The architecture of Horsten Homes is **frozen**.

No changes to core infrastructure, tenancy model, runtime assumptions, or foundational tooling are permitted without an explicit Architecture Decision Record (ADR).

This includes—but is not limited to—the areas listed below.

---

## Frozen Architecture

### Application Structure
- Single Django project (modular monolith)
- Multiple Django apps within one codebase
- No microservices

### Multi-Tenancy Model
- PostgreSQL schema-per-tenant via `django-tenants`
- Public schema for control-plane data only
- Tenant schemas for all business and user data
- Hostname-based tenant resolution

### Authentication
- Tenant-local user model
- No global/shared users
- No cross-tenant authentication

### Runtime & Environment
- Docker-based local development
- PostgreSQL and Redis as standalone containers
- No docker-compose
- No Kubernetes
- Production target: single-node Ubuntu (systemd-managed services)

### Frontend
- Django templates
- HTMX for interactivity
- Bootstrap for styling
- No SPA framework (React, Angular, Vue, etc.)

### Tooling
- Explicit operational scripts under `./bin/`
- Single CLI entrypoint via `./bin/dev`
- No hidden automation

---

## Explicitly Rejected (Unless New ADR)

The following are **explicitly out of scope** and may not be introduced casually:

- Kubernetes
- docker-compose
- Microservices
- Global/shared user tables
- Cross-tenant data access
- SPA frontend frameworks
- Serverless components
- Auto-scaling infrastructure
- Multiple databases per tenant

---

## Consequences

### Positive
- Predictable behavior
- Easier onboarding
- Clear operational boundaries
- Reduced cognitive load
- Strong tenant isolation guarantees

### Trade-offs
- Scaling requires deliberate planning
- Some automation is manual by design
- Infrastructure changes require formal review

These trade-offs are **intentional**.

---

## Change Process

Any change to frozen areas must follow this process:

1. Create a new ADR (e.g. `ADR-0002-<title>.md`)
2. Clearly state:
    - Problem
    - Proposed change
    - Alternatives considered
    - Risks
3. Review and approval by core maintainers
4. Merge ADR **before** implementation

No exceptions.

---

## Notes

This ADR exists to protect the platform from:
- Accidental over-engineering
- Tooling sprawl
- Premature scaling decisions
- Inconsistent operational patterns

Feature development may continue freely **within** these boundaries.

---

**Architecture is frozen as of this record.**