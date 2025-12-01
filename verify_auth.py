import requests
import sys

BASE_URL = "http://localhost:8000/api/v1/auth"

def test_signup():
    print("Testing Signup...")
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/signup", json=payload)
    if response.status_code == 200:
        print("Signup Successful:", response.json())
        return True
    elif response.status_code == 400 and "already exists" in response.text:
        print("User already exists, proceeding...")
        return True
    else:
        print("Signup Failed:", response.status_code, response.text)
        return False

def test_login():
    print("Testing Login...")
    payload = {
        "username": "testuser",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/login", json=payload)
    if response.status_code == 200:
        token = response.json().get("token")
        print("Login Successful. Token:", token)
        return token
    else:
        print("Login Failed:", response.status_code, response.text)
        return None

def test_me(token):
    print("Testing Get Me...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/me", headers=headers)
    if response.status_code == 200:
        print("Get Me Successful:", response.json())
        return True
    else:
        print("Get Me Failed:", response.status_code, response.text)
        return False

if __name__ == "__main__":
    if test_signup():
        token = test_login()
        if token:
            test_me(token)
