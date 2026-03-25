import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import register_student, list_students, delete_student, check_api_health

st.set_page_config(page_title="Students | FaceCheck", layout="centered", initial_sidebar_state="expanded")

if st.session_state.get("role") != "admin":
    st.error("Access Denied. Please log in as Admin.")
    st.stop()

st.markdown(
    """<style>
    .stApp { background-color: #0f1117; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    </style>""", unsafe_allow_html=True
)

st.title("Student Directory")
st.markdown("Add a new student and enroll their face for recognition.")

if not check_api_health():
    st.error("Cannot reach FaceCheck API.")
    st.stop()

with st.form("register_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", placeholder="Alice Johnson")
        roll_no = st.text_input("Roll Number *", placeholder="CS2024001")
    with col2:
        email = st.text_input("Email *", placeholder="student@college.edu")
        password = st.text_input("Initial Password *", type="password", placeholder="Secret123")

    photo = st.file_uploader("Face Photo *", type=["jpg", "jpeg", "png"])
    if photo:
        st.image(photo, caption="Preview", width=220)

    submitted = st.form_submit_button("Register Student", use_container_width=True, type="primary")

if submitted:
    if not all([name, roll_no, email, password, photo]):
        st.warning("Please fill in all fields and upload a photo.")
    else:
        with st.spinner("Registering student..."):
            result, status_code = register_student(
                name=name, roll_no=roll_no, email=email, password=password,
                photo_bytes=photo.read(), filename=photo.name
            )

        if status_code == 201 and result.get("success"):
            st.success(result['message'])
        else:
            st.error(result.get('detail', 'Registration failed.'))

st.divider()
st.subheader("Registered Students")

if st.button("Refresh List"):
    st.rerun()

try:
    data = list_students()
    students = data.get("students", [])

    if not students:
        st.info("No students registered yet.")
    else:
        for s in students:
            with st.expander(f"{s['name']} - {s['roll_no']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Email:** {s.get('email', '-')}")
                    st.write(f"**Registered:** {s.get('registered_at', '-')}")
                with col2:
                    if st.button("Delete", key=f"del_{s['roll_no']}"):
                        res, code = delete_student(s["roll_no"])
                        if code == 200:
                            st.success("Deleted.")
                            st.rerun()
                        else:
                            st.error(res.get("detail", "Delete failed."))
except Exception as e:
    st.error(f"Failed to load students: {e}")
