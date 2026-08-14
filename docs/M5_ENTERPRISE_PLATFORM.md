# M5.8 Enterprise Automation Platform

Control-plane features for multi-tenant operations on top of the plugin and distributed runtime.

## Capabilities

| Capability | Module | Notes |
|------------|--------|-------|
| Tenant context | `TenantContext` | `tenant_id` + `actor` from body or headers |
| API key auth | `ApiKeyAuthenticator` | Enabled when `SWP_API_KEYS` is non-empty |
| Rate limiting | `RateLimiter` | Fixed window per tenant |
| Audit log | `AuditLog` | In-memory trail of `task.run` events |
| Readiness | `EnterprisePlatform.readiness` | Aggregates auth / rate limit / infra checks |
| Admin API | `/api/v1/admin/*` | Plugins, audit, status |

## Headers

| Header | Purpose |
|--------|---------|
| `X-API-Key` | Shared secret when auth is enabled |
| `X-Tenant-Id` | Tenant attribution (default `default`) |
| `X-Actor` | Human or service identity (default `anonymous`) |

## Settings (`SWP_` prefix)

| Variable | Default | Notes |
|----------|---------|-------|
| `API_KEYS` | `[]` | List; empty disables auth |
| `RATE_LIMIT_PER_MINUTE` | `120` | Per-tenant fixed window |
| `AUDIT_MAX_EVENTS` | `5000` | In-memory ring buffer size |

## Admin endpoints

- `GET /ready` — readiness (no auth required for orchestrators)
- `GET /api/v1/admin/plugins` — loaded plugins and tasks
- `GET /api/v1/admin/audit` — recent audit events
- `GET /api/v1/admin/status` — platform summary

## Out of scope

- OAuth/OIDC, RBAC roles matrix
- Durable audit store (Postgres)
- Per-tenant plugin isolation / separate runtimes
