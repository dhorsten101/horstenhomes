# Security Model

This document defines the **security boundaries** of Horsten Homes.

Security is designed around **tenant isolation first**, not perimeter defenses.

---

## Threat Model

Primary threats considered:
- Cross-tenant data leakage
- Privilege escalation between tenants
- Misconfigured routing
- Unsafe admin access

---

## Authentication

- Authentication is **tenant-local**
- Each tenant has its own user table
- Credentials are never shared across tenants

There are:
- No global users
- No shared sessions
- No cross-tenant tokens

---

## Authorization

- Django permissions are tenant-scoped
- Superusers exist per tenant only
- Staff access applies only within a tenant schema

---

## Session & Cookies

- Sessions stored in tenant schema
- Cookies are scoped to tenant domains
- No shared authentication cookies

---

## Routing Security

- Tenant resolution is based on hostname
- Unknown hostnames return 404
- No fallback tenant
- No default tenant

---

## Database Security

- PostgreSQL enforces schema isolation
- Application never queries across schemas
- No database user has cross-schema privileges at runtime

---

## Admin Interface

- `/admin` is tenant-specific
- Admin access is isolated per tenant
- No master admin across tenants

---

## Prohibited Security Patterns

❌ Global admin dashboards  
❌ Shared auth backends  
❌ Cross-tenant reporting endpoints  
❌ Raw SQL without schema safety  
❌ Background tasks that span tenants

---

## Incident Response

Any suspected breach of tenant isolation requires:
1. Immediate halt of affected services
2. Audit of schema access
3. Formal incident report
4. ADR if architectural changes are required

---

**Tenant isolation is the primary security boundary.**