import datetime as dt
from zoneinfo import ZoneInfo
import re
import requests

from google import genai
from google.genai import types as genai_types

import os
from dotenv import load_dotenv

load_dotenv()

# ========================
# CONFIG
# ========================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("Please set the GOOGLE_API_KEY environment variable first.")

client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-2.0-flash"   # or "gemini-2.5-flash-lite" if enabled

# URL of your local Flask bridge (no Cloudflare)
CALENDAR_BRIDGE_URL = "http://127.0.0.1:5001/create_event"

# ========================
# Timezone helpers
# ========================

def get_ist_tz() -> dt.tzinfo:
    """
    Safely get Asia/Kolkata timezone.

    - Tries ZoneInfo('Asia/Kolkata')
    - If tzdata is missing, falls back to fixed +05:30 offset
    """
    try:
        return ZoneInfo("Asia/Kolkata")
    except Exception:
        # No tzdata on this system – use fixed IST offset (good enough, no DST).
        return dt.timezone(dt.timedelta(hours=5, minutes=30))


# ========================
# Tools
# ========================

def get_current_datetime(timezone: str = "Asia/Kolkata") -> dict:
    """
    Returns current date/time so we can:
    - know today's date
    - answer "what is today"
    - interpret "tomorrow", etc.
    """
    if timezone == "Asia/Kolkata":
        tz = get_ist_tz()
    else:
        try:
            tz = ZoneInfo(timezone)
        except Exception:
            tz = get_ist_tz()

    now = dt.datetime.now(tz)

    return {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "weekday": now.strftime("%A"),
        "human_readable": now.strftime("%A, %d %B %Y, %I:%M %p"),
        "timezone": timezone,
    }


def create_calendar_event(summary: str, description: str, start_iso: str, end_iso: str) -> dict:
    """
    Call your local calendar_bridge.py server (Flask) to create an event.

    Args:
        summary: event title
        description: event description
        start_iso: ISO 8601 string (with timezone)
        end_iso: ISO 8601 string
    """
    payload = {
        "summary": summary,
        "description": description,
        "start": start_iso,
        "end": end_iso,
    }

    try:
        resp = requests.post(CALENDAR_BRIDGE_URL, json=payload, timeout=10)
        print("[DEBUG] Calendar bridge status:", resp.status_code)
        print("[DEBUG] Calendar bridge body  :", resp.text)

        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


# ========================
# Helper: auto-parse "tomorrow at 11pm"
# ========================

def auto_create_tomorrow_event(user_message: str, today_info: dict) -> dict | None:
    """
    Very simple 'direct save' helper.

    If user says things like:
      "i want to save reminder for DSA task tomorrow at 11pm"

    We:
      - detect "tomorrow"
      - parse "11pm"
      - build IST datetimes for tomorrow 23:00–23:30
      - call create_calendar_event()
    """
    text = user_message.lower()

    if "tomorrow" not in text:
        return None

    # find time like '11pm', '7 am', '07:30pm'
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text)
    if not m:
        # no recognizable time – let manual flow handle it
        return None

    hour = int(m.group(1))
    minute = int(m.group(2) or "0")
    ampm = m.group(3)

    if ampm == "pm" and hour != 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0

    # figure out "tomorrow" date from today's date
    # today_info['date'] is "YYYY-MM-DD"
    today_date = dt.datetime.fromisoformat(today_info["date"] + "T00:00:00")
    ist = get_ist_tz()
    today_date = today_date.replace(tzinfo=ist)

    start_dt = today_date + dt.timedelta(days=1, hours=hour, minutes=minute)
    end_dt = start_dt + dt.timedelta(minutes=30)  # default 30-minute reminder

    # crude summary guess from text
    summary = "Reminder"
    if "dsa" in text:
        summary = "DSA Task Reminder"
    elif "gym" in text:
        summary = "GYM"
    elif "exam" in text:
        summary = "Exam Prep"

    description = user_message

    calendar_result = create_calendar_event(
        summary=summary,
        description=description,
        start_iso=start_dt.isoformat(),
        end_iso=end_dt.isoformat(),
    )

    return {
        "calendar_result": calendar_result,
        "summary": summary,
        "start_dt": start_dt,
        "end_dt": end_dt,
    }


# ========================
# Helper: ask Gemini
# ========================

