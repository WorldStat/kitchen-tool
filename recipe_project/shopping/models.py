from django.db import models
from django.conf import settings
from recipes.models import Recipe

class ShoppingList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    recipes = models.ManyToManyField(Recipe, related_name="shopping_lists")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"List for {self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"

class ShoppingItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    quantity = models.CharField(max_length=100, blank=True)
    checked = models.BooleanField(default=False)
    
    # ADD THIS LINE:
    source_recipe = models.ForeignKey('recipes.Recipe', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name