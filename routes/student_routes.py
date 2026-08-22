from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from urllib.parse import urlencode
from services.event_service import EventService
from services.attendance_service import AttendanceService

student_bp = Blueprint("student", __name__)


@student_bp.route("/checkin/<event_id>")
def checkin_page(event_id: str):
    """
    Student scan landing page.
    Triggered when the student scans the dynamic QR code with their mobile device.
    """
    token = request.args.get("token", "")
    event = EventService.get_event_by_id(event_id)
    return render_template(
        "student/checkin.html",
        event=event,
        token=token,
        event_id=event_id
    )


@student_bp.route("/api/attendance/submit", methods=["POST"])
def submit_attendance_api():
    """
    Receives student attendance submission and executes the 5-layer verification pipeline.
    """
    data = request.get_json(silent=True) or request.form.to_dict()

    event_id = data.get("event_id", "").strip()
    token = data.get("token", "").strip()
    student_name = data.get("student_name", "").strip()
    student_id = data.get("student_id", "").strip()
    student_lat = data.get("student_lat")
    student_lon = data.get("student_lon")
    accuracy = data.get("accuracy", 0.0)

    # Capture client device metadata
    user_agent = request.headers.get("User-Agent", "Unknown")
    ip_address = request.remote_addr

    success, message, record, meta = AttendanceService.process_attendance_submission(
        event_id=event_id,
        token=token,
        student_id=student_id,
        student_name=student_name,
        student_lat=student_lat,
        student_lon=student_lon,
        accuracy=float(accuracy or 0.0),
        user_agent=user_agent,
        ip_address=ip_address
    )

    event = EventService.get_event_by_id(event_id)
    event_title = event.title if event else "College Event"

    # Determine status code and query parameters for the redirect page
    if success:
        status_code = "SUCCESS"
        params = {
            "status_code": status_code,
            "student_name": student_name,
            "student_id": student_id,
            "event_title": event_title,
            "distance": meta.get("distance", 0.0),
            "radius": meta.get("radius", 50.0)
        }
    else:
        status_code = meta.get("error_type", "GENERAL_ERROR") if meta else "GENERAL_ERROR"
        params = {
            "status_code": status_code,
            "message": message,
            "student_name": student_name,
            "student_id": student_id,
            "event_title": event_title,
            "distance": meta.get("distance", "") if meta else "",
            "radius": meta.get("radius", "") if meta else ""
        }

    status_url = url_for("student.status_page") + "?" + urlencode(params)

    return jsonify({
        "success": success,
        "message": message,
        "status_code": status_code,
        "redirect_url": status_url,
        "meta": meta
    }), (200 if success else 400)


@student_bp.route("/attendance/status")
def status_page():
    """
    Renders the universal student attendance status feedback page.
    """
    status_code = request.args.get("status_code", "SUCCESS")
    message = request.args.get("message", "")
    student_name = request.args.get("student_name", "")
    student_id = request.args.get("student_id", "")
    event_title = request.args.get("event_title", "Event Attendance")
    distance = request.args.get("distance", "")
    radius = request.args.get("radius", "")

    return render_template(
        "student/status.html",
        status_code=status_code,
        message=message,
        student_name=student_name,
        student_id=student_id,
        event_title=event_title,
        distance=distance,
        radius=radius
    )
