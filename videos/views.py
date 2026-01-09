from rest_framework import generics
from .models import Video
from .serializers import VideoSerializer

class VideoListView(generics.ListAPIView):
    queryset = Video.objects.filter(is_published=True).order_by('-created_at')
    serializer_class = VideoSerializer
