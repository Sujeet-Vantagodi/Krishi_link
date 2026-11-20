from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import get_db
from app.main import app
from app.models.enums import LedgerReason, TripStatus, TripType
from app.models.payment import Settlement
from app.models.stock import HubStockStatus, StockLedger
from app.models.trip import Trip
from conftest import TestingSessionLocal, make_auth_headers


@pytest.fixture
def api():
    def get_test_db():
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db)


def test_live_catalog_and_published_prices(api, db_session, seed_data):
    crop = seed_data["tomato"]
    crop.shelf_life_hours = 48
    db_session.add(StockLedger(
        hub_id=seed_data["main_hub"].id, crop_id=crop.id,
        delta_kg=5, reason=LedgerReason.ADJUSTMENT,
    ))
    db_session.commit()
    result = api.get("/api/v1/crops")
    assert result.status_code == 200
    by_slug = {item["slug"]: item for item in result.json()["items"]}
    assert by_slug["onion"]["price"] is None
    assert by_slug["onion"]["availability"] == "OUT"
    assert by_slug["tomato"]["availability"] == "LOW"
    assert api.get("/api/v1/crops?category=roots").json()["total"] == 1
    detail = api.get(f"/api/v1/catalog/crops/{crop.id}").json()
    assert detail["shelf_life_hours"] == 48
    assert detail["price"]["reference"] == 2600
    assert api.get("/api/v1/prices/today").json()["items"][0]["date"] == date.today().isoformat()


def test_farmer_thresholds_and_listings_persist(api, seed_data):
    path = "/api/v1/farmers/me/threshold"
    headers = make_auth_headers(seed_data["farmer_user"])
    crop_id = str(seed_data["tomato"].id)
    assert api.get(path).status_code == 401
    assert api.get(path, headers=make_auth_headers(seed_data["buyer_user"])).status_code == 403
    override = {"crop_id": crop_id, "min_kg": 45}
    assert api.put(path, headers=headers, json={
        "default_min_kg": 30, "per_crop": [override, override],
    }).status_code == 422
    assert api.put(path, headers=headers, json={
        "default_min_kg": 30, "per_crop": [{"crop_id": str(uuid4()), "min_kg": 45}],
    }).status_code == 404
    assert api.get(path, headers=headers).json()["default_min_kg"] == 20
    assert api.put(path, headers=headers, json={"default_min_kg": 32, "per_crop": [override]}).status_code == 200
    assert api.put(path, headers=headers, json={"default_min_kg": 33}).status_code == 200
    assert api.get(path, headers=headers).json() == {"default_min_kg": 33, "per_crop": [override]}

    listing_date = date.today() + timedelta(days=3)
    listings = "/api/v1/farmers/me/listings"
    response = api.post(listings, headers=headers, json={
        "crop_id": crop_id, "est_kg": 40, "listing_date": listing_date.isoformat(),
        "ready_by": f"{listing_date.isoformat()}T01:00:00Z",
    })
    assert response.status_code == 201
    listing = response.json()
    assert listing["status"] == "INELIGIBLE"
    assert listing["min_kg_applied"] == 45
    assert listing["cutoff_at"].endswith("+05:30")
    assert api.get(listings, headers=headers).json()["items"][0]["id"] == listing["id"]
    assert api.delete(f"{listings}/{listing['id']}", headers=headers).status_code == 200
    assert api.get(listings, headers=headers).json()["items"][0]["status"] == "CANCELLED"


