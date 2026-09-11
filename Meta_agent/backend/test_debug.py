import json
import requests
url = "http://127.0.0.1:8081/api/agent/chat"
headers = {"Content-Type": "application/json"}
payload = {
    "prompt": "Action Payload attached",
    "action": {
        "event": {
            "name": "confirm_booking",
            "context": {
                "hotel_name": "Seaside Resort",
                "price": "$350/night",
                "full_name": "qwerty",
                "check_in_date": "2026-09-10",
                "num_guests": "1",
                "breakfast": True
            }
        }
    },
    "session_id": "test_session_5"
}
resp = requests.post(url, headers=headers, json=payload)
print(json.dumps(resp.json(), indent=2))
