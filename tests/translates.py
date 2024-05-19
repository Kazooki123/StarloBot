import requests
from dotenv import load_dotenv
import os

load_dotenv()
 
RAPID_API_KEY = os.getenv('RAPID_API')
url = "https://deep-translate1.p.rapidapi.com/language/translate/v2/languages"

headers = {
	"X-RapidAPI-Key": {RAPID_API_KEY},
	"X-RapidAPI-Host": "deep-translate1.p.rapidapi.com"
}

response = requests.get(url, headers=headers)

print(response.json())