import requests

data = {
    "email": "admin@demo.transport.com",
    "password": "password123"
}
try:
    response = requests.post("http://localhost:8000/api/v1/auth/login", json=data)
    print(response.status_code)
    print(response.text)
except Exception as e:
    print(e)
