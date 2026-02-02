from django.urls import path, include
from . import views

urlpatterns = [
    # Custom Registration View
    path('register/', views.register, name='register'),
    
    # Built-in Auth views (login, logout, password_reset, etc.)
    # Django looks for templates in 'registration/' by default
    path('', include('django.contrib.auth.urls')),
]