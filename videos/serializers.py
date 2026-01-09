from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    word_lat = serializers.CharField(source='title_lat')
    word_kiril = serializers.CharField(source='title_kiril')
    word_ru = serializers.CharField(source='title_ru')
    definition_lat = serializers.CharField(source='description_lat')
    definition_kiril = serializers.CharField(source='description_kiril')
    definition_ru = serializers.CharField(source='description_ru')
    category = serializers.CharField(source='category.name')

    class Meta:
        model = Video
        fields = [
            'word_lat', 'word_kiril', 'word_ru',
            'definition_lat', 'definition_kiril', 'definition_ru',
            'category', 'telegram_file_id'
        ]
