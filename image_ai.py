import requests
from PIL import Image
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
API_TOKEN = "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"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.content
image_bytes = query({
	"inputs": "Astronaut riding a horse",
})


import io
image = Image.open(io.BytesIO(image_bytes))

with open("image.jpg", "wb") as f:
	f.write(image_bytes)
