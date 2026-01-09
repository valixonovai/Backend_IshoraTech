from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Video

class ModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")

    def test_video_creation_multilang(self):
        """Test that a video is created correctly with multi-language fields."""
        video = Video.objects.create(
            title_lat="Video Title Lat",
            title_kiril="Видео Титле Кирил",
            title_ru="Видео Заголовок",
            description_lat="Desc Lat",
            description_kiril="Десц Кирил",
            description_ru="Описание",
            category=self.category,
            telegram_file_id="12345",
            is_published=True
        )
        self.assertEqual(video.title_lat, "Video Title Lat")
        self.assertEqual(video.title_kiril, "Видео Титле Кирил")
        self.assertEqual(video.title_ru, "Видео Заголовок")
        self.assertEqual(str(video), "Video Title Lat")

class VideoAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="API Category")
        self.video = Video.objects.create(
            title_lat="Apple",
            title_kiril="Olma",
            title_ru="Яблоко",
            description_lat="A fruit",
            description_kiril="Meva",
            description_ru="Фрукт",
            category=self.category,
            telegram_file_id="file_123",
            is_published=True
        )
        self.url = reverse('video-list')

    def test_get_videos_structure(self):
        """Test retrieving the list of videos and checking JSON structure."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(len(response.data), 1)
        data = response.data[0]
        
        # Check all fields are present
        self.assertEqual(data['word_lat'], "Apple")
        self.assertEqual(data['word_kiril'], "Olma")
        self.assertEqual(data['word_ru'], "Яблоко")
        self.assertEqual(data['definition_lat'], "A fruit")
        self.assertEqual(data['definition_kiril'], "Meva")
        self.assertEqual(data['definition_ru'], "Фрукт")
        self.assertEqual(data['category'], "API Category")
        self.assertEqual(data['telegram_file_id'], "file_123")

    def test_unpublished_video(self):
        """Test that unpublished videos are not returned."""
        Video.objects.create(
            title_lat="Hidden",
            category=self.category,
            telegram_file_id="hidden_file",
            is_published=False
        )
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