def test_hub_status_write_is_scoped_and_does_not_create_inventory(api, db_session, seed_data):
    crop = seed_data["tomato"]
    assigned = seed_data["main_hub"]
    other = seed_data["village_hub"]
    headers = make_auth_headers(seed_data["hub_staff_user"])
    request = {"status": "LOW"}
    assert api.put(f"/api/v1/hubs/{other.id}/stock-status/{crop.id}", headers=headers, json=request).status_code == 403
    response = api.put(f"/api/v1/hubs/{assigned.id}/stock-status/{crop.id}", headers=headers, json=request)
    assert response.status_code == 200
    assert response.json()["set_by"] == str(seed_data["hub_staff_user"].id)
    assert db_session.get(HubStockStatus, (assigned.id, crop.id)).status.value == "LOW"
    assert db_session.query(StockLedger).count() == 0
    matrix = api.get("/api/v1/hubs/stock-matrix", headers=headers).json()
    assert [hub["id"] for hub in matrix["hubs"]] == [str(assigned.id)]
    cell = next(cell for cell in matrix["hubs"][0]["cells"] if cell["crop_id"] == str(crop.id))
    assert cell["status"] == "LOW"
    assert cell["suggested"] == "OUT"
    assert cell["exact_kg"] == 0
    detail = api.get(f"/api/v1/hubs/{assigned.id}").json()
    assert detail["lat"] == assigned.location["lat"]
    assert api.get("/api/v1/hubs").json()["total"] == 2


def test_driver_acknowledgement_and_start_contract(api, db_session, seed_data):
    driver = seed_data["driver_user"]
    trip = Trip(
        type=TripType.FIRST_MILE, status=TripStatus.ASSIGNED, driver_id=driver.id,
        vehicle_id=seed_data["vehicle"].id, assigned_by=seed_data["admin_user"].id,
    )
    db_session.add(trip)
    db_session.commit()
    path = f"/api/v1/trips/{trip.id}"
    assert api.post(f"{path}/acknowledge", headers=make_auth_headers(seed_data["buyer_user"])).status_code == 403
    headers = make_auth_headers(driver)
    assert api.post(f"{path}/acknowledge", headers=headers).json()["status"] == "ACKNOWLEDGED"
    assert api.post(f"{path}/start", headers=headers).json()["status"] == "STARTED"
    db_session.refresh(trip)
    assert trip.status == TripStatus.STARTED


def test_settlement_approval_persists_without_marking_paid(api, db_session, seed_data):
    farmer = seed_data["farmer_user"]
    draft = Settlement(
        farmer_id=farmer.id, settle_date=date.today(), accepted_kg=40,
        gross=100_000, commission=6_000, logistics_share=5_000, net=89_000,
    )
    db_session.add(draft)
    db_session.commit()
    farmer_headers = make_auth_headers(farmer)
    admin_headers = make_auth_headers(seed_data["admin_user"])
    path = "/api/v1/admin/settlements"
    approval = f"{path}/{draft.id}/approve"
    original = api.get("/api/v1/farmers/me/settlements", headers=farmer_headers).json()["items"][0]
    assert original["gross_amount"] == 100_000
    assert original["status"] == "DRAFT"
    assert api.post(approval, headers=farmer_headers).status_code == 403
    response = api.post(approval, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert response.json()["paid_at"] is None
    assert api.get(path, headers=admin_headers).json()["items"][0] == response.json()


def test_password_paths_and_production_mock_otp_fail_closed(api, monkeypatch, seed_data):
    for prefix in ("/api/auth", "/api/v1/auth"):
        admin_phone = seed_data["admin_user"].phone
        for operation in ("login", "register"):
            response = api.post(f"{prefix}/{operation}", json={"phone": admin_phone, "password": "ignored"})
            assert response.status_code == 503
            assert "access_token" not in response.json()
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    response = api.post("/api/v1/auth/otp/request", json={"phone": seed_data["buyer_user"].phone})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OTP_DELIVERY_UNAVAILABLE"


def test_development_otp_verified_through_http(api, seed_data):
    response = api.post("/api/v1/auth/otp/request", json={"phone": seed_data["buyer_user"].phone})
    assert response.status_code == 200
    assert "sent" not in response.json()["message"].lower()
    challenge = response.json()
    url = "/api/v1/auth/otp/verify"
    assert api.post(url, json={"request_id": challenge["request_id"], "otp": "999999"}).status_code == 400
    verified = api.post(url, json={"request_id": challenge["request_id"], "otp": challenge["mock_otp"]})
    token = verified.json()["access_token"]
    assert api.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"}).json()["role"] == "buyer"
    assert api.post(url, json={"request_id": challenge["request_id"], "otp": challenge["mock_otp"]}).status_code == 400
    assert api.get("/openapi.json").status_code == 200
