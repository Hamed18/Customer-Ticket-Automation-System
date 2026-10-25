import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from src.main import app
from src.utils.init_db import init_db

print("Initializing DB...")
init_db()

client = TestClient(app)

print("\n--- 1. Testing Login for Seeded Users ---")
for uname, pwd in [("sai", "sai123"), ("ramya", "ramya123"), ("customer1", "customer123"), ("acme_user", "acme123")]:
    resp = client.post("/auth/login", json={"username": uname, "password": pwd})
    assert resp.status_code == 200, f"Failed login for {uname}: {resp.text}"
    data = resp.json()
    print(f"Login success: {data['username']} | Role: {data['role']} | Tenant: {data['tenant_id']}")

print("\n--- 2. Testing User Registration ---")
import uuid
unique_user = f"user_{uuid.uuid4().hex[:6]}"
reg_payload = {
    "username": unique_user,
    "fullname": "Corporate User",
    "email": f"{unique_user}@enterprise.io",
    "password": "corpPassword123!",
    "role": "Customer",
    "tenant_id": "tenant_enterprise"
}
resp = client.post("/auth/register", json=reg_payload)
assert resp.status_code == 201, f"Register failed: {resp.text}"
corp_token = resp.json()["access_token"]
print("Registration success: new_corp_user registered in tenant_enterprise")

print("\n--- 3. Testing Guest Session Creation (TTL Enabled) ---")
guest_resp = client.post("/auth/guest", json={"fullname": "Anonymous Visitor", "tenant_id": "default"})
assert guest_resp.status_code == 200, f"Guest session failed: {guest_resp.text}"
guest_data = guest_resp.json()
guest_token = guest_data["access_token"]
print(f"Guest session created: {guest_data['username']} | is_guest={guest_data['is_guest']}")

print("\n--- 4. Testing Identity Verification (/auth/me) ---")
me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {guest_token}"})
assert me_resp.status_code == 200
print(f"/auth/me verified: {me_resp.json()['username']} | Guest: {me_resp.json()['is_guest']}")

print("\n--- 5. Testing Multi-Tenant & User Isolation ---")
# Login as acme_user (tenant: tenant_acme)
acme_token = client.post("/auth/login", json={"username": "acme_user", "password": "acme123"}).json()["access_token"]
acme_tickets = client.get("/tickets/", headers={"Authorization": f"Bearer {acme_token}"}).json()
print(f"acme_user (tenant_acme) sees {len(acme_tickets)} tickets (all must have tenant_id == 'tenant_acme')")
for t in acme_tickets:
    assert t["tenant_id"] == "tenant_acme", f"LEAK! Ticket {t['ticket_id']} has tenant {t['tenant_id']}"

# Login as customer1 (tenant: default)
cust_token = client.post("/auth/login", json={"username": "customer1", "password": "customer123"}).json()["access_token"]
cust_tickets = client.get("/tickets/", headers={"Authorization": f"Bearer {cust_token}"}).json()
print(f"customer1 (default) sees {len(cust_tickets)} tickets (all must have user_id == customer1's user_id and tenant_id == 'default')")
for t in cust_tickets:
    assert t["tenant_id"] == "default", f"LEAK! Ticket {t['ticket_id']} has tenant {t['tenant_id']}"
    assert t["username"] == "customer1", f"LEAK! Ticket {t['ticket_id']} belongs to {t['username']}"

# Lead Support Agent (sai) in tenant 'default' can view all tickets in tenant 'default'
sai_token = client.post("/auth/login", json={"username": "sai", "password": "sai123"}).json()["access_token"]
sai_tickets = client.get("/tickets/", headers={"Authorization": f"Bearer {sai_token}"}).json()
print(f"Lead Support Agent sai sees {len(sai_tickets)} tickets in tenant 'default'")
for t in sai_tickets:
    assert t["tenant_id"] == "default", f"LEAK! Agent saw non-default tenant ticket {t['tenant_id']}"

print("\n--- 6. Testing Logout & Token Revocation ---")
logout_resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {cust_token}"})
assert logout_resp.status_code == 200
# Attempt to use revoked token
expired_try = client.get("/auth/me", headers={"Authorization": f"Bearer {cust_token}"})
assert expired_try.status_code == 401, f"Expected 401 for revoked token, got {expired_try.status_code}"
print("Logout and token revocation verified successfully! Revoked token blocked with 401.")

print("\n ALL AUTH & MULTI-TENANT ISOLATION TESTS PASSED PERFECTLY! ")
