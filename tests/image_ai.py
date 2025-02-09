import os
from dotenv import load_dotenv
import requests
from PIL import Image

load_dotenv('../.env')

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
API_TOKEN = os.getenv('HUGGING_FACE_API')
headers = {"Authorization": f"Bearer {API_TOKEN}"}


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content


image_bytes = query({
    "inputs": "Anime girl at a coffee shop",
})

import io

image = Image.open(io.BytesIO(image_bytes))

with open("image.jpg", "wb") as f:
    f.write(image_bytes)
