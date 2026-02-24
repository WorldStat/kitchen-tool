from django.urls import path, include
from . import views

urlpatterns = [
    # Custom Registration View
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('community/', views.public_cookbook, name='community_cookbook'),
    
    # Built-in Auth views (login, logout, password_reset, etc.)
    # Django looks for templates in 'registration/' by default
    path('', include('django.contrib.auth.urls')),
]