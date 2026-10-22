import os
import requests
import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")

def init_session():
    """Initialize Streamlit session state keys."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "token" not in st.session_state:
        st.session_state.token = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None


def login():
    """Render the login card and authenticate with FastAPI backend."""
    st.set_page_config(
        page_title="AI Ticket Ops",
        page_icon="🎫",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.markdown("""
    <style>
    .main-title{
        text-align:center;
        font-size:42px;
        font-weight:700;
        color:#6C63FF;
        margin-bottom:10px;
    }
    .signin-text{
        text-align:center;
        color:#94a3b8;
        margin-bottom:20px;
        font-size:18px;
        font-weight:500;
    }
    .login-box{
        max-width:450px;
        margin:auto;
        margin-top:40px;
    }
    .stButton button{
        background:linear-gradient(90deg,#6C63FF,#8E7CFF);
        color:white;
        border:none;
        border-radius:10px;
        height:45px;
        font-size:16px;
        font-weight:600;
        width: 100%;
    }
    .stButton button:hover{
        background:linear-gradient(90deg,#5A52E0,#7A6BFF);
        color:white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">🎫 AI Ticket Ops</div>', unsafe_allow_html=True)
    st.markdown('<div class="signin-text">Sign in to manage and review support tickets</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1, 1.2])
    with col2:
        with st.container(border=True):
            username = st.text_input("Username", placeholder="e.g. sai")
            password = st.text_input("Password", type="password", placeholder="Enter your password")

            if st.button("Sign In", use_container_width=True):
                if not username or not password:
                    st.warning("Please provide both username and password")
                    return

                with st.spinner("Authenticating..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/auth/login",
                            data={
                                "username": username,
                                "password": password
                            },
                            timeout=10
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.logged_in = True
                            st.session_state.token = data["access_token"]
                            st.session_state.username = data.get("username", username)
                            st.session_state.user_id = data.get("user_id", "")
                            st.success("Authenticated successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please verify your username and password.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Cannot connect to backend server at {API_URL}. Ensure the API is running.")

            st.markdown("<div style='text-align: center; margin-top: 15px;'><small>Made with ❤️ by <a href='https://www.linkedin.com/in/devhamed/' target='_blank' style='color: #6C63FF; text-decoration: none; font-weight: 600;'>Hamed</a></small></div>", unsafe_allow_html=True)


def get_tickets_data(token: str) -> list:
    """Fetch tickets list from backend API."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/tickets/", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.session_state.logged_in = False
            st.warning("Session expired. Please log in again.")
            st.rerun()
            return []
        else:
            st.error(f"Failed to fetch tickets: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Network error while connecting to backend API: {e}")
        return []


def edit_response(token: str, ticket_id: str, final_response: str, userid: str, username: str) -> bool:
    """Resume and resolve an interrupted ticket thread via the backend API."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        thread_resp = requests.get(
            f"{API_URL}/threads/thread",
            params={"ticket_id": ticket_id},
            headers=headers,
            timeout=10
        )
        if thread_resp.status_code != 200:
            st.error(f"Could not locate active thread for ticket {ticket_id}")
            return False

        thread_data = thread_resp.json()
        thread_id = thread_data["thread_id"]

        resume_resp = requests.post(
            f"{API_URL}/agent/resume",
            json={
                "thread_id": thread_id,
                "final_response": final_response,
                "ticket_id": ticket_id,
                "user_id": userid,
                "username": username,
                "token": token
            },
            headers=headers,
            timeout=15
        )

        return resume_resp.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Network error communicating with agent service: {e}")
        return False


def get_resolved_ticket_details(row: Dict[str, Any]) -> pd.DataFrame:
    """Format ticket dictionary for table display."""
    data = {
        "Ticket ID": row.get("ticket_id"),
        "User": f"{row.get('username')} ({row.get('user_id')})",
        "Category": row.get("category"),
        "Query": row.get("title_query"),
        "Description": row.get("ticket_description"),
        "Status": row.get("status"),
        "Priority": row.get("priority"),
        "Intent": row.get("intent"),
        "Resolution State": row.get("resolution_state"),
        "Resolved By": row.get("resolved_by"),
        "AI Confidence": f"{row.get('ai_confidence')}%" if row.get("ai_confidence") is not None else "N/A",
        "Created At": str(row.get("created_at")),
    }
    return pd.DataFrame(data.items(), columns=["Key", "Value"])
