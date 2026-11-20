# Local operational development

This creates a separate PostgreSQL/PostGIS database on `127.0.0.1:5433`; it does not connect to or modify another database. Docker Compose keeps data in the named `krishilink_pg_dev_data` volume. Do not use `down -v` unless intentionally deleting this local development database.

PowerShell commands from the repository root:

```powershell
$env:KRISHILINK_DEV_DB_PASSWORD = Read-Host "Development database password"
docker compose -f compose.postgres.dev.yml up -d
$env:ENVIRONMENT = "development"
$env:MOCK_OTP = "true"
$env:DATABASE_URL = "postgresql+psycopg://krishilink_dev:$($env:KRISHILINK_DEV_DB_PASSWORD)@127.0.0.1:5433/krishilink_dev"
Set-Location services/api
alembic upgrade head
python -m app.seed_dev --apply
```

The deterministic development identities printed by the seed command can request OTPs only when the backend is explicitly configured with `ENVIRONMENT=development` and `MOCK_OTP=true`. The public OTP flow cannot choose privileged roles. Never reuse these credentials outside the isolated development database.

Settlement calculations use only farmer confirmed, grade A/B pickup receipts and the published reference price for the listing date. The default pilot deductions are 5% commission and 3% logistics. Admin approval creates balanced ledger entries and a `PENDING` payout intent. A provider callback and verified signature are required before a payout can become `SUCCESS` or a settlement can be marked paid; that provider integration is not included.
