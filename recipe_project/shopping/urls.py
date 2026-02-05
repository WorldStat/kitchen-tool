from django.urls import path
from . import views

urlpatterns = [
    # The detail view for a specific generated list
    path('list/<int:pk>/', views.shopping_list_detail, name='shopping_list_detail'),
    
    # Optional: A view to see all historical shopping lists
    path('history/', views.shopping_list_history, name='shopping_list_history'),
    
    # AJAX/API endpoint to toggle items (for a truly frictionless experience)
    path('item/<int:item_id>/toggle/', views.toggle_item, name='toggle_item'),
]