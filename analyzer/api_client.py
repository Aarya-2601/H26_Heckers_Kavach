import requests

BASE_URL = "https://api.example.com"


def fetch_user_data(user_id):
    response = requests.get(f"{BASE_URL}/users/{user_id}", timeout=5)
    return response.json()


def create_user(payload):
    response = requests.post(f"{BASE_URL}/users", json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


def delete_user(user_id):
    return requests.delete(f"{BASE_URL}/users/{user_id}", timeout=5)
