import requests
import json

# Test Quiz My Uploads
print("Testing Quiz My Uploads...")

# 1. List uploads
print("\n1. Listing uploads...")
response = requests.get("http://127.0.0.1:5000/list_uploads")
print(f"Status: {response.status_code}")
files_data = response.json()
print(f"Files: {json.dumps(files_data, indent=2)}")

if files_data.get("files"):
    filename = files_data["files"][0]["name"]
    print(f"\n2. Generating quiz for: {filename}")
    
    response = requests.post(
        "http://127.0.0.1:5000/generate_quiz",
        json={"mode": "upload", "filename": filename}
    )
    
    print(f"Status: {response.status_code}")
    quiz_data = response.json()
    print(f"Response: {json.dumps(quiz_data, indent=2)}")
    
    if quiz_data.get("questions"):
        print(f"\n✅ SUCCESS! Generated {len(quiz_data['questions'])} questions")
        print(f"First question: {quiz_data['questions'][0]['question']}")
    else:
        print(f"\n❌ FAILED: {quiz_data.get('error', 'Unknown error')}")
else:
    print("\n❌ No files found in uploads")
