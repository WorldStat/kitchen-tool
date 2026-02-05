from django.urls import path
from . import views

urlpatterns = [
    # Ensure this 'name' matches the {% url 'shopping_list_history' %} in base.html
    path('history/', views.shopping_list_history, name='shopping_list_history'),
    path('list/<int:pk>/', views.shopping_list_detail, name='shopping_list_detail'),
    path('item/<int:item_id>/toggle/', views.toggle_item, name='toggle_item'),
]