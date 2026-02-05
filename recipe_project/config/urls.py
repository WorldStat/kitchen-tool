from django.contrib import admin
from django.urls import path, include
# Ensure your views.py actually has this class-based view
from recipes.views import LandingPageView 

urlpatterns = [
    # Landing page at root
    path('', LandingPageView.as_view(), name='landing_page'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # App inclusions
    path('recipes/', include('recipes.urls')),
    path('users/', include('users.urls')),
]