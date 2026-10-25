import streamlit as st
import difflib
from src.ui_utils import get_resolved_ticket_details, edit_response

if not st.session_state.get("logged_in"):
    st.switch_page("pages/home.py")

st.markdown("""
<style>
.chat-user {
    background: #2563eb;
    color: white;
    padding: 14px 16px;
    border-radius: 18px 18px 4px 18px;
    margin-left: auto;
    width: fit-content;
    max-width: 75%;
    margin-bottom: 16px;
}
.chat-ai {
    background: #1e293b;
    color: #f1f5f9;
    padding: 14px 16px;
    border-radius: 18px 18px 18px 4px;
    width: fit-content;
    max-width: 75%;
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.08);
}
.chat-label {
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 6px;
    opacity: 0.8;
}
.section-card {
    background: #1e293b;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 16px;
    line-height: 1.6;
    color: #f1f5f9;
}
.timeline-item {
    background: #1e293b;
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 4px solid #8b5cf6;
    padding: 12px 14px;
    border-radius: 10px;
    margin-bottom: 12px;
    font-size: 14px;
    color: #f1f5f9;
}
.retrieved-item {
    background: #1e293b;
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 4px solid #06b6d4;
    padding: 12px 14px;
    border-radius: 10px;
    margin-bottom: 12px;
    font-size: 14px;
    color: #f1f5f9;
}
section[data-testid="stSidebar"] {
    background: #111827;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Ticket Details", page_icon="🔍", layout="wide")
with st.sidebar:
    st.caption("Made with :material/favorite: by [Hamed](https://www.linkedin.com/in/devhamed/)")

ticket = st.session_state.get("selected_ticket", None)
if ticket is None:
    st.warning("Please select a ticket from View Tickets to see its details.")
    st.stop()

top_left, top_right = st.columns([6, 2])
with top_left:
    st.markdown(f"## 🔍 Ticket {ticket['ticket_id']}")
with top_right:
    st.info(f"Status: **{ticket.get('status', 'Unknown')}**")


def show_human_review_ui(ticket):
    data = get_resolved_ticket_details(ticket)
    st.subheader("🎫 Ticket Details")
    st.dataframe(data, use_container_width=True, hide_index=True)

    with st.expander("💬 Conversation Context", expanded=True):
        st.markdown(
            f"""
            <div class="chat-user">
                <div class="chat-label">👤 User Query</div>
                {ticket.get('title_query', '')}
            </div>
            """,
            unsafe_allow_html=True
        )
        ai_resp = ticket.get('ai_response') or "No draft response generated."
        st.markdown(
            f"""
            <div class="chat-ai">
                <div class="chat-label">🤖 AI Proposed Draft</div>
                {ai_resp}
            </div>
            """,
            unsafe_allow_html=True
        )

    retriever_docs = ticket.get("retrieved_documents") or []
    if retriever_docs:
        with st.expander("📄 Retrieved Knowledge Sources"):
            for step in retriever_docs:
                st.markdown(f"<div class='retrieved-item'>📗 {step}</div>", unsafe_allow_html=True)

    confidence = ticket.get("ai_confidence") or 0.0
    st.markdown("### 🤖 AI Evaluation Confidence")
    st.progress(min(int(confidence), 100))
    st.caption(f"{int(confidence)}% confidence score")

    st.divider()
    st.subheader("✏️ Review & Edit Response")
    initial_draft = ticket.get("ai_response") or ""
    edited_response = st.text_area(
        "Response Content",
        value=initial_draft,
        height=180,
        label_visibility="collapsed"
    )

    if edited_response != initial_draft and initial_draft:
        st.markdown("#### 🔍 Changes Diff")
        diff = difflib.ndiff(initial_draft.split(), edited_response.split())
        diff_html = ""
        for word in diff:
            if word.startswith("- "):
                diff_html += f"<span style='color:#ef4444;text-decoration:line-through'>{word[2:]} </span>"
            elif word.startswith("+ "):
                diff_html += f"<span style='color:#22c55e;font-weight:600'>{word[2:]} </span>"
            else:
                diff_html += f"{word[2:]} "
        st.markdown(diff_html, unsafe_allow_html=True)

    token, ticket_id = st.session_state.token, ticket["ticket_id"]
    userid = ticket.get("user_id", "")
    username = ticket.get("username", "")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ Edit & Approve", use_container_width=True):
            success = edit_response(token, ticket_id, edited_response, userid, username)
            if success:
                st.success("Edited response successfully approved and resolved!")
                st.switch_page("pages/view_tickets.py")
            else:
                st.error("Failed to approve response. Please try again.")

    with col2:
        if st.button("✅ Approve As-Is", type="primary", use_container_width=True):
            success = edit_response(token, ticket_id, initial_draft, userid, username)
            if success:
                st.success("Draft response approved and ticket resolved!")
                st.switch_page("pages/view_tickets.py")
            else:
                st.error("Failed to approve response. Please try again.")


def show_resolved_ui(ticket):
    st.success("✅ Ticket Successfully Resolved")
    data = get_resolved_ticket_details(ticket)
    st.subheader("🎫 Ticket Details")
    st.dataframe(data, use_container_width=True, hide_index=True)

    st.subheader("🧾 User Query")
    st.info(ticket.get("title_query", ""))

    st.subheader("📩 Final Delivered Response")
    final_text = ticket.get("final_response") or ticket.get("ai_response") or "Ticket marked resolved."
    st.markdown(f'<div class="section-card">{final_text}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Resolved By", ticket.get("resolved_by", "AI"))
    with col2:
        resolved_at = ticket.get("created_at", "N/A")
        st.metric("Timestamp", str(resolved_at)[:19])

    retriever_docs = ticket.get("retrieved_documents") or []
    if retriever_docs:
        st.subheader("📄 Knowledge Sources Used")
        for step in retriever_docs:
            st.markdown(f"<div class='retrieved-item'>📗 {step}</div>", unsafe_allow_html=True)


def show_processing_ui(ticket):
    st.markdown('<div class="section-card">🤖 AI Agent is currently analyzing and processing this ticket.</div>', unsafe_allow_html=True)
    data = get_resolved_ticket_details(ticket)
    st.subheader("🎫 Ticket Details")
    st.dataframe(data, use_container_width=True, hide_index=True)

    st.subheader("⚙️ Processing Pipeline")
    st.progress(70)
    steps = [
        "✔ Intent Classified",
        "✔ Retrieved Knowledge Base",
        "⏳ Generating Response",
        "⬜ Awaiting Completion"
    ]
    for step in steps:
        st.markdown(f"<div class='timeline-item'>{step}</div>", unsafe_allow_html=True)


def show_manual_ui(ticket):
    st.error("🔥 Escalated for Manual Handling")
    data = get_resolved_ticket_details(ticket)
    st.subheader("🎫 Ticket Details")
    st.dataframe(data, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧾 Ticket Query")
        st.info(ticket.get("title_query", ""))
    with col2:
        st.subheader("⚠ Escalation Reason")
        st.warning("High/Critical urgency flagged by classifier for direct human agent investigation.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Urgency", ticket.get("priority", "High"))
    c2.metric("Handling", "Manual Human Assignment")
    c3.metric("SLA Tier", "Tier 1 Priority")


# Dynamic UI dispatch
status = ticket.get("status")
if status == "Human Review":
    show_human_review_ui(ticket)
elif status == "Resolved":
    show_resolved_ui(ticket)
elif status == "AI Processing":
    show_processing_ui(ticket)
elif status == "Manual Handling":
    show_manual_ui(ticket)
else:
    show_human_review_ui(ticket)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("⬅️ Back to Tickets"):
    st.switch_page("pages/view_tickets.py")
