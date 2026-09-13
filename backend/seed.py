import requests

BASE_URL = "https://kicks-mtaani-api.onrender.com/api"
API_KEY = "kicks-admin-key-nakuru"

products = [
    {
        "name": "Nike Kyrie 4",
        "price": 1250.0,
        "description": "Classic Kyrie silhouette, white with orange sole",
        "in_stock": True
    },
    {
        "name": "Nike Kyrie 3",
        "price": 1200.0,
        "description": "Kyrie 3 signature shoe, clean colorway",
        "in_stock": True
    },
    {
        "name": "Nike LeBron Soldier 11",
        "price": 1150.0,
        "description": "LeBron Soldier 11, white with navy straps",
        "in_stock": True
    },
    {
        "name": "Nike LeBron 16",
        "price": 1500.0,
        "description": "LeBron 16, white/red with gold branding",
        "in_stock": True
    },
    {
        "name": "Nike PG",
        "price": 1350.0,
        "description": "Paul George signature, clean all-white",
        "in_stock": True
    },
    {
        "name": "Way of Wade 9",
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
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Added: {data['name']} (id={data['id']})")
    else:
        print(f"❌ Failed: {product['name']} — {response.text}")