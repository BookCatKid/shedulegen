"""
Schedule Generator Web App

A Flask web application that generates customizable school schedules in SVG format.
Allows users to input class names and titles through a web interface.
Handles schedule generation, validation, and error handling.
"""

import json
import markdown
from flask import Flask, Response, render_template, request, redirect, url_for
from daschedule import normalize_classes, create_svg, CLASSES, TITLE_TEXT, ROOMS, TEACHERS
from format_schedule import format_schedule_for_events
import os
from flask import session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "da_dev_secret_key")
GOOGLE_CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
REDIRECT_URI = "https://127.0.0.1:5000/oauth2callback"

@app.route("/")
def index():
    """
    Render homepage with schedule_form.html template
    """
    default_classes = {str(k): v for k, v in CLASSES.items()}
    default_rooms = {str(k): v for k, v in ROOMS.items()}
    default_teachers = {str(k): v for k, v in TEACHERS.items()}
    return render_template("schedule_form.html",
                           classes=default_classes,
                           rooms=default_rooms,
                           teachers=default_teachers,
                           title=TITLE_TEXT)


@app.route("/generate", methods=["POST"])
def generate_schedule():
    """
    Generate SVG schedule based on POST form data.
    """
    try:
        title = request.form.get("title", "Schedule")
        free_period_name = request.form.get("free_period_name", "").strip() or "Study Period"
        classes_json = request.form.get("classes", "{}")

        raw_classes = json.loads(classes_json)

        # Extract just the 'name' for normalize_classes
        classes = {
            str(k): v.get("name", "").strip()
            for k, v in raw_classes.items()
            if isinstance(v, dict)
        }

        # Extract room data
        rooms = {
            str(k): v.get("room", "").strip()
            for k, v in raw_classes.items()
            if isinstance(v, dict)
        }

        # Extract teacher data
        teachers = {
            str(k): v.get("teacher", "").strip()
            for k, v in raw_classes.items()
            if isinstance(v, dict)
        }

        # Normalize classes
        classes = normalize_classes(classes)

        if classes is None:
            return "Error: Invalid classes format", 400

        svg_content = create_svg(classes, rooms, teachers, title, free_period_name, exact_dimension=False)
        return Response(svg_content, mimetype='image/svg+xml')

    except json.JSONDecodeError:
        return "Error: Invalid JSON format for classes", 400
    except Exception as e:
        return f"Error generating schedule: {str(e)}", 500


@app.route("/generate", methods=["GET"])
def generate_schedule_get():
    """
    Redirect user back to homepage if they try to open /generate in the browser
    """
    return redirect(url_for("index"))


@app.route("/guide")
def guide():
    """
    Render GUIDE.md as GitHub-style HTML
    """
    with open("GUIDE.md", "r", encoding="utf-8") as f:
        guide_md = f.read()

    guide_html = markdown.markdown(
        guide_md,
        extensions=["fenced_code", "tables", "toc"]
    )

    return render_template("guide.html", content=guide_html)


@app.route("/api/import_by_email", methods=["POST"])
def import_by_email():
    data = request.get_json()
    email = data.get("email") if data else None
    if not email:
        return {"error": "Missing email"}, 400
    try:
        # Check if email is in failed calendars list
        with open("failed_calendars.json", "r", encoding="utf-8") as f:
            failed_calendars = json.load(f)
        if email in failed_calendars:
            return {"error": f"Email '{email}' exists but their permissions were off at caching time. Please contact me to update the calendar data."}, 400

        with open("events_monday_by_calendar.json", "r", encoding="utf-8") as f:
            all_schedules = json.load(f)
        if email not in all_schedules:
            return {"error": f"Email '{email}' not found in the cached calendar data."}, 404
        student_events = all_schedules[email]
        formatted, unrecognized = format_schedule_for_events(student_events)
        return {"schedule": formatted, "unrecognized": unrecognized}
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/login/google")
def login_google():
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type="online",
        include_granted_scopes="true",
        prompt="consent"
    )
    session["oauth_state"] = state
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    state = session.get("oauth_state")
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session["google_credentials"] = {
        "token": credentials.token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }
    return redirect(url_for("index") + "?imported=google")

@app.route("/api/import_google_calendar")
def import_google_calendar():
    creds_data = session.get("google_credentials")
    if not creds_data:
        return {"error": "Not authenticated with Google."}, 401
    creds = Credentials(
        token=creds_data["token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"]
    )
    try:
        service = build("calendar", "v3", credentials=creds)
        # Fetch events for the next Monday (similar to from_json.py logic)
        import datetime
        DESIRED_WEEKDAY = 0  # Monday
        today = datetime.datetime.now(datetime.timezone.utc)
        days_ahead = (DESIRED_WEEKDAY - today.weekday() + 7) % 7
        next_monday = today + datetime.timedelta(days=days_ahead)
        next_monday_start = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        next_monday_end = next_monday_start + datetime.timedelta(days=1)
        events_result = service.events().list(
            calendarId='primary',
            timeMin=next_monday_start.isoformat(),
            timeMax=next_monday_end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500
        ).execute()
        events = events_result.get("items", [])
        # Format events for the schedule generator
        formatted, unrecognized = format_schedule_for_events(events)
        return {"schedule": formatted, "unrecognized": unrecognized}
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    # For development with HTTPS
    app.run(debug=True, ssl_context='adhoc', host='127.0.0.1', port=5000)
