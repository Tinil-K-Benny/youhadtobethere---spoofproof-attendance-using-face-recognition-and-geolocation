import streamlit as st
import sys, os
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import list_classes, mark_attendance, check_api_health

st.set_page_config(page_title="Mark Attendance | FaceCheck", layout="centered", initial_sidebar_state="expanded")

if st.session_state.get("role") != "student":
    st.error("Access Denied. Please log in as a Student.")
    st.stop()

st.markdown(
    """<style>
    .stApp { background-color: #0f1117; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    </style>""", unsafe_allow_html=True
)

st.title("Mark Attendance")
user = st.session_state.user
st.markdown(f"Student: **{user['name']}** ({user['roll_no']})")

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
    st.warning("No classes available today.")
    st.stop()

class_options = {f"{c['subject']} ({c['subject_code']}) - {c['schedule']['start_time']} to {c['schedule']['end_time']}": c["id"] for c in classes}
selected_label = st.selectbox("Select Class", list(class_options.keys()))
selected_class_id = class_options[selected_label]

st.subheader("Face Capture")
camera_image = st.camera_input("Take a snapshot")

st.subheader("Your Location")
st.info("Allow location access in your browser or enter coordinates manually.")

coords = None
try:
    from streamlit_js_eval import get_geolocation
    coords = get_geolocation()
except ImportError:
    pass

lat_val = coords.get("coords", {}).get("latitude") if isinstance(coords, dict) else None
lng_val = coords.get("coords", {}).get("longitude") if isinstance(coords, dict) else None

col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("Latitude", value=float(lat_val or 0.0), format="%.6f", step=0.000001)
with col2:
    lng = st.number_input("Longitude", value=float(lng_val or 0.0), format="%.6f", step=0.000001)

if lat_val and lng_val:
    st.success(f"GPS detected: {lat_val:.6f}, {lng_val:.6f}")
else:
    st.warning("GPS not auto-detected. Enter coordinates manually.")

st.divider()
if st.button("Submit Attendance", type="primary", use_container_width=True):
    if camera_image is None:
        st.warning("Please take a face snapshot first.")
    elif lat == 0.0 and lng == 0.0:
        st.warning("Please provide location coordinates.")
    else:
        with st.spinner("Verifying identity and location..."):
            result, status_code = mark_attendance(
                class_id=selected_class_id, lat=lat, lng=lng,
                image_bytes=camera_image.getvalue(), filename="snapshot.jpg",
            )

        success = result.get("success", False)
        status = result.get("status", "unknown")

        if success:
            if status == "present":
                st.success(f"Present! {result.get('message', '')}")
            else:
                st.warning(f"Late - {result.get('message', '')}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Student", result.get("student_name", "N/A"))
            c2.metric("Face Match", f"{result.get('face_match_score', 0):.4f}")
            c3.metric("Distance", f"{result.get('distance_from_zone_m', 0):.1f} m")
        else:
            reason = result.get("rejection_reason", "unknown")
            st.error(f"Rejected: {reason.replace('_', ' ').title()}\n\n{result.get('message', '')}")
            with st.expander("Details"):
                st.json({
                    "Reason": reason,
                    "Face Match": result.get("face_match_score"),
                    "Distance (m)": result.get("distance_from_zone_m"),
                })
