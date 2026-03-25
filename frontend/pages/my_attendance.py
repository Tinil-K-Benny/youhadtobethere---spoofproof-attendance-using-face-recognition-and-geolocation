import streamlit as st
import sys, os
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import get_student_attendance, check_api_health

st.set_page_config(page_title="My Attendance | FaceCheck", layout="wide", initial_sidebar_state="expanded")

if st.session_state.get("role") != "student":
    st.error("Access Denied. Please log in as a Student.")
    st.stop()

st.markdown(
    """<style>
    .stApp { background-color: #0f1117; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    div[data-testid="stMetricValue"] { color: #6366f1; font-weight: 800; }
    </style>""", unsafe_allow_html=True
)

user = st.session_state.user
st.title("My Attendance History")

if not check_api_health():
    st.error("Cannot reach FaceCheck API.")
    st.stop()

try:
    data = get_student_attendance(user["roll_no"])
    logs = data.get("logs", [])
    
    if not logs:
        st.info("No attendance records found.")
    else:
        # Calculate summary stats
        present_count = sum(1 for log in logs if log.get("status") in ("present", "late"))
        rejected_count = sum(1 for log in logs if log.get("status") == "rejected")
        total = len(logs)
        attendance_pct = (present_count / total) * 100 if total > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Sessions", total)
        col2.metric("Present / Late", present_count)
        col3.metric("Rejected", rejected_count)
        col4.metric("Overall %", f"{attendance_pct:.1f}%")
        
        st.divider()
        st.subheader("Detailed Logs")
        
        log_rows = []
        for log in logs:
            ts = log.get("timestamp", "")
            try:
                ts_fmt = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
            except Exception:
                ts_fmt = ts

            log_rows.append({
                "Class": log.get("class_id", "N/A"),
                "Timestamp": ts_fmt,
                "Status": log.get("status", "").upper(),
                "Face Match": f"{log.get('face_match_score', 0):.4f}",
                "Dist (m)": log.get("distance_from_zone_m", 0),
                "Reason": log.get("rejection_reason") or "-",
            })

        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Failed to load attendance history: {e}")
