import requests

def update_level(user_id, level):
    url = "http://127.0.0.1:8080/update_level"
    data = {"user_id": user_id, "level": level}
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print("Level updated successfully")
    else:
        print("Failed to update level")
        
def check_server_health():
    url = "http://127.0.0.1:8080/health_check"
    response = requests.get(url)
    
    if response.status_code == 200:
        print("Server is running")
    else:
        print("Server is down or having an issue, server health checked failed")
        
if __name__ == "__main__":
    check_server_health()
    update_level(123456789, 5)