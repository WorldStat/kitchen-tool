from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.recipe_list, name='recipe_list'),
    path('create/', views.create_recipe, name='create_recipe'),
]