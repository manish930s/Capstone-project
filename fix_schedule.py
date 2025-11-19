import requests
import datetime as dt
import json

LIST_URL = "http://127.0.0.1:5001/list_events"
UPDATE_URL = "http://127.0.0.1:5001/update_event"

def get_ist_time():
    # Simple helper to get current time in ISO format for query
    now = dt.datetime.now()
    return now.isoformat(), (now + dt.timedelta(days=7)).isoformat()

def find_event(summary_name):
    time_min, time_max = get_ist_time()
    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "maxResults": 50
    }
    try:
        print(f"Searching for event '{summary_name}'...")
        resp = requests.get(LIST_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("ok"):
            print("Error listing events:", data.get("error"))
            return None
            
        events = data.get("events", [])
        for event in events:
            if event.get("summary") == summary_name:
                print(f"Found event: {event['summary']} (ID: {event['id']})")
                print(f"Current Start: {event['start']}")
                return event
        
        print(f"Event '{summary_name}' not found.")
        return None
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Exception searching event: {e}")
        return None

def update_event_time(event_id, new_start_iso, new_end_iso):
    payload = {
        "eventId": event_id,
        "start": new_start_iso,
        "end": new_end_iso
    }
    try:
        print(f"Updating event {event_id}...")
        resp = requests.post(UPDATE_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("ok"):
            print("✅ Event updated successfully!")
            print(f"New Start: {data.get('start')}")
            print(f"New End: {data.get('end')}")
        else:
            print("❌ Failed to update event:", data.get("error"))
            
    except Exception as e:
        print(f"Exception updating event: {e}")

if __name__ == "__main__":
    # Target: Python Basics
    # New Time: Nov 20, 2025, 2:00 PM (14:00)
    
    event = find_event("Python Basics")
    if event:
        # Hardcoded target times for tomorrow (Nov 20, 2025)
        # 2:00 PM IST is 14:00:00+05:30
        # 1.5 hours duration -> 15:30:00+05:30
        
        new_start = "2025-11-20T11:00:00+05:30"
        new_end = "2025-11-20T13:00:00+05:30"
        
        update_event_time(event["id"], new_start, new_end)
