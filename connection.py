"""
MIT License

Copyright (c) 2024 KAZOOKIovestocode,

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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