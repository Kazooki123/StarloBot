import requests

url = "https://deep-translate1.p.rapidapi.com/language/translate/v2/languages"

headers = {
	"X-RapidAPI-Key": "defb4f53a9msh0dc05b3f255fab2p16601ejsndefc49120355",
	"X-RapidAPI-Host": "deep-translate1.p.rapidapi.com"
}

response = requests.get(url, headers=headers)

print(response.json())