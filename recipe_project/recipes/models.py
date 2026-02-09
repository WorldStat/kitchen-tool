from django.db import models
from django.conf import settings

class Recipe(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    ingredients = models.TextField()
    instructions = models.TextField()
    servings = models.IntegerField(default=1)
    image = models.ImageField(upload_to='recipe_photos/', null=True, blank=True)
    source_url = models.URLField(max_length=500, null=True, blank=True)
    
    # ADD THESE TWO LINES:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title