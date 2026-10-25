import sys
import os
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from src.main import app
from src.database import SessionLocal
from src.utils.init_db import init_db
from src.models.Users import User
from src.models.Tickets import Ticket
from src.models.Threads import Thread
from src.models.EpisodicMemory import EpisodicMemory
from src.services.memory_service import MemoryService
from src.services.reaper_service import TTLReaperService
from src.utils.hashing import hash_password

print("=" * 60)
print("PHASE 6 CONSOLIDATION: COMPREHENSIVE INTEGRATION TEST SUITE")
print("=" * 60)

init_db()
client = TestClient(app)
db = SessionLocal()

# -------------------------------------------------------------
# TEST 1: Episodic Memory Creation, Retrieval & Tenant Isolation
# -------------------------------------------------------------
print("\n[TEST 1] Testing Episodic Memory Isolation & Semantic Retrieval...")

# Create episodic memories for customer1 (tenant: default)
MemoryService.record_interaction(
    tenant_id="default",
    user_id="USR004",
    summary="Customer reported VPN gateway routing timeout on workstation Ubuntu 22.04.",
    memory_type="interaction"
)
MemoryService.record_interaction(
    tenant_id="default",
    user_id="USR004",
    summary="Customer prefers receiving notifications via Slack and email.",
    memory_type="preference"
)

# Create episodic memory for acme_user (tenant: tenant_acme)
MemoryService.record_interaction(
    tenant_id="tenant_acme",
    user_id="USR005",
    summary="Acme user requested Enterprise bulk billing invoice for Q3.",
    memory_type="interaction"
)

# Verify customer1 memories
cust1_mems = MemoryService.retrieve_relevant_memory(
    tenant_id="default",
    user_id="USR004",
    current_query="VPN connection issues",
    limit=5
)
assert len(cust1_mems) > 0, "Failed to retrieve memories for customer1"
assert "VPN" in cust1_mems[0], f"Expected VPN memory to rank highest, got: {cust1_mems[0]}"
print(f" Customer1 retrieved relevant memory: {cust1_mems[0]}")

# Verify cross-tenant isolation: customer1 cannot retrieve acme_user memory
cust1_acme_check = MemoryService.retrieve_relevant_memory(
    tenant_id="default",
    user_id="USR004",
    current_query="Enterprise bulk billing invoice",
    limit=5
)
for m in cust1_acme_check:
    assert "Acme" not in m and "Enterprise" not in m, f"LEAK: Customer1 saw Acme memory: {m}"
print(" Cross-tenant memory isolation confirmed! Zero memory leakage across tenants.")


# -------------------------------------------------------------
# TEST 2: Agent HITL Resolution & Episodic Memory Persistence
# -------------------------------------------------------------
print("\n[TEST 2] Testing Ticket Resolution -> Episodic Memory Auto-Capture...")

# Record approved response for a test ticket
test_ticket_id = f"TCK_TEST_{uuid.uuid4().hex[:6]}"
t = Ticket(
    ticket_id=test_ticket_id,
    tenant_id="default",
    user_id="USR004",
    username="customer1",
    title_query="Cannot checkout using Stripe payment gateway",
    status="Human Review",
    resolution_state="Open"
)
db.add(t)
db.commit()

# Record resolution
resolved_memory = MemoryService.record_ticket_resolution(
    tenant_id="default",
    user_id="USR004",
    ticket_id=test_ticket_id,
    title_query=t.title_query,
    final_response="Cleared duplicate token authorization with payment processor. Charge succeeded.",
    category="Billing"
)
assert resolved_memory.memory_id is not None
print(f" Resolution memory recorded: {resolved_memory.summary}")

# Verify it is retrieved when user asks about payment later
subsequent_mems = MemoryService.retrieve_relevant_memory(
    tenant_id="default",
    user_id="USR004",
    current_query="payment checkout issue",
    limit=1
)
assert len(subsequent_mems) > 0 and "Stripe" in subsequent_mems[0]
print(f" Subsequent inquiry recalled past resolution: {subsequent_mems[0]}")


# -------------------------------------------------------------
# TEST 3: TTL Reaper Automated Cleanup of Expired Guest Data
# -------------------------------------------------------------
print("\n[TEST 3] Testing TTL Reaper Automated Cleanup...")

now = datetime.now(timezone.utc)
past_time = now - timedelta(hours=2) # 2 hours in the past -> EXPIRED
future_time = now + timedelta(hours=24) # 24 hours in the future -> ACTIVE

# Create Expired Guest
expired_guest_id = f"GST_EXP_{uuid.uuid4().hex[:6]}"
expired_guest = User(
    user_id=expired_guest_id,
    username=f"guest_exp_{uuid.uuid4().hex[:4]}",
    fullname="Expired Guest User",
    email=f"{expired_guest_id}@temporary.guest",
    password_hash=hash_password("pwd"),
    role="Customer",
    tenant_id="default",
    is_guest=True,
    expires_at=past_time
)
db.add(expired_guest)

