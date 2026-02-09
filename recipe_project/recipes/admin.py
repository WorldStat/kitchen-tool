from django.contrib import admin
from .models import Recipe

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'servings', 'created_at')
    list_filter = ('created_at', 'owner')
    search_fields = ('title', 'ingredients', 'owner__username')
    ordering = ('-created_at',)