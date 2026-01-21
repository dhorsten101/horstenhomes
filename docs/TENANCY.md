# Tenancy Rules & Guarantees

This document defines **non-negotiable rules** governing multi-tenancy in Horsten Homes.

Violations of these rules are considered **critical defects**.

---

## Tenancy Model

Horsten Homes uses **PostgreSQL schema-per-tenant isolation** via `django-tenants`.

- One **public schema**
- One **schema per tenant**
- No shared business data

---

## Public Schema Rules

The public schema MAY contain:
- Tenant registry (`Tenant`)
- Domain routing (`Domain`)
- Platform metadata

The public schema MUST NOT contain:
- Users
- Authentication data
- Business models
- Tenant-owned configuration
- Any data tied to customer activity

Public schema is **control-plane only**.

---

## Tenant Schema Rules

Each tenant schema contains:
- User accounts
- Authentication state
- Business data
- Admin interface

Tenant schemas are:
- Logically isolated
- Independently migratable
- Independently queryable

---

## Absolute Prohibitions

The following are **strictly forbidden**:

❌ Cross-tenant queries  
❌ Foreign keys across schemas  
❌ Global user tables  
❌ Shared authentication  
❌ “Reporting” schemas that aggregate tenants  
❌ Bypassing `TenantMainMiddleware`  
❌ Raw SQL that ignores `search_path`

Any of the above constitutes a **security incident**.

---

## ORM Usage Rules

- All ORM access MUST be tenant-aware
- Use `schema_context()` **only** for explicit maintenance tasks
- Application code MUST NOT manually switch schemas

---

## Admin Rules

- Django admin is **tenant-local**
- Superusers exist per tenant
- No global admin UI across tenants

---

## Enforcement

- Tenant middleware is mandatory
- CI reviews must reject cross-tenant patterns
- ADR required to change any rule here

---

**Tenant isolation is a core product guarantee.**