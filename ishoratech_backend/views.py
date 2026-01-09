from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "message": "Welcome to IshoraTech API",
        "endpoints": {
            "videos": "/api/videos/",
            "admin": "/admin/"
        }
    })
