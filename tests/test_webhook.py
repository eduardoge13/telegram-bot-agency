import json
import requests

# Simula un update de Telegram (mensaje privado)
fake_update = {
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "from": {
            "id": 111111111,
            "is_bot": False,
            "first_name": "Eduardo",
            "username": "testuser",
            "language_code": "es"
        },
        "chat": {
            "id": 111111111,
            "first_name": "Eduardo",
            "username": "testuser",
            "type": "private"
        },
        "date": 1727220000,
        "text": "/start"
    }
}

resp = requests.post(
    "http://127.0.0.1:5000/api/telegram",
    json=fake_update
)

print("Status code:", resp.status_code)
print("Response text:", resp.text)