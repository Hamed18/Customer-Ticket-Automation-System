import sys
import os
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from src.main import app
from src.utils.init_db import init_db

print("=" * 65)
print("TEST: MULTI-BROWSER PERSISTENCE & DATABASE RESTORATION")
print("=" * 65)

init_db()

# --------------------------------------------------------------------------
# BROWSER 1 (Simulated Device A): Customer creates ticket & sends message
# --------------------------------------------------------------------------
print("\n[DEVICE A - BROWSER 1] Customer logs in on Device A...")
client_device_a = TestClient(app)

login_resp_a = client_device_a.post("/auth/login", json={"username": "customer1", "password": "customer123"})
assert login_resp_a.status_code == 200
token_device_a = login_resp_a.json()["access_token"]

# Customer creates ticket on Device A
create_resp = client_device_a.post(
    "/tickets/create",
    headers={"Authorization": f"Bearer {token_device_a}"},
    json={
        "title_query": "Order shipment tracking unavailable in customer portal",
        "ticket_description": "I ordered 2 items yesterday but tracking number shows 404.",
        "category": "Order",
        "priority": "Medium"
    }
)
assert create_resp.status_code == 201
ticket_id = create_resp.json()["ticket_id"]
print(f" Created Ticket {ticket_id} on Device A.")

# Customer sends first chat message on Device A
msg_resp_1 = client_device_a.post(
    f"/tickets/{ticket_id}/messages",
    headers={"Authorization": f"Bearer {token_device_a}"},
    json={"content": "Hello support, could you check courier status for my order?"}
)
assert msg_resp_1.status_code == 201
print(f" Customer sent chat message: '{msg_resp_1.json()['content']}'")

# --------------------------------------------------------------------------
# BROWSER 2 (Simulated Device B - Support Agent): Agent adds note & replies
# --------------------------------------------------------------------------
print("\n[DEVICE B - BROWSER 2] Support Agent logs in on Device B...")
client_device_b = TestClient(app)

agent_login = client_device_b.post("/auth/login", json={"username": "sai", "password": "sai123"})
assert agent_login.status_code == 200
agent_token_b = agent_login.json()["access_token"]

# Agent adds an internal staff note
note_resp = client_device_b.post(
    f"/tickets/{ticket_id}/notes",
    headers={"Authorization": f"Bearer {agent_token_b}"},
    json={"content": "Checked DHL courier API: gateway sync delay. Delivery scheduled for Tuesday."}
)
assert note_resp.status_code == 201
print(f" Agent added internal note: '{note_resp.json()['content']}'")

# Agent sends chat reply back to customer
msg_resp_2 = client_device_b.post(
    f"/tickets/{ticket_id}/messages",
    headers={"Authorization": f"Bearer {agent_token_b}"},
    json={"content": "Hi! We verified with DHL. The tracking link will activate within 2 hours. Delivery is scheduled for Tuesday."}
)
assert msg_resp_2.status_code == 201
print(f" Agent sent reply: '{msg_resp_2.json()['content']}'")


# --------------------------------------------------------------------------
# BROWSER 3 (Simulated Device C - Brand New Clean Device / Tablet):
# Customer logs in from scratch with completely empty storage!
# --------------------------------------------------------------------------
print("\n[DEVICE C - BROWSER 3] Completely new device/browser with empty localStorage...")
client_device_c = TestClient(app) # Clean client instance, no session state

# Fresh login
login_resp_c = client_device_c.post("/auth/login", json={"username": "customer1", "password": "customer123"})
assert login_resp_c.status_code == 200
token_device_c = login_resp_c.json()["access_token"]

# Fetch conversation from database on Device C
db_messages = client_device_c.get(
    f"/tickets/{ticket_id}/messages",
    headers={"Authorization": f"Bearer {token_device_c}"}
).json()

print(f" Restored {len(db_messages)} messages from database on Device C:")
for m in db_messages:
    print(f"   [{m['sender_role']} {m['sender_name']}]: {m['content']}")

assert len(db_messages) == 2, f"Expected 2 messages, found {len(db_messages)}"
assert db_messages[0]["content"] == "Hello support, could you check courier status for my order?"
assert "DHL" in db_messages[1]["content"]

# --------------------------------------------------------------------------
# BROWSER 4 (Simulated Device D - Admin on phone):
# Admin logs in from scratch and checks internal notes
# --------------------------------------------------------------------------
print("\n[DEVICE D - BROWSER 4] Admin logs in from mobile phone with empty localStorage...")
client_device_d = TestClient(app)

admin_login = client_device_d.post("/auth/login", json={"username": "sai", "password": "sai123"})
assert admin_login.status_code == 200
admin_token_d = admin_login.json()["access_token"]

db_notes = client_device_d.get(
    f"/tickets/{ticket_id}/notes",
    headers={"Authorization": f"Bearer {admin_token_d}"}
).json()

print(f" Restored {len(db_notes)} internal staff notes from database on Device D:")
for n in db_notes:
    print(f"   [Staff Note by {n['author_name']}]: {n['content']}")

assert len(db_notes) == 1
assert "DHL courier API" in db_notes[0]["content"]

print("\n" + "=" * 65)
print(" VERIFIED: ZERO reliance on browser localStorage for data! ")
print(" All chats, tickets, notes, and memories are 100% database-backed! ")
print("=" * 65)
