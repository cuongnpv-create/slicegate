# SAAS_GUIDE — multi-tenant SaaS industry rules ({{PROJECT}})

Supplements `GATE_PROTOCOL`. Primary gates: `tenancy-lead` (isolation, zone K), `billing-lead` (plans & billing, zone T/F).

## 1. Choose an isolation model (record it in `DECISIONS.md`)

| Model | Isolation | Operating cost | The pack's guards |
|---|---|---|---|
| Shared tables, `tenant_id` column | lowest — relies on queries + RLS | cheap | `tenant_scope` + `tenant_rls` (enable `require_rls`) |
| Schema per tenant | medium — relies on `search_path` | medium | cross-tenant tests in zone K |
| Database per tenant | highest | expensive | connection-routing tests |

## 2. Suggested risk zones (declare them in `gatekit.toml`)

| Zone | Typical code | Example regex |
|---|---|---|
| K | tenant context, auth, permissions, middleware, repositories/DAO, cache | `'^src/(tenancy|auth|middleware|repositories?|cache)/'` |
| T | recurring billing, billing webhooks, tenant deletion | `'^src/(billing|webhooks?)/'`, `'^src/tenants/delete'` |
| F | proration, usage metering, plan limits | `'^src/(billing/proration|metering|entitlements?)/'` |

## 3. Hard rules

1. Tenant context only from the authenticated session; never from an unchecked parameter/header/subdomain.
2. Every customer-data table has `tenant_id NOT NULL` (leading the primary key or indexed); shared tables declare `-- tenant: global <reason>`.
3. Every query on a tenant table filters `tenant_id`; on Postgres enable RLS + a policy on `current_setting('app.tenant_id')`.
4. Cache / queue / storage / search / realtime channel / rate-limit keys carry the tenant.
5. Background jobs carry the tenant in the payload and reset the context before running.
6. Impersonation: reason + expiry + audit log.
7. All of one tenant's data can be exported / deleted.
8. Plan limits are checked server-side at each place of use.

## 4. Mandatory cross-tenant tests (zone K)

Build two tenants A and B with identical data; every read/edit/delete endpoint called by an A user with a B id ⇒ named
refusal; A's lists / search / exports contain no B record. One test parametrized over the endpoint list — an endpoint added
but not declared in the list ⇒ RED (compare the real route set with the declared set).

## 5. Sample mutant suite (zone K)

```toml
zone = "K"
cmd = "PYTHONPATH=src python -m pytest -q tests/tenancy"

[[mutant]]
id = "tenant-q-01"
file = "src/repositories/invoices.py"
find = "WHERE tenant_id = %s AND id = %s"
replace = "WHERE id = %s"
why = "drops the tenant condition ⇒ tenant A reads tenant B's invoices"

[[mutant]]
id = "tenant-cache-01"
file = "src/cache/keys.py"
find = "return f\"{tenant_id}:{name}:{key}\""
replace = "return f\"{name}:{key}\""
why = "cache key without the tenant ⇒ B receives A's cached data"

[[mutant]]
id = "tenant-ctx-01"
file = "src/tenancy/middleware.py"
find = "tenant_id = session.tenant_id"
replace = "tenant_id = request.headers.get(\"X-Tenant-Id\", session.tenant_id)"
why = "tenant context taken from a self-declared header ⇒ changing the header switches tenant"
```
