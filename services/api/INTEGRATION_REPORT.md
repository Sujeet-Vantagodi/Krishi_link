# KrishiLink frontend-first integration report

## Core logistics continuation from `1e6253a8d03f7d8cc048d10a6cf15ea82aa92553`

| Workflow | Result |
| --- | --- |
| Buyer catalog, checkout and persisted orders | Browser verified. The adapter uses live checkout, history and detail DTOs. Checkout stores the address, charges the current published quote in the order total, schedules the next available date in IST and creates a pending payment record. It does not collect payment, allocate future stock or dispatch unpaid orders. The order ID and `PLACED` status persist after reload. |
| Buyer tracking | TestClient verifies persisted status and real driver telemetry. Live page integration remains blocked by protected synthetic fallbacks and the absence of a durable secure handover-code presentation. |
| Farmer harvest and pickup | Browser verified harvest submission and reload. TestClient verifies eligible listing assignment, unauthorized denial, driver acknowledgement/start, arrival, confirmed pickup receipt, and pickup completion. Driver and dispatch screens remain unverified. |
| Hub grades and settlements | TestClient verifies mismatched grade weights are rejected and settlement uses the reconciled quantities. Saleable stock excludes rejected kilograms. The browser displayed a reconciled farmer settlement calculated through the real API using seeded receipt evidence. Payout remains pending through the native approval path. |
| Transfers | Browser verified approval and reload. Native tests verify assignment to an actual compatible trip, measured dispatch, destination arrival, measured receipt, duplicate protection and stock ledger entries. The browser transfer controls still lack trip and measurement inputs. |

### Final checks

- `python -m pytest -q --tb=short` passed **66 tests**, with 10 deprecation warnings. `app.openapi()` generated **87 paths**.
- `node_modules/.bin/tsc.cmd --noEmit` and Vite live and demo production builds passed. The standalone temporary checkout kept Vite separated from the conflicted parent checkout.
- `node services/api/tests/frontend_smoke.mjs live` exercised real FastAPI requests on a dedicated demo SQLite database. Admin pickup assignment, driver arrival/completion, grade weigh-in, transfer dispatch and transfer receipt were tested through native APIs or services and were not browser-driven.
- `node services/api/tests/frontend_smoke.mjs screenshots` captured both viewport sizes. All 12 demo screenshot pairs against `origin/2branch` matched pixel-for-pixel. The protected path comparison and `git diff --check` passed.

### Changed files

- Frontend changes are confined to `src/lib/api/index.ts`.
- API model and migration changes are in `app/models/order.py` and `alembic/versions/0005_order_address.py`.
- Routes are in `app/routers/{driver,hubs,orders,transfers}.py`. Request/response schemas are in `app/schemas/{order,transfer}.py`.
- Business rules are in `app/services/{order_service,trip_service,transfer_service,settlement_service}.py`.
- Verification changes are in `tests/frontend_smoke.mjs` and `tests/test_{driver_dispatch,e2e_integration,frontend_contract,operations,order_concurrency}.py`.
- The frontend audit and database requirements list the exact protected approval points and migration prerequisites. The teammate-owned `database/` tree remains unchanged.

## Continuation from `1dbca2eb727b385cddae2b0c280107acdbe1e609`

| Scope | Result |
| --- | --- |
| Password authentication | Buyer and farmer registration, salted scrypt verification, duplicate protection, backend role navigation, JWT issuance, current user and refresh. The approved frontend handlers no longer fall back to mock authentication in live mode. |
| OTP | Real API challenge and verification with explicitly enabled development OTP. Production reports unavailable SMS. Fixed development OTP cannot sign into password or operational accounts. |
| Transfers | Live listing, requests, approval and rejection, persisted urgency and hub-scoped access. Native dispatch now requires an explicit sent weight. The current frontend cannot collect assignment and measured weights, so its dispatch and receipt actions remain unavailable. |
| Tracking | Native API now returns real order status and assigned-driver telemetry, with null missing location and ETA. The protected page contains synthetic fallbacks, so its live adapter stays unavailable. Buyer order replay no longer rotates the delivery code, and idempotency collision handling respects buyer ownership. |

### Verification for this continuation

- `python -m pytest -q --tb=short` from `services/api` passed **64 tests** with seven deprecation warnings. This includes native buyer order, driver workflow, dispatch, and transfer lifecycle tests as well as password, OTP, transfer validation and tracking contract tests.
- `node_modules/.bin/tsc.cmd --noEmit` passed. Vite production and explicit-demo builds both passed in the standalone temporary checkout. `app.openapi()` generated **82 paths**.
- Playwright live smoke passed buyer form registration, wrong and correct passwords, development OTP, and protected-route session restoration on navigation. It also passed live buyer catalog/detail, farmer threshold and harvest writes, hub stock updates, admin settlement read, and transfer approval. It checked persisted writes after reload.
- The original CSS asset remained byte-identical. All 12 desktop/mobile screenshot pairs against the source commit matched pixel-for-pixel in the demo comparison. The protected-file check against `origin/2branch` found no changes outside the two API modules and the three approved auth files. No top-level teammate database files changed.
- Browser checkout, driver itinerary/receipts, dispatch, and transfer dispatch/receipt remain unverified. The settlement browser check reads persisted statements, and does not verify hub scale reconciliation.

