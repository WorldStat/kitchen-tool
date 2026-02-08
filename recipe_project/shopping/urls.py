from django.urls import path
from . import views

urlpatterns = [
    # ... your existing path for 'history' ...
    path('list/', views.shopping_list_history, name='shopping_list_history'),

    # NEW: The Detail View
    path('list/<int:pk>/', views.shopping_list_detail, name='shopping_list_detail'),
    
    # NEW: The "Click" Action
    path('item/<int:item_id>/toggle/', views.toggle_item, name='toggle_item'),
]