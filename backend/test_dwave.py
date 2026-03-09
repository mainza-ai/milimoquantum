import requests
import json

url = "http://localhost:8000/api/chat/send"
headers = {"Content-Type": "application/json"}
data = {
    "message": "Create a D-Wave QUBO for a simple triangle graph and solve it.",
    "agent_type": "dwave",
    "conversation_id": None
}

print("Sending request to /api/chat/send for D-Wave agent...")
try:
    response = requests.post(url, json=data, headers=headers, stream=True)
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.text}")
    else:
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data:'):
                    try:
                        msg = json.loads(decoded[5:])
                        if 'content' in msg:
                            print(msg['content'], end='', flush=True)
                    except Exception:
                        pass
        print("\n\nTest Finished Successfully.")
except Exception as e:
    print(f"Connection failed: {e}")
