import requests
import datetime as dt
import json

BASE_URL = "http://127.0.0.1:5000"

def test_delete_flow():
    print("1. Creating a test event...")
    now = dt.datetime.now()
    start = (now + dt.timedelta(minutes=10)).isoformat()
    end = (now + dt.timedelta(minutes=40)).isoformat()
    
    # We need to simulate the agent's create_events action or call calendar_bridge directly
    # But agent_app doesn't have a direct create_event endpoint exposed to public, 
    # it processes agent logic. 
    # However, calendar_bridge is running on 5001. Let's hit agent_app's /delete_event which proxies to calendar_bridge.
    # To create, we can hit calendar_bridge directly for this test.
    
    CALENDAR_URL = "http://127.0.0.1:5001/create_event"
    payload = {
        "summary": "Delete Me Test",
        "description": "Temporary event",
        "start": start,
        "end": end
    }
    
    try:
        resp = requests.post(CALENDAR_URL, json=payload)
        data = resp.json()
        if not data.get("ok"):
            print("FAILED to create event:", data)
            return
            
        event_id = data["eventId"]
        print(f"   Created event: {event_id}")
        
        print("2. Deleting event via Agent App proxy...")
        DELETE_URL = f"{BASE_URL}/delete_event"
        del_payload = {"event_id": event_id}
        
        del_resp = requests.post(DELETE_URL, json=del_payload)
        del_data = del_resp.json()
        
        if del_data.get("ok"):
            print("   SUCCESS: Event deleted.")
        else:
            print("   FAILED to delete:", del_data)
            
    except Exception as e:
        print("EXCEPTION:", e)

if __name__ == "__main__":
    test_delete_flow()
