# Local frontend integration

Use a standalone checkout of the integration branch. Run the backend against its dedicated fictional SQLite database. The seed entry point enforces its exact path and development settings.

From the repository root in PowerShell:

```powershell
Set-Location services/api
python -m pip install -r requirements.txt
$env:ENVIRONMENT = 'development'
$env:ENABLE_DEMO_MODE = 'true'
$env:MOCK_OTP = 'true'
$env:DATABASE_URL = 'sqlite+pysqlite:///' + ((Join-Path (Get-Location) 'krishilink_demo.db').Replace('\','/'))
python -m app.seed_dev --demo
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second shell at the repository root:

```powershell
npm.cmd ci
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000/api/v1'
npm.cmd run dev -- --host 127.0.0.1
```

Live adapter calls are the default. To start an explicit frontend simulation, set `VITE_API_DEMO_MODE=true` before starting Vite or building, and use the existing demo role navigation. Demo data belongs to the current browser session. Backend demo login and browser simulation are independent.

Buyer and farmer password registration persists a user and its credential in the API-owned database. Sign in with that mobile number and password. Existing operational users require administrator provisioning. Dev OTP challenges require explicit development settings and do not send SMS. The browser smoke uses the normal sign-up and sign-in forms for its buyer session and gated demo identities for operational workflows. Do not expose this development server to other clients.

Run the FastAPI suite from `services/api` using `python -m pytest -q`. Run `npm.cmd run build` from the standalone frontend checkout. The build includes TypeScript checking. If testing via Vite preview on a different port, include its exact origin in backend `ALLOWED_ORIGINS` before launching FastAPI.

To run the browser smoke from the repository root, install Playwright locally with `npm.cmd install --no-save --package-lock=false playwright` and install Chromium with `npx.cmd playwright install chromium`. Set `KRISHILINK_BROWSER_EXECUTABLE` to use an existing browser instead. Set `KRISHILINK_FRONTEND_URL` and `KRISHILINK_API_URL` to override loopback defaults. Run `node services/api/tests/frontend_smoke.mjs live` against the seeded backend and live adapter. Run `node services/api/tests/frontend_smoke.mjs screenshots` against the explicit demo build or the original branch. Set `KRISHILINK_SCREENSHOTS` to choose a destination outside the checkout.

PostgreSQL/PostGIS integration requires a separate database and DBA review. The SQLite seed command is specific to the isolated demo file.

Settlement calculations use only farmer confirmed, grade A/B pickup receipts and the published reference price for the listing date. The default pilot deductions are 5% commission and 3% logistics. Admin approval creates balanced ledger entries and a `PENDING` payout intent. A provider callback and verified signature are required before a payout can become `SUCCESS` or a settlement can be marked paid; that provider integration is not included.
