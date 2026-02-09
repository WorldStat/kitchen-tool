from django.contrib import admin
from .models import ShoppingList, ShoppingItem

# This lets you edit items directly inside the List page
class ShoppingItemInline(admin.TabularInline):
    model = ShoppingItem
    extra = 1  # Provides one empty row to add new items easily

@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'item_count')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    inlines = [ShoppingItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'