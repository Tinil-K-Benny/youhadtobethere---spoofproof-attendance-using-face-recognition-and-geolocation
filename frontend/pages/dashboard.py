import streamlit as st
import sys, os
import pandas as pd
import plotly.express as px
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import list_classes, get_attendance_summary, get_class_attendance, check_api_health
from utils.navigation import render_sidebar

st.set_page_config(page_title="Dashboard | FaceCheck", layout="wide", initial_sidebar_state="expanded")

if st.session_state.get("role") != "admin":
    st.error("Access Denied. Please log in as Admin.")
    st.stop()

render_sidebar()

st.markdown(
    """<style>
    .stApp { background-color: #0f1117; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    div[data-testid="stMetricValue"] { color: #6366f1; font-weight: 800; }
    </style>""", unsafe_allow_html=True
)

st.title("Attendance Dashboard")

if not check_api_health():
    st.error("Cannot reach FaceCheck API.")
    st.stop()

try:
    classes_data = list_classes()
    classes = classes_data.get("classes", [])
except Exception as e:
    st.error(f"Failed to load classes: {e}")
    st.stop()

if not classes:
    st.warning("No classes found. Add classes via Manage Classes.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    selected_date = st.date_input("Select Date", value=datetime.today())
    selected_day = selected_date.strftime("%A")

day_classes = [c for c in classes if c.get("schedule", {}).get("day", "").strip().lower() == selected_day.lower()]

if not day_classes:
    st.info(f"No classes scheduled for {selected_day}, {selected_date.strftime('%B %d, %Y')}.")
    st.stop()

class_options = {
    f"{c['subject']} ({c['subject_code']}) - {c.get('schedule', {}).get('start_time', '')}": c["id"] 
    for c in day_classes
}

with col2:
    selected_label = st.selectbox("Select Class", list(class_options.keys()))
    
selected_class_id = class_options[selected_label]

tab1, tab2, tab3 = st.tabs(["Day Overview", "Class Summary", "Class Logs"])

with tab1:
    st.subheader(f"Classes for {selected_date.strftime('%B %d, %Y')} ({selected_day})")
    
    schedule_data = []
    for c in day_classes:
        sched = c.get("schedule", {})
        schedule_data.append({
            "Time": f"{sched.get('start_time')} - {sched.get('end_time')}",
            "Subject": c.get("subject"),
            "Code": c.get("subject_code"),
            "Teacher": c.get("teacher")
        })
        
    df_schedule = pd.DataFrame(schedule_data)
    if not df_schedule.empty:
        df_schedule = df_schedule.sort_values("Time")
        st.dataframe(df_schedule, use_container_width=True, hide_index=True)

with tab2:
    try:
        summary_data = get_attendance_summary(selected_class_id)
        summary = summary_data.get("summary", [])

        if not summary:
            st.info("No attendance data for this class yet.")
        else:
            df = pd.DataFrame(summary)
            col1, col2, col3, col4 = st.columns(4)
            total_students = len(df)
            avg_pct = df["attendance_percentage"].mean()
            above_threshold = (df["attendance_percentage"] >= 75).sum()
            below_threshold = total_students - above_threshold

            col1.metric("Students", total_students)
            col2.metric("Avg Attendance", f"{avg_pct:.1f}%")
            col3.metric("≥75% Attendance", above_threshold)
            col4.metric("<75% Attendance", below_threshold)

            st.divider()

            fig = px.bar(
                df.sort_values("attendance_percentage", ascending=False),
                x="roll_no", y="attendance_percentage",
                text="attendance_percentage", color="attendance_percentage",
                color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"], range_color=[0, 100],
                labels={"roll_no": "Roll No", "attendance_percentage": "Attendance %"},
                title="Attendance % per Student"
            )
            fig.add_hline(y=75, line_dash="dash", line_color="orange", annotation_text="75% threshold")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(coloraxis_showscale=False, height=420, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig, use_container_width=True)

            total_present = df["present_count"].sum()
            total_rejected = df["rejected_count"].sum()
            pie_fig = px.pie(
                values=[total_present, total_rejected], names=["Present / Late", "Rejected"],
                color_discrete_sequence=["#22c55e", "#ef4444"], title="Overall Present vs Rejected", hole=0.4
            )
            pie_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(pie_fig, use_container_width=True)

            st.subheader("Student Breakdown")
            display_df = df[["roll_no", "student_name", "present_count", "rejected_count", "total_attempts", "attendance_percentage"]].copy()
            display_df.columns = ["Roll No", "Name", "Present", "Rejected", "Total", "Attendance %"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Failed to load summary: {e}")

with tab3:
    try:
        logs_data = get_class_attendance(selected_class_id)
        logs = logs_data.get("logs", [])

        if not logs:
            st.info("No attendance logs for this class.")
        else:
            log_rows = []
            for log in logs[:50]:
                ts = log.get("timestamp", "")
                try:
                    ts_fmt = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    ts_fmt = ts

                log_rows.append({
                    "Timestamp": ts_fmt,
                    "Student": log.get("student_name", ""),
                    "Roll No": log.get("roll_no", ""),
                    "Status": log.get("status", "").upper(),
                    "Face Score": f"{log.get('face_match_score', 0):.4f}",
                    "Distance (m)": log.get("distance_from_zone_m", 0),
                    "Rejection Reason": log.get("rejection_reason") or "-",
                })

            st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Failed to load logs: {e}")