### Remaining work

- Checkout still sends a fixed date. The API lacks the immutable delivery address and verified payment contract needed by the existing order history and checkout. Tracking needs permission to remove hardcoded driver, ETA and OTP fallbacks from the protected page.
- Driver and dispatch UI still need stop and assignment contracts that preserve the existing business invariants. The protected arrival hook drops coordinates. Pickup and delivery forms also need support for batch evidence with per-crop measurements.
- Settlement calculation uses confirmed grade A/B pickup receipts. Per-farmer allocation when the aggregate hub weight differs from those receipts remains unresolved.
- Operational password provisioning, verified phone ownership, production SMS, and server-side refresh revocation require separate integration. The current schema migrations were exercised through fresh SQLite ORM schema creation and tests. PostgreSQL Alembic application remains unverified.

### Changed files

- Frontend `src/stores/authStore.ts`, `src/pages/auth/Login.tsx`, `src/pages/auth/VerifyOtp.tsx`, and `src/lib/api/index.ts`.
- API models `app/models/{user,trip}.py`, routes and schemas `app/{routers,schemas}/{auth,orders,transfers}` (schema modules use the singular `order` and `transfer`), and services `app/services/{auth_service,password_service,order_service,transfer_service}.py`.
- Migrations `0003_password_credentials.py` and `0004_transfer_urgency.py`.
- `tests/test_frontend_contract.py`, `tests/frontend_smoke.mjs`, and the setup, audit, DB requirements and integration documents.

## Prior integration results

## Repository and scope

- Repository `Sujeet-Vantagodi/Krishi_link`, source `origin/2branch` at `9c9a89bb94e118817838c1058a0d7cf57c25651b`.
- Local integration branch `feat/frontend-first-api-integration` in a fresh clone. The surrounding checkout points to a different repository and contained unresolved conflicts.
- This is a partial integration. Unwired adapter operations return an unavailable error in live mode. The original adapter simulations are explicit through `VITE_API_DEMO_MODE=true`.

## Protected frontend verification

The Git tree at the source commit is the protected file baseline. The following comparison passed with no diff. The source `database/` tree matched the baseline too.

```powershell
git diff --exit-code origin/2branch -- src ':(exclude)src/lib/api/client.ts' ':(exclude)src/lib/api/index.ts' public index.html tailwind.config.js postcss.config.js vite.config.ts database
```

Baseline and integration builds produced byte-identical CSS assets with SHA-256 `9FAE31E70104534B7D71AB7761E07AE0AAFD6A14FEBFC063D2195E723C37D3C1`. The 12 screenshot pairs were pixel-identical. Playwright covered landing, login, and buyer, farmer, driver, and admin dashboards at 1440×900 and 390×844. The source build came from a Git archive. The integration comparison used explicit frontend demo mode, the same fixture roles and clock, and local resources. The live browser checks below use real HTTP.

## Coverage and working journeys

| Feature | Status | Evidence |
| --- | --- | --- |
| Landing, login screen and role dashboards | Implemented and verified for route rendering | Playwright captured each route in desktop and mobile views. Password and role authentication are tracked separately below. |
| Buyer catalog, crop detail and published price read | Implemented and verified | Browser observed live catalog and detail GETs and rendered the seeded crop. HTTP contract covers roots filtering, no synthetic price, and ledger-derived available stock. Catalog crops need current prices, shelf life and a supported category. Network-level stock is indicative. Buyer-specific availability is unresolved. |
| Farmer thresholds and harvest listing | Implemented and verified | Browser saved a threshold, reloaded persisted state, submitted a crop listing and reloaded the same listing ID. HTTP contract tests also cover role denials, invalid overrides, cancellation and threshold-based eligibility. Existing native listing creation retains pilot cutoff behavior. |
| Hub list, detail, matrix and status | Implemented and verified | The browser rendered the hub matrix, changed a stock status and reloaded the persisted value. TestClient covers hub detail and role scope. Verified ledger kg is distinct from manual status. The protected success toast currently runs before a mutation resolves. |
| Driver transition adapter | Partially implemented | Native acknowledge/start verified via HTTP contract, with native tests for further transitions. Live trip lists, full itinerary, actual coordinates forwarded by the arrival hook, receipt forms, telemetry, and driver browser actions remain blocked. |
| Farmer and admin settlement review | Implemented and verified | The admin browser rendered a real settlement statement. TestClient covers owner-only farmer statements and admin approval. Approval persists without a paid date. |
| Account creation and password login | Blocked | Credential fields and ownership verification must be reconciled with the database team. Legacy and current URL aliases return HTTP 503. |
| OTP and existing session operations | Partially implemented | Backend-generated development OTP was tested over TestClient with invalid code and replay rejection, JWT and current user. Backend refresh can issue fresh tokens with the existing design. Production SMS and persistent revocation are blocked. Protected browser OTP flow still runs local demo logic. |
| Buyer orders, checkout, tracking and confirmation | Not implemented through the live adapter | Native routes exist. Order address/location, payment state, item and tracking contracts require integration. Browser order creation remains unverified. |
| Admin dispatch, transfers, pricing publication, alerts, directories and settings | Not implemented through the live adapter | Native domain coverage varies. Audit documents the missing DTOs, evidence inputs and directly mocked protected pages. |
| Forecasts, masked calls and payout execution | Blocked | No verified external providers were configured. |

