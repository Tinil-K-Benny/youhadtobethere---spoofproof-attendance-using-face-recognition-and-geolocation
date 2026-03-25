import streamlit as st
import os
import sys

# Ensure frontend directory is on path for child pages
sys.path.insert(0, os.path.dirname(__file__))

from utils.api_client import check_api_health, login

st.set_page_config(
    page_title="FaceCheck | Login",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Dark modern theme injected via CSS
st.markdown(
    """
    <style>
    /* Sleek Background & Typography */
    .stApp {
        background-color: #0f1117;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Login Card Styling */
    .login-container {
        background-color: #1a1d27;
        padding: 2.5rem;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        border: 1px solid #2d313a;
        max-width: 400px;
        margin: auto;
    }
    
    .title-text {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        background: -webkit-linear-gradient(45deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle-text {
        text-align: center;
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

if st.session_state.user is not None:
    st.success(f"Welcome back, {st.session_state.user['name']}!")
    
    st.markdown("### Navigation Directory")
    if st.session_state.role == "admin":
        st.page_link("pages/dashboard.py", label="Dashboard")
        st.page_link("pages/register_student.py", label="Students")
        st.page_link("pages/manage_classes.py", label="Manage Classes")
    elif st.session_state.role == "student":
        st.page_link("pages/mark_attendance.py", label="Mark Attendance")
        st.page_link("pages/my_attendance.py", label="My Attendance")
        
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()
    st.stop()

st.markdown('<div class="login-container">', unsafe_allow_html=True)
st.markdown('<div class="title-text">FaceCheck</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Secure Identity & Attendance System</div>', unsafe_allow_html=True)

if not check_api_health():
    st.error("Backend API is currently offline. Please start it up.")
    st.stop()

# Role Tabs
tab_admin, tab_student = st.tabs(["Admin", "Student"])

with tab_admin:
    with st.form("admin_login"):
        st.markdown("**Admin Access**")
        admin_password = st.text_input("Password", type="password")
        submit_admin = st.form_submit_button("Sign In", use_container_width=True)
        
        if submit_admin:
            if not admin_password:
                st.warning("Please enter the admin password.")
            else:
                res, code = login("admin", "admin", admin_password)
                if code == 200 and res.get("success"):
                    st.session_state.user = res["user"]
                    st.session_state.role = "admin"
                    st.success("Authenticated successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

with tab_student:
    with st.form("student_login"):
        st.markdown("**Student Portal**")
        student_roll = st.text_input("Roll Number", placeholder="e.g. CS2024001")
        student_pass = st.text_input("Password", type="password")
        submit_student = st.form_submit_button("Sign In", use_container_width=True)
        
        if submit_student:
            if not student_roll or not student_pass:
                st.warning("Please enter both Roll Number and Password.")
            else:
                res, code = login("student", student_roll, student_pass)
                if code == 200 and res.get("success"):
                    st.session_state.user = res["user"]
                    st.session_state.role = "student"
                    st.success("Authenticated successfully!")
                    st.rerun()
                else:
                    st.error(res.get("detail", "Invalid credentials."))

st.markdown('</div>', unsafe_allow_html=True)
