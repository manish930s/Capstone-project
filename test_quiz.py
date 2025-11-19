import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_list_uploads():
    print("1. Testing /list_uploads...")
    response = requests.get(f"{BASE_URL}/list_uploads")
    data = response.json()
    print(f"   Files found: {len(data.get('files', []))}")
    if data.get('files'):
        print(f"   First file: {data['files'][0]['name']}")
    return data.get('files', [])

def test_daily_recall():
    print("\n2. Testing Daily Recall quiz...")
    response = requests.post(f"{BASE_URL}/generate_quiz", 
                            json={"mode": "recall"})
    data = response.json()
    if data.get('questions'):
        print(f"   ✓ Generated {len(data['questions'])} questions")
        print(f"   Topics: {data.get('topics', 'N/A')}")
    else:
        print(f"   ⚠ {data.get('error', 'Unknown error')}")

def test_interview():
    print("\n3. Testing Mock Interview...")
    response = requests.post(f"{BASE_URL}/generate_quiz",
                            json={"mode": "interview", "job_role": "Frontend Developer"})
    data = response.json()
    if data.get('questions'):
        print(f"   ✓ Generated {len(data['questions'])} interview questions")
        print(f"   Q1: {data['questions'][0]['question'][:60]}...")
    else:
        print(f"   ✗ Error: {data.get('error')}")

def test_upload_quiz(files):
    if not files:
        print("\n4. Skipping Upload Quiz (no files)")
        return
    
    print(f"\n4. Testing Upload Quiz with '{files[0]['name']}'...")
    response = requests.post(f"{BASE_URL}/generate_quiz",
                            json={"mode": "upload", "filename": files[0]['name']})
    data = response.json()
    if data.get('questions'):
        print(f"   ✓ Generated {len(data['questions'])} questions")
        print(f"   Q1: {data['questions'][0]['question'][:60]}...")
    else:
        print(f"   ✗ Error: {data.get('error')}")

if __name__ == "__main__":
    print("=== Quiz Hub Backend Test ===\n")
    try:
        files = test_list_uploads()
        test_daily_recall()
        test_interview()
        test_upload_quiz(files)
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
