from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.shopping_list_history, name='shopping_list_history'),
    path('create/', views.shopping_list_create, name='shopping_list_create'), # New
    path('list/<int:pk>/', views.shopping_list_detail, name='shopping_list_detail'),
    path('list/<int:pk>/edit/', views.shopping_list_edit, name='shopping_list_edit'), # New
    path('list/<int:pk>/add_item/', views.add_item, name='add_item'), # New
    path('list/<int:pk>/delete/', views.shopping_list_delete, name='shopping_list_delete'),
    path('generate/', views.generate_shopping_list, name='generate_shopping_list'),
    path('item/<int:item_id>/toggle/', views.toggle_item, name='toggle_item'),
]