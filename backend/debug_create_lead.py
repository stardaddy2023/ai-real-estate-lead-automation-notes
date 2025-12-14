import requests
import json

url = "http://localhost:8000/leads"
payload = {
    "address": "123 Test St",
    "owner_name": "Test Owner",
    "status": "New",
    "strategy": "Wholesale",
    "sqft": 1000,
    "bedrooms": 3,
    "bathrooms": 2,
    "year_built": 2000,
    "lot_size": 0.25,
    "has_pool": "No",
    "has_garage": "No",
    "has_guesthouse": "No",
    "distress_score": 50
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
