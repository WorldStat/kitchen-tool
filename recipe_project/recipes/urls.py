from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.recipe_list, name='recipe_list'),
    path('create/', views.create_recipe, name='create_recipe'),
    
    # AJAX API Endpoint for Bedrock Scraper
    path('api/scrape/', views.scrape_recipe_api, name='scrape_api'),

    # New Detail View
    path('<int:pk>/', views.recipe_detail, name='recipe_detail'),

    # Editing Recipe Ingredients
    path('<int:pk>/edit/', views.recipe_edit, name='recipe_edit'),
    
    path('<int:pk>/delete/', views.recipe_delete, name='recipe_delete'),
    path('<int:pk>/clone/', views.clone_recipe, name='clone_recipe'),
]