# Create Active Guest
active_guest_id = f"GST_ACT_{uuid.uuid4().hex[:6]}"
active_guest = User(
    user_id=active_guest_id,
    username=f"guest_act_{uuid.uuid4().hex[:4]}",
    fullname="Active Guest User",
    email=f"{active_guest_id}@temporary.guest",
    password_hash=hash_password("pwd"),
    role="Customer",
    tenant_id="default",
    is_guest=True,
    expires_at=future_time
)
db.add(active_guest)
db.commit()

# Attach ticket & episodic memory to expired guest
exp_ticket_id = f"TCK_GEXP_{uuid.uuid4().hex[:4]}"
exp_ticket = Ticket(
    ticket_id=exp_ticket_id,
    tenant_id="default",
    user_id=expired_guest_id,
    username=expired_guest.username,
    title_query="Temporary guest issue",
    status="AI Processing"
)
db.add(exp_ticket)
db.commit()

MemoryService.record_interaction(
    tenant_id="default",
    user_id=expired_guest_id,
    summary="Temporary guest inquiry regarding guest refund policy.",
    ticket_id=exp_ticket_id
)

print(f" Created expired guest ({expired_guest_id}) with ticket & memory, and active guest ({active_guest_id})")

# Run TTL Reaper Sweep
sweep_report = TTLReaperService.run_sweep(db)
print(f" TTL Reaper Report: {sweep_report}")

assert expired_guest_id in sweep_report["purged_user_ids"], "Expired guest was not purged!"
assert active_guest_id not in sweep_report["purged_user_ids"], "Active guest was incorrectly purged!"

# Verify expired guest is deleted from DB
check_guest = db.query(User).filter(User.user_id == expired_guest_id).first()
assert check_guest is None, "Expired guest still exists in users table!"

# Verify expired guest tickets & memories are deleted
check_ticket = db.query(Ticket).filter(Ticket.ticket_id == exp_ticket_id).first()
assert check_ticket is None, "Expired guest ticket still exists in tickets table!"

check_mem = db.query(EpisodicMemory).filter(EpisodicMemory.user_id == expired_guest_id).first()
assert check_mem is None, "Expired guest episodic memory still exists!"

# Verify permanent users and active guests remain intact
check_active = db.query(User).filter(User.user_id == active_guest_id).first()
assert check_active is not None, "Active guest was deleted!"

check_permanent = db.query(User).filter(User.username == "sai").first()
assert check_permanent is not None, "Permanent user was deleted!"
print(" TTL Reaper sweep fully verified: cascaded cleanup purged all expired guest data, keeping active & permanent accounts safe.")


# -------------------------------------------------------------
# TEST 4: API Endpoint Integration (Reaper Trigger & Memories API)
# -------------------------------------------------------------
print("\n[TEST 4] Testing API Endpoints for Memories & Reaper...")

# Agent login
login_resp = client.post("/auth/login", json={"username": "sai", "password": "sai123"})
assert login_resp.status_code == 200
agent_token = login_resp.json()["access_token"]

# Memories endpoint
mem_resp = client.get("/memories/", headers={"Authorization": f"Bearer {agent_token}"})
assert mem_resp.status_code == 200
print(f" GET /memories/ returned {len(mem_resp.json())} memories for current tenant.")

# Reaper trigger endpoint
reaper_resp = client.post("/reaper/trigger", headers={"Authorization": f"Bearer {agent_token}"})
assert reaper_resp.status_code == 200
reaper_data = reaper_resp.json()
assert "swept_guests" in reaper_data
print(f" POST /reaper/trigger success: {reaper_data}")

# Customer cannot trigger reaper (Forbidden 403)
cust_login = client.post("/auth/login", json={"username": "customer1", "password": "customer123"}).json()
cust_token = cust_login["access_token"]
unauth_reaper = client.post("/reaper/trigger", headers={"Authorization": f"Bearer {cust_token}"})
assert unauth_reaper.status_code == 403, f"Expected 403 Forbidden, got {unauth_reaper.status_code}"
print(" Role security confirmed: Customers are forbidden from invoking TTL Reaper (403).")


# -------------------------------------------------------------
# TEST 5: Cross-Tenant Ticket Access Penetration Test
# -------------------------------------------------------------
print("\n[TEST 5] Testing Cross-Tenant Direct Ticket Access Penetration...")

# acme_user logs in
acme_login = client.post("/auth/login", json={"username": "acme_user", "password": "acme123"}).json()
acme_token = acme_login["access_token"]

# acme_user attempts to fetch customer1's ticket in tenant 'default'
leak_attempt = client.get(f"/tickets/{test_ticket_id}", headers={"Authorization": f"Bearer {acme_token}"})
assert leak_attempt.status_code == 404, f"Expected 404 access denied, got {leak_attempt.status_code}"
print(" Cross-tenant penetration blocked: Tenant 'tenant_acme' cannot access 'default' tenant tickets.")

print("\n" + "=" * 60)
print(" ALL PHASES (1, 2, 3, 4, 5, 6) CONSOLIDATION TESTS PASSED 100%! ")
print("=" * 60)

db.close()
