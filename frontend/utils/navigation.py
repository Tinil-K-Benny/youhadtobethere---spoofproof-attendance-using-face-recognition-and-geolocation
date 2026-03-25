import streamlit as st

def render_sidebar():
    """
    Hides the default Streamlit sidebar page navigation and dynamically renders 
    a custom sidebar based on the authenticated user's role.
    """
    # Hide the default Streamlit sidebar menu so users can't see all pages
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("user") is None or st.session_state.get("role") is None:
        return

    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.user['name'].split()[0]}")
        st.divider()

        if st.session_state.role == "admin":
            st.markdown("**Admin Menu**")
            st.page_link("pages/dashboard.py", label="Dashboard")
            st.page_link("pages/register_student.py", label="Students")
            st.page_link("pages/manage_classes.py", label="Manage Classes")
        elif st.session_state.role == "student":
            st.markdown("**Student Menu**")
            st.page_link("pages/mark_attendance.py", label="Mark Attendance")
            st.page_link("pages/my_attendance.py", label="My Attendance")

        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()
