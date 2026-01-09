from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Video(models.Model):
    title_lat = models.CharField(max_length=255, default='')
    title_kiril = models.CharField(max_length=255, default='')
    title_ru = models.CharField(max_length=255, blank=True, null=True)
    
    description_lat = models.TextField(default='')
    description_kiril = models.TextField(default='')
    description_ru = models.TextField(blank=True, null=True)
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
    telegram_file_id = models.CharField(max_length=255)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title_lat or "Untitled"
