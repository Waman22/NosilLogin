import requests

url = "http://127.0.0.1:5000/send-email"
data = {
    "recipient": "test@example.com",
    "subject": "Hello from Flask-Mail",
    "body": "This is a test email!"
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=data, headers=headers)

print(response.json())
