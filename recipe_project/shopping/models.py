from django.db import models
from django.conf import settings
from recipes.models import Recipe  # Ensure this import works

class ShoppingList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='shared_shopping_lists')
    # NEW: Allow users to name their list (e.g., "Sunday Dinner")
    title = models.CharField(max_length=100, default="My Shopping List") 
    created_at = models.DateTimeField(auto_now_add=True)
    recipes = models.ManyToManyField(Recipe, blank=True, related_name='shopping_lists')

    def __str__(self):
        return self.title

class ShoppingItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    quantity = models.CharField(max_length=100, blank=True)
    checked = models.BooleanField(default=False)
    source_recipe = models.ForeignKey(Recipe, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name