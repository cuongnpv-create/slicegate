# CONSTITUTION — {{PROJECT}} (Tier 0)

Supreme articles. Each article names where the machine enforces it; an article without enforcement is a **DRAFT** (Article 7).

## Article 1 — Single source of truth
Every fact has exactly one owner (one file, one table, one constant). Copies are only machine-generated from the owner, with a consistency check.

## Article 2 — Everything is an identified entity
Business entities have stable identifiers and an explicit lifecycle (state machine); never derived from display strings.

## Article 3 — Capability over role
Permissions are checked against granted capabilities, never against role names hard-coded in the code. Missing capability
⇒ **named refusal** (reason code), never `return None`, never pretend it worked.

## Article 4 — Every risky action is auditable
Actions touching money, permissions or user data are logged: who · when · what · outcome. Dangerous mode switches default
to OFF (fail-closed).

## Article 5 — Every screen has an archetype
A screen belongs to one of the defined page archetypes (overview · list · detail · action); empty, error and loading states
are mandatory; no fake data.

## Article 6 — The domain leads the implementation
Business rules live in the server-side domain layer; the UI never computes business logic and never calls external services directly.

## Article 7 — Governance must be machine-enforceable
Important rules have a guard (`slicegate check`) with a negative-case selftest, running in hooks and CI. A new guard is only
born after its defect class has fired ≥ 3 real times (`GUARD_CATCH_LOG.tsv`) and must name the code defect it blocks. A
guard with 0 catches for a long time is a removal candidate.
{{#pack i18n}}

## Article 8 — Localized from day one
Every user-facing string goes through the catalog, in every language, in the SAME slice that adds it. The server returns
`{code, message_key, params}`, never sentences. Numbers / money / dates follow the user's locale and time zone. Never show
an external service's raw error — map it to a reason code and translate. Enforced by: `locale_parity`.
{{/pack}}
{{#pack multi_provider}}

## Article 9 — The provider is explicit
A provider's name lives only in its adapter; every key / table / channel carries the provider (or tenant) dimension.
Enforced by: `provider_name_scope`, `partition_key_scope`.

## Article 10 — Intent → route → translate
The business layer emits intents that do not know the provider; the routing layer checks capabilities; each provider's
translator does the rest. Compare MEANING (reason codes), never a provider's raw error codes.

## Article 11 — Unknown is not No
A capability has 4 values `YES · NO · UNKNOWN · EMULATED`; `UNKNOWN ≠ NO`. Override a library's declaration only with a dated measurement.
{{/pack}}
{{#pack ecommerce}}

## Article 12 — Money is exact
Money is integer minor units or exact decimals, always with its currency; never floating point. Sum of lines = order
total = charged = booked. Card data never lives in the system (tokens only). Enforced by: `money_float`, `pci_scope`.
{{/pack}}
{{#pack saas_multitenant}}

## Article 13 — The tenant is explicit
Every request, job, cache key and customer-data row belongs to exactly one tenant, taken from the authenticated session.
A query without a tenant filter is a defect, even when ids are hard to guess. Enforced by: `tenant_scope`, `tenant_rls`.
{{/pack}}
{{#pack healthcare}}

## Article 14 — Health data is minimal and traceable
Every read of health data has a reader, a reason and a log row; that data never leaves the protected zone (logs,
analytics, notifications). Every clinical number carries a unit and a source. Enforced by: `phi_log`, `phi_tag`.
{{/pack}}
{{#pack logistics}}

## Article 15 — Quantities and times are unambiguous
A physical quantity is never a bare number: its unit is in its name and conversions live in one module. A timestamp is
never naive: it is stored in UTC with its zone and becomes local time only on display. A carrier call that can be
retried never books twice. Enforced by: `unit_suffix`, `naive_time`.
{{/pack}}
