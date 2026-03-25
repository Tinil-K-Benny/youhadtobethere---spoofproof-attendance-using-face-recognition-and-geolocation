import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import list_classes, create_class, update_class, delete_class, check_api_health
from utils.navigation import render_sidebar

st.set_page_config(page_title="Manage Classes | FaceCheck", layout="wide", initial_sidebar_state="expanded")

if st.session_state.get("role") != "admin":
    st.error("Access Denied. Please log in as Admin.")
    st.stop()

render_sidebar()

st.markdown(
    """<style>
    .stApp { background-color: #0f1117; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    </style>""", unsafe_allow_html=True
)

st.title("Manage Classes")

if not check_api_health():
    st.error("Cannot reach FaceCheck API.")
    st.stop()

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

with st.expander("Create New Class", expanded=True):
    with st.form("create_class_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject Name *")
            subject_code = st.text_input("Subject Code *")
            teacher = st.text_input("Teacher Name *")
        with col2:
            day = st.selectbox("Day of Week *", DAYS)
            start_time = st.time_input("Start Time *")
            end_time = st.time_input("End Time *")

        st.markdown("**Classroom GPS Zone**")
        col3, col4, col5 = st.columns(3)
        with col3:
            zone_lat = st.number_input("Latitude", value=0.0, format="%.6f", key="create_lat")
        with col4:
            zone_lng = st.number_input("Longitude", value=0.0, format="%.6f", key="create_lng")
        with col5:
            radius = st.number_input("Radius (meters)", min_value=10, max_value=5000, value=100, step=10)

        submitted = st.form_submit_button("Create Class", use_container_width=True, type="primary")

    if submitted:
        if not all([subject, subject_code, teacher]):
            st.warning("Please fill in subject, code, and teacher name.")
        elif start_time >= end_time:
            st.warning("Start time must be before end time.")
        else:
            payload = {
                "subject": subject,
                "subject_code": subject_code,
                "teacher": teacher,
                "schedule": {"day": day, "start_time": start_time.strftime("%H:%M"), "end_time": end_time.strftime("%H:%M")},
                "location_zone": {"lat": zone_lat, "lng": zone_lng, "radius_meters": radius},
            }
            result, code = create_class(payload)
            if code in (200, 201) and result.get("success"):
                st.success(f"Class '{subject}' created successfully!")
                st.rerun()
            else:
                st.error(result.get('detail', 'Failed to create class.'))

st.divider()
st.subheader("Existing Classes")

if st.button("Refresh"): st.rerun()

try:
    data = list_classes()
    classes = data.get("classes", [])
except Exception:
    classes = []

if not classes:
    st.info("No classes yet.")
else:
    # Group classes by day
    from collections import defaultdict
    grouped = defaultdict(list)
    for c in classes:
        day = c.get("schedule", {}).get("day", "Unknown")
        grouped[day].append(c)
        
    for day in DAYS:
        day_classes = grouped.get(day, [])
        if not day_classes:
            continue
            
        with st.expander(f"📅 {day} ({len(day_classes)} Classes)", expanded=False):
            # Sort by start time
            day_classes = sorted(day_classes, key=lambda x: x.get("schedule", {}).get("start_time", ""))
            
            for cls in day_classes:
                sched = cls.get("schedule", {})
                zone = cls.get("location_zone", {})
                
                st.markdown(f"**{cls['subject']}** - {sched.get('start_time')}-{sched.get('end_time')}")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Teacher:** {cls['teacher']} | **Code:** `{cls['subject_code']}`")
                    st.markdown(f"**Zone:** lat=`{zone.get('lat')}`, lng=`{zone.get('lng')}`, radius=`{zone.get('radius_meters')}m`")

                with col2:
                    with st.popover("Edit Zone"):
                        with st.form(f"update_form_{cls['id']}"):
                            st.markdown("**Edit Zone**")
                            new_lat = st.number_input("Latitude", value=float(zone.get("lat", 0)), format="%.6f", key=f"lat_{cls['id']}")
                            new_lng = st.number_input("Longitude", value=float(zone.get("lng", 0)), format="%.6f", key=f"lng_{cls['id']}")
                            new_radius = st.number_input("Radius (m)", value=int(zone.get("radius_meters", 100)), min_value=10, key=f"r_{cls['id']}")
                            save = st.form_submit_button("Save")

                        if save:
                            update_payload = {"location_zone": {"lat": new_lat, "lng": new_lng, "radius_meters": new_radius}}
                            res, code = update_class(cls["id"], update_payload)
                            if code == 200:
                                st.success("Zone updated!")
                                st.rerun()
                            else:
                                st.error("Update failed.")

                    if st.button("Delete", key=f"delete_{cls['id']}", type="secondary"):
                        res, code = delete_class(cls["id"])
                        if code == 200:
                            st.success("Class deleted.")
                            st.rerun()
                        else:
                            st.error("Delete failed.")
                st.divider()
