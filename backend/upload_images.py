import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api")
API_KEY = os.getenv("ADMIN_API_KEY")
if not API_KEY:
    raise ValueError("ADMIN_API_KEY not set in .env file")
default_images_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "images"))
IMAGES_DIR = os.getenv("IMAGES_DIR", default_images_dir)


products = [
    {"id": 1, "image": "Nike-Kyrie-4.jpeg"},
    {"id": 2, "image": "Nike-Kyrie-3.jpeg"},
    {"id": 3, "image": "Nike-Lebron-soldier-11.jpeg"},
    {"id": 4, "image": "Nike-Lebron-16.jpeg"},
    {"id": 5, "image": "Nike-PG.jpeg"},
    {"id": 6, "image": "Way-of-Wade-9.jpeg"},
]

for item in products:
    image_path = os.path.join(IMAGES_DIR, item["image"])

    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        continue

    with open(image_path, "rb") as f:
        res = requests.post(
            f"{BASE_URL}/products/{item['id']}/upload-image",
            headers={"X-API-Key": API_KEY},
            files={"file": (item["image"], f, "image/jpeg")}
        )

    if res.ok:
        print(f"✅ Uploaded image for product {item['id']}: {item['image']}")
    else:
        print(f"❌ Failed for product {item['id']}: {res.text}")