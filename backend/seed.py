import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api")
API_KEY = os.getenv("ADMIN_API_KEY")
if not API_KEY:
    raise ValueError("ADMIN_API_KEY not set in .env file")

products = [
    {
        "name": "Nike Kyrie 4",
        "category": "Shoes",
        "price": 1250.0,
        "description": "Classic Kyrie silhouette, white with orange sole",
        "in_stock": True
    },
    {
        "name": "Nike Kyrie 3",
        "category": "Shoes",
        "price": 1200.0,
        "description": "Kyrie 3 signature shoe, clean colorway",
        "in_stock": True
    },
    {
        "name": "Nike LeBron Soldier 11",
        "category": "Shoes",
        "price": 1150.0,
        "description": "LeBron Soldier 11, white with navy straps",
        "in_stock": True
    },
    {
        "name": "Nike LeBron 16",
        "category": "Shoes",
        "price": 1500.0,
        "description": "LeBron 16, white/red with gold branding",
        "in_stock": True
    },
    {
        "name": "Nike PG",
        "category": "Shoes",
        "price": 1350.0,
        "description": "Paul George signature, clean all-white",
        "in_stock": True
    },
    {
        "name": "Way of Wade 9",
        "category": "Shoes",
        "price": 1550.0,
        "description": "Way of Wade 9, purple/black colorway",
        "in_stock": True
    },
]

for product in products:
    response = requests.post(
        f"{BASE_URL}/products",
        json=product,
        headers={"X-API-Key": API_KEY}
    )
    if response.status_code in (200, 201):
        data = response.json()
        print(f"✅ Added: {data['name']} (id={data['id']})")
    else:
        print(f"❌ Failed: {product['name']} — {response.text}")