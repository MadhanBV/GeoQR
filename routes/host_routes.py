from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from services.event_service import EventService
from services.attendance_service import AttendanceService
from utils.token_generator import generate_qr_token
from utils.qr_generator import generate_qr_base64
from config import Config

host_bp = Blueprint("host", __name__)


@host_bp.route("/host/create", methods=["GET", "POST"])
def create_event_page():
    """Renders event creation form and processes new event submissions."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        date = request.form.get("date", "").strip()
        lat_str = request.form.get("organizer_lat", "").strip()
        lon_str = request.form.get("organizer_lon", "").strip()
        radius_str = request.form.get("radius_meters", "50").strip()

        if not title or not description or not date or not lat_str or not lon_str:
            flash("All fields including organizer GPS location are required.", "error")
            return redirect(url_for("host.create_event_page"))

        try:
            organizer_lat = float(lat_str)
            organizer_lon = float(lon_str)
            radius_meters = float(radius_str)
        except ValueError:
            flash("Invalid coordinate or radius format.", "error")
            return redirect(url_for("host.create_event_page"))

        # Create event via service layer
        event = EventService.create_event(
            title=title,
            description=description,
            date=date,
            organizer_lat=organizer_lat,
            organizer_lon=organizer_lon,
            radius_meters=radius_meters
        )

        flash(f"Event '{event.title}' created successfully!", "success")
        return redirect(url_for("host.event_dashboard", event_id=event.id))

    return render_template("host/create_event.html")


@host_bp.route("/host/events")
def list_events_page():
    """Lists all created events for organizer reference."""
    events = EventService.get_all_events()
    return render_template("host/list_events.html", events=events)


@host_bp.route("/host/event/<event_id>")
def event_dashboard(event_id: str):
    """Renders the Live Dynamic QR Host Dashboard for an event."""
    event = EventService.get_event_by_id(event_id)
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for("host.create_event_page"))

    # Pre-render initial QR token so image displays immediately without JS delay
    token, timestamp = generate_qr_token(event_id)
    checkin_url = request.host_url.rstrip("/") + url_for("student.checkin_page", event_id=event_id, token=token)
    initial_qr_image = generate_qr_base64(checkin_url)

    return render_template(
        "host/dashboard.html",
        event=event,
        qr_expiry_seconds=Config.QR_TOKEN_MAX_AGE_SECONDS,
        initial_qr_image=initial_qr_image,
        initial_checkin_url=checkin_url
    )


@host_bp.route("/api/event/<event_id>/qr-token")
def get_dynamic_qr_token(event_id: str):
    """
    API endpoint invoked by the Host Dashboard every 25 seconds.
    Generates a new signed token and in-memory base64 QR code.
    """
    event = EventService.get_event_by_id(event_id)
    if not event:
        return jsonify({"success": False, "error": "Event not found"}), 404

    # Generate freshly signed timed token
    token, timestamp = generate_qr_token(event_id)

    # Build the full mobile check-in URL
    # e.g., http://127.0.0.1:5000/checkin/evt_xxx?token=yyy
    checkin_url = request.host_url.rstrip("/") + url_for("student.checkin_page", event_id=event_id, token=token)

    # Render directly to in-memory Base64 Data URL
    qr_base64 = generate_qr_base64(checkin_url)

    return jsonify({
        "success": True,
        "token": token,
        "qr_image": qr_base64,
        "checkin_url": checkin_url,
        "expires_in": Config.QR_TOKEN_MAX_AGE_SECONDS,
        "created_at": timestamp
    })


@host_bp.route("/api/event/<event_id>/attendees")
def get_event_attendees_api(event_id: str):
    """
    API endpoint returning live verified attendee list for the dashboard.
    """
    attendees = AttendanceService.get_attendees_for_event(event_id)
    return jsonify({
        "success": True,
        "count": len(attendees),
        "attendees": [att.to_dict() for att in attendees]
    })
