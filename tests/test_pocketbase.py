from pocketbase import PocketBase  # Client also works the same
from pocketbase.client import FileUpload

client = PocketBase('http://127.0.0.1:8090')

# authenticate as regular user
user_data = client.collection("users").auth_with_password(
    "user@example.com", "0123456789")

# or as admin
admin_data = client.admins.auth_with_password("test@example.com", "0123456789")

# list and filter "example" collection records
result = client.collection("example").get_list(
    1, 20, {"filter": 'status = true && created > "2022-08-01 10:00:00"'})

# create record and upload file to image field
result = client.collection("example").create(
    {
        "status": "true",
        "image": FileUpload(("image.png", open("image.png", "rb"))),
    })