## Authentication and remaining protected wiring

- Legacy password endpoints previously used insecure issuance. The aliases now return an explicit unavailable response. The backend issues development demo tokens only through its already gated seeded SQLite path. Development OTP requires explicit opt-in and returns a generated-development message. Production reports SMS unavailable.
- Shared trip operations now check the actor's role and driver ownership. Hub stock writes and matrix reads scope hub staff to assigned hubs. Validation responses omit non-serializable internals and sensitive raw inputs.
- `src/stores/authStore.ts:61,105,130,153,168,186,200` requires approval for session bootstrap, OTP verification, server role enforcement and logout wiring. The protected login/OTP and route guard currently have demo behavior even when API adapters use live mode. The server denies fake JWTs.
- The detailed frontend audit lists protected directory/settings pages, success toasts, driver coordinate handling and direct mock realtime subscriptions needing approval. The database requirements document lists unresolved identity, order, trip, transfer, ledger and provider dependencies.

## Verification executed

| Check | Result |
| --- | --- |
| Baseline `python -m pytest -q` from `services/api` | 54 passed. |
| Integration `python -m pytest -q --tb=short` from `services/api` | 61 passed. Includes seven added FastAPI contract tests using isolated SQLite. |
| TypeScript `node_modules/.bin/tsc.cmd --noEmit` and Vite `npm.cmd run build` | Baseline and integration production builds passed in a standalone temporary checkout. Initial nested Vite run encountered merge markers in an ancestor's unrelated package.json. |
| `app.openapi()` | Generated 79 paths. The contract suite independently fetched `/openapi.json` through FastAPI. |
| `node services/api/tests/frontend_smoke.mjs screenshots` | Captured 12 route screenshots per build. All pairs matched pixel-for-pixel. |
| `node services/api/tests/frontend_smoke.mjs live` | Passed against Vite preview and loopback Uvicorn with the isolated SQLite seed. Verified buyer catalog/detail, farmer threshold and harvest persistence, hub stock matrix persistence, and admin settlement review. Also verified unauthenticated threshold denial. The browser received real access tokens from the gated demo endpoint. |
| Protected-path Git comparison and `git diff --check` | Passed. |

Real loopback HTTP traffic included demo token issuance, catalog and detail reads, threshold GET/PUT with authorization and retention, listing POST/GET with a persisted listing ID, stock status PUT and matrix reload, and admin settlement retrieval. TestClient exercised other HTTP contracts in-process. No shared DB, PostgreSQL/PostGIS instance, SMS, payment gateway, payout provider, route service, or forecast provider was used.

## Changed-file inventory

- Frontend API wiring only in `src/lib/api/client.ts` and `src/lib/api/index.ts`.
- FastAPI bootstrap, development settings and seed in `app/main.py`, `app/config.py` and `app/seed_dev.py`.
- Router changes in `app/routers/{admin,auth,catalog,farmers,frontend_bridge,hubs}.py`.
- DTO changes in `app/schemas/{crop,farmer,hub,settlement,trip}.py`.
- Domain changes in `app/services/{auth_service,listing_service,stock_service,trip_service}.py`.
- Tests in `tests/{conftest.py,test_frontend_contract.py,frontend_smoke.mjs}`.
- Setup and audit documents in `DEV_OPERATIONS.md`, `FRONTEND_CONTRACT_AUDIT.md`, `DATABASE_INTEGRATION_REQUIREMENTS.md`, and this report.

## Starting the app

Use the isolated backend setup and seed instructions in [DEV_OPERATIONS.md](DEV_OPERATIONS.md). Start FastAPI with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` from `services/api`, and the frontend with `npm.cmd run dev -- --host 127.0.0.1` from the integration repository root. Set `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1` in the frontend shell. Use the live browser smoke for supported real HTTP workflows until the protected authentication wiring is approved.
