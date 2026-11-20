"""
Automated End-to-End Verification of Registration and Password Authentication
Tests all 4 roles: Farmer, Buyer, Driver, Admin
Verifies:
1. Account creation with custom password for every role
2. Password properly hashed with Bcrypt (salt rounds 10) in the database
3. Immediate rejection (HTTP 401) on wrong passwords
4. Strict enforcement: no backdoor / no unauthorized access
5. Immediate approval & JWT token generation on correct custom password
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connection import SessionLocal
from database.models import User, Farmer, Buyer, Driver
from database.auth_utils import verify_password
from fastapi import HTTPException
from services.api.main import register_user, login_with_password, RegisterPayload, LoginPayload


def run_tests():
    db = SessionLocal()
    print("=" * 75)
    print("  KRISHILINK AUTHENTICATION & DATABASE VERIFICATION TEST SUITE")
    print("=" * 75)

    test_cases = [
        {
            "role": "farmer",
            "name": "Basavaraj Bommanahalli",
            "phone": "+919900112233",
            "password": "GreenField@2026",
            "village": "Channarayapatna",
            "taluk": "Devanahalli",
            "land_acres": 3.5,
            "min_threshold_kg": 30.0,
        },
        {
            "role": "buyer",
            "name": "Udupi Sagar Deluxe",
            "phone": "+919900445566",
            "password": "SagarDosa#2026",
            "business_name": "Udupi Sagar Deluxe",
            "business_type": "Restaurant & Catering",
        },
        {
            "role": "driver",
            "name": "Manju Pilot",
            "phone": "+919900778899",
            "password": "DriveSafe@2026",
            "licence_no": "KA04-2022-9988776",
            "vehicle_reg": "KA-04-E-5544",
        },
        {
            "role": "admin",
            "name": "Pooja Hegde",
            "phone": "+919900123987",
            "password": "TowerOps#2026",
            "employee_id": "KL-ADM-99",
        },
    ]

    for tc in test_cases:
        role_upper = tc["role"].upper()
        # Clean up prior test runs if any
        old_u = db.query(User).filter(User.phone == tc["phone"]).first()
        if old_u:
            db.query(Farmer).filter(Farmer.user_id == old_u.id).delete()
            db.query(Buyer).filter(Buyer.user_id == old_u.id).delete()
            db.query(Driver).filter(Driver.user_id == old_u.id).delete()
            db.delete(old_u)
            db.commit()

        # 1. Register with custom password
        payload = RegisterPayload(**tc)
        res = register_user(payload, db=db)
        user_id = res["user"]["id"]
        print(f"\n[OK] Registered {role_upper} Account: {user_id} ({tc['name']}, {tc['phone']})")

        # 2. Verify stored password is a valid Bcrypt hash
        user_row = db.query(User).filter(User.id == user_id).first()
        assert user_row is not None, "User must exist in database"
        assert user_row.password_hash.startswith("$2b$10$"), f"Hash must be bcrypt salt 10, got {user_row.password_hash[:10]}"
        print(f"  -> Database Bcrypt Hash: {user_row.password_hash[:25]}... (STORED SECURELY)")

        # 3. Verify bcrypt check
        assert verify_password(tc["password"], user_row.password_hash), "Password must match"
        assert not verify_password("WrongPass123", user_row.password_hash), "Wrong password must fail"
        assert not verify_password("123456", user_row.password_hash), "Demo default must fail on custom password"
        print("  -> Cryptographic verification passed: matching password is valid, incorrect is rejected")

        # 4. Attempt login with wrong password -> expect HTTP 401
        wrong_attempt_passed = False
        try:
            login_with_password(LoginPayload(phone=tc["phone"], password="TotallyWrongPassword"), db=db)
            wrong_attempt_passed = True
        except HTTPException as e:
            assert e.status_code == 401, f"Expected 401, got {e.status_code}"
            print("  -> Security check passed: Incorrect password correctly rejected (401 Unauthorized)")
        assert not wrong_attempt_passed, "Security flaw: Wrong password was accepted!"

        # 5. Attempt login with correct custom password -> expect success & JWT
        login_res = login_with_password(LoginPayload(phone=tc["phone"], password=tc["password"]), db=db)
        assert login_res["access_token"] is not None
        assert login_res["user"]["role"] == tc["role"]
        print(f"  -> Sign In check passed: Access granted for {login_res['user']['name']} with JWT token")

    db.close()
    print("\n" + "=" * 75)
    print("  ALL 4 ROLES PASSED: 100% SECURE PASSWORD CREATION & VERIFICATION!")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
