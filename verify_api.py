import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ishoratech_backend.settings')
django.setup()

from videos.models import Category, Video
from rest_framework.test import APIClient

def verify():
    print("Verifying API...")
    
    # Create dummy data
    cat, _ = Category.objects.get_or_create(name="Test Category")
    Video.objects.create(
        title="Test Video",
        description="This is a test video",
        category=cat,
        telegram_file_id="TEST_FILE_ID",
        is_published=True
    )
    
    # Test API
    client = APIClient()
    response = client.get('/api/videos/')
    
    if response.status_code == 200:
        print("API Response 200 OK")
        print("Data:", response.json())
        if len(response.json()) > 0 and response.json()[0]['word'] == "Test Video":
            print("✅ Verification Successful: Video found in API.")
        else:
            print("❌ Verification Failed: Video not found in API.")
    else:
        print(f"❌ Verification Failed: Status {response.status_code}")

if __name__ == "__main__":
    verify()
