from src.models.Users import User
from src.models.Tickets import Ticket
from src.models.Threads import Thread
from src.utils.hashing import hash_password
from datetime import datetime, timedelta, timezone
import random

def seed_users(db):
    users = [
        User(
            user_id="USR001",
            username="sai",
            fullname="Hamed",
            email="sai@mail.com",
            password_hash=hash_password("sai123"),
            mobile_number="9876543210",
            role="Lead Support Agent",
            tenant_id="default",
            is_guest=False
        ),
        User(
            user_id="USR002",
            username="ramya",
            fullname="Ramya",
            email="ramya@mail.com",
            password_hash=hash_password("ramya123"),
            mobile_number="9876543211",
            role="Support Specialist",
            tenant_id="default",
            is_guest=False
        ),
        User(
            user_id="USR003",
            username="sandy",
            fullname="Sandy",
            email="sandy@mail.com",
            password_hash=hash_password("sandy123"),
            mobile_number="9876543212",
            role="Tier 2 Support",
            tenant_id="default",
            is_guest=False
        ),
        User(
            user_id="USR004",
            username="customer1",
            fullname="John Customer",
            email="customer1@mail.com",
            password_hash=hash_password("customer123"),
            mobile_number="9876543213",
            role="Customer",
            tenant_id="default",
            is_guest=False
        ),
        User(
            user_id="USR005",
            username="acme_user",
            fullname="Acme Employee",
            email="acme@corp.com",
            password_hash=hash_password("acme123"),
            mobile_number="9876543214",
            role="Customer",
            tenant_id="tenant_acme",
            is_guest=False
        )
    ]

    for u in users:
        existing = db.query(User).filter(User.username == u.username).first()
        if not existing:
            db.add(u)
        else:
            existing.role = u.role
            existing.tenant_id = u.tenant_id
            existing.is_guest = u.is_guest
    db.commit()
    print("Users seeded/updated successfully")

def seed_tickets(db):
    users = [
        ("USR001", "sai", "default"),
        ("USR002", "ramya", "default"),
        ("USR003", "sandy", "default"),
        ("USR004", "customer1", "default"),
        ("USR005", "acme_user", "tenant_acme"),
    ]

    categories = [
        ("Refund", "Refund Request"),
        ("Billing", "Billing Issue"),
        ("Technical", "Technical Support"),
        ("Order", "Order Issue"),
        ("Login", "Login Issue"),
    ]

    sample_documents = [
        "Password reset troubleshooting guide",
        "Refund policy document",
        "Billing FAQ document",
        "Order cancellation guide",
        "Account security guide"
    ]

    ticket_counter = 1
    thread_counter = 1
    now = datetime.now(timezone.utc)

    tickets_to_add = []
    threads_to_add = []

    for user_id, username, tenant_id in users:
        for _ in range(3):
            ticket_id = f"TCK{ticket_counter:04d}"
            ticket_counter += 1

            category, intent = random.choice(categories)
            priority = random.choice(["Low", "Medium", "High"])

            created_time = now - timedelta(
                days=random.randint(0, 10),
                hours=random.randint(1, 23)
            )

            scenario = random.choice([
                "Resolved",
                "AI Processing",
                "Human Review",
                "Manual Handling"
            ])

            ai_confidence = round(random.uniform(55, 98), 1)

            if scenario == "Resolved":
                status = "Resolved"
                resolution_state = "Closed"
                resolved_by = random.choice(["AI", "AI+Human", "Human"])
                retrieved_documents = random.sample(sample_documents, k=random.randint(2, 3)) if resolved_by in ["AI", "AI+Human"] else None
                ai_response = f"AI generated response for {category.lower()} issue."
                final_response = f"{category} issue resolved successfully."
            elif scenario == "AI Processing":
                status = "AI Processing"
                resolution_state = "Pending"
                resolved_by = None
                retrieved_documents = None
                ai_response = f"AI is currently processing the {category.lower()} issue."
                final_response = None
            elif scenario == "Human Review":
                status = "Human Review"
                resolution_state = "Pending"
                resolved_by = None
                retrieved_documents = random.sample(sample_documents, k=random.randint(2, 3))
                ai_response = f"AI drafted response for {category.lower()} issue requiring human approval."
                final_response = None
            else:
                status = "Manual Handling"
                resolution_state = "Open"
                resolved_by = "Human"
                retrieved_documents = None
                ai_response = None
                final_response = None

            ticket = Ticket(
                ticket_id=ticket_id,
                tenant_id=tenant_id,
                user_id=user_id,
                username=username,
                category=category,
                title_query=f"{category} issue reported",
                ticket_description=f"Customer reported a {category.lower()} related issue.",
                status=status,
                created_at=created_time,
                intent=intent,
                priority=priority,
                ai_response=ai_response,
                ai_confidence=ai_confidence,
                retrieved_documents=retrieved_documents,
                final_response=final_response,
                resolution_state=resolution_state,
                resolved_by=resolved_by
            )
            tickets_to_add.append(ticket)

            if scenario in ["Human Review", "Manual Handling"]:
                thread = Thread(
                    thread_id=f"THR{thread_counter:03d}",
                    tenant_id=tenant_id,
                    ticket_id=ticket_id,
                    current_node="human_review",
                    current_state={
                        "intent": intent,
                        "priority": priority,
                        "draft_response": ai_response,
                        "confidence": ai_confidence
                    },
                    status="Running" if scenario == "Manual Handling" else "Completed",
                    interrupt_reason="Low confidence flagged for review" if scenario == "Human Review" else "High urgency routing",
                    last_run_at=created_time
                )
                threads_to_add.append(thread)
                thread_counter += 1

    db.add_all(tickets_to_add)
    db.add_all(threads_to_add)
    db.commit()
    print("Tickets & threads seeded successfully")
