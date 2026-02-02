from django.db import models
from django.conf import settings

class Recipe(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    description = models.TextField(blank=True)
    ingredients = models.TextField(help_text="Separate ingredients by new line")
    instructions = models.TextField()
    servings = models.CharField(max_length=50, blank=True)
    is_public = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title