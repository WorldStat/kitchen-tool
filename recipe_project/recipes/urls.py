from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.recipe_list, name='recipe_list'),
    path('create/', views.create_recipe, name='create_recipe'),
    # New Detail View
    path('<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('<int:pk>/edit/', views.edit_recipe, name='edit_recipe'),
    path('<int:pk>/delete/', views.delete_recipe, name='delete_recipe'),
    # Shopping Logic
    path('generate-shopping/', views.generate_shopping_list, name='generate_shopping_list'),
    # Editing Recipe Ingredients
    path('<int:pk>/edit/', views.recipe_edit, name='recipe_edit'),
    
    path('<int:pk>/delete/', views.recipe_delete, name='recipe_delete'),
]