import os
import datetime as dt

from flask import Flask, request, jsonify

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


# ========= CONFIG =========

# ✅ Calendar scope: allows creating & editing events
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# ✅ Put the EXACT name of your OAuth client secret file here
# (the JSON you downloaded from Google Cloud Console)
CLIENT_SECRET_FILE = (
    "client_secret_2_370055681762-1an83limrs9ui5li794lmvpslk35bloj.apps.googleusercontent.com.json"
)

# Token file where OAuth credentials will be cached
TOKEN_FILE = "token.json"

# Default timezone for all events
DEFAULT_TZ = "Asia/Kolkata"

# ==========================


def get_credentials():
    """
    Load / refresh OAuth credentials, or run browser OAuth flow if first time.
    This will create/refresh token.json on disk.
    """
    creds = None

    # Load existing token if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there are no valid credentials, refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Try to refresh using the refresh token
            creds.refresh(Request())
        else:
            # First-time login: open browser and ask user to sign in
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for next time
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def build_calendar_service():
    """
    Build the Google Calendar API service client.
    """
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    return service


def add_study_block(summary: str, description: str, start_iso: str, end_iso: str) -> dict:
    """
    Create an event on the user's primary Google Calendar.

    `start_iso` and `end_iso` should be ISO-8601 datetime strings, e.g.:
      "2025-11-20T22:00:00+05:30"

    We always send an explicit timezone field (Asia/Kolkata).
    """
    service = build_calendar_service()

    event = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_iso,
            "timeZone": DEFAULT_TZ,
        },
        "end": {
            "dateTime": end_iso,
            "timeZone": DEFAULT_TZ,
        },
    }

    created = service.events().insert(calendarId="primary", body=event).execute()

    return {
        "ok": True,
        "eventId": created.get("id"),
        "htmlLink": created.get("htmlLink"),
        "summary": created.get("summary"),
        "start": created.get("start"),
        "end": created.get("end"),
    }


# ============== FLASK APP ==============

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """
    Simple health-check endpoint.
    Useful to test if your Flask server is up.
    """
    return jsonify({"ok": True, "message": "calendar_bridge is running"}), 200


@app.route("/create_event", methods=["POST"])
def create_event():
    """
    HTTP endpoint called from your agent_app.py.

    Expected JSON body:
    {
      "summary": "Title",
      "description": "Details",
      "start": "2025-11-20T22:00:00+05:30",
      "end":   "2025-11-20T23:59:00+05:30"
    }
    """
    try:
        data = request.get_json(force=True) or {}

        summary = data.get("summary", "Study Block")
        description = data.get("description", "")
        start = data.get("start")
        end = data.get("end")

        if not start or not end:
            return jsonify(
                {
                    "ok": False,
                    "error": "Missing 'start' or 'end' in request payload.",
                }
            ), 400

        result = add_study_block(summary, description, start, end)
        return jsonify(result), 200

    except Exception as e:
        # Make error visible to the caller (agent_app.py)
        return jsonify({"ok": False, "error": str(e)}), 500


# Optional: quick CLI test when you run:
#   python calendar_bridge.py --test
def quick_test():
    """
    Create a one-off test event directly from this script (no HTTP).
    """
    now = dt.datetime.now()
    start = (now + dt.timedelta(minutes=5)).replace(microsecond=0).isoformat()
    end = (now + dt.timedelta(minutes=65)).replace(microsecond=0).isoformat()

    print("Creating a test event from calendar_bridge.py ...")
    result = add_study_block(
        "CLI Test Block",
        "Sanity check from calendar_bridge.py quick_test()",
        start,
        end,
    )
    print("✅ Result:", result)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="Create a single test event and exit.",
    )
    args = parser.parse_args()

    if args.test:
        quick_test()
    else:
        # Normal mode: run the Flask server
        print("🚀 Serving Flask app on http://127.0.0.1:5001")
        app.run(host="127.0.0.1", port=5001)