SYSTEM_PROMPT = """
You are Manish's personal Study & Career Co-Pilot.

Capabilities:
- Help plan study, AI/ML learning, Kaggle competitions, MCA exam prep.
- You know how to reason about today's date and relative dates using the `get_current_datetime` tool.
- You can create Google Calendar events via the `create_calendar_event` tool, but Python code actually calls it.

VERY IMPORTANT:

1) When the user asks for the current date/day:
   - The wrapper passes today's date/time in [CONTEXT]. Use that to answer.

2) When the user says things like:
   - "tomorrow", "day after tomorrow", "next Monday", "this weekend"
   - or specific dates like "20th Nov 2025"
   you must interpret them into concrete datetimes in IST (Asia/Kolkata).

3) There are TWO ways to create calendar events:

   (A) Direct auto-save:
       The Python wrapper may already have created an event and will pass details in [CONTEXT]
       under 'auto_event_info'. In that case, just confirm what was done.

   (B) Manual wizard:
       If the wrapper sets 'manual_calendar_flow' in [CONTEXT], then you should speak like
       a conversational wizard while Python collects the exact date/time from the user.

4) You DO NOT directly call Python functions. They are already called outside and results are put in [CONTEXT].
"""


def chat_with_agent(user_message: str, context: dict | None = None) -> str:
    """
    Send a message to Gemini with some extra context (tools results, etc.)
    and get back a reply.
    """
    parts = []

    # System prompt
    parts.append(genai_types.Part(text=SYSTEM_PROMPT))

    # Add context (like today's date, calendar results, etc.)
    if context:
        parts.append(
            genai_types.Part(
                text=f"[CONTEXT]\n{context}"
            )
        )

    # User message
    parts.append(genai_types.Part(text=f"[USER]\n{user_message}"))

    content = genai_types.Content(
        role="user",
        parts=parts
    )

    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=[content],
    )

    # Extract text
    if resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
        text = resp.candidates[0].content.parts[0].text
        if text is not None:
            return text.strip()

    return "(No response from model)"


# ========================
# CLI loop
# ========================

def main():
    print("=== Manish's Study & Career Co-Pilot (local, no Cloudflare) ===")
    print("Type 'exit' to quit.\n")

    # Cache today's datetime once at start (you can also refresh per turn if you prefer)
    today_info = get_current_datetime()
    print(f"[INFO] Today is: {today_info['human_readable']} ({today_info['timezone']})")

    while True:
        user_msg = input("\nYou > ").strip()
        if user_msg.lower() in {"exit", "quit"}:
            print("Bye! 👋")
            break

        lower_msg = user_msg.lower()

        # Very simple intent detection for demo:
        wants_date = any(
            phrase in lower_msg
            for phrase in ["today's date", "today date", "what is today", "what day is it"]
        )
        wants_calendar = (
            "calendar" in lower_msg
            or "reminder" in lower_msg
            or "remainder" in lower_msg  # common typo
            or "save" in lower_msg and "tomorrow" in lower_msg
        )

        context: dict = {"today_info": today_info}
        calendar_result = None

        # 1) Try AUTO mode first: "tomorrow at 11pm" style
        auto_info = None
        if "tomorrow" in lower_msg and ("am" in lower_msg or "pm" in lower_msg):
            auto_info = auto_create_tomorrow_event(user_msg, today_info)
            if auto_info is not None:
                calendar_result = auto_info["calendar_result"]
                context["auto_event_info"] = {
                    "summary": auto_info["summary"],
                    "start_iso": auto_info["start_dt"].isoformat(),
                    "end_iso": auto_info["end_dt"].isoformat(),
                    "calendar_result": calendar_result,
                }

        # 2) If no auto event happened but user wants calendar, use MANUAL wizard
        if wants_calendar and calendar_result is None:
            context["manual_calendar_flow"] = True
            print("Let's create a calendar event.")
            title = input("  - Event title (e.g. 'DSA Practice'): ").strip() or "Study Block"
            desc = input("  - Short description: ").strip() or "No description"

            date_str = input("  - Date (YYYY-MM-DD) in IST: ").strip()
            start_time = input("  - Start time (HH:MM, 24h): ").strip()
            end_time = input("  - End time (HH:MM, 24h): ").strip()

            # Construct ISO datetimes in IST
            start_iso = f"{date_str}T{start_time}:00+05:30"
            end_iso = f"{date_str}T{end_time}:00+05:30"

            calendar_result = create_calendar_event(
                summary=title,
                description=desc,
                start_iso=start_iso,
                end_iso=end_iso,
            )

            context["calendar_result"] = calendar_result
            context["manual_event_info"] = {
                "summary": title,
                "start_iso": start_iso,
                "end_iso": end_iso,
            }

        # Agent reply with context (today + calendar_result if any)
        reply = chat_with_agent(user_msg, context=context)

        print("\nAgent >", reply)

        # Extra confirmation from Python if we created an event this turn
        if calendar_result:
            if calendar_result.get("ok") or calendar_result.get("success"):
                link = (
                    calendar_result.get("htmlLink")
                    or calendar_result.get("bridge_response", {}).get("htmlLink")
                )
                print("✅ Python: Event created successfully.")
                if link:
                    print("   Link:", link)
            else:
                print("❌ Python: Failed to create event.")
                print("   Error:", calendar_result.get("error"))


if __name__ == "__main__":
    main()
