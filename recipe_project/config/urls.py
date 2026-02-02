from django.contrib import admin
from django.urls import path, include
from recipes.views import LandingPageView 

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing_page'),
    path('admin/', admin.site.urls),
    
    # This connects the files above
    path('users/', include('users.urls')), 
    
    # Recipes App
    path('recipes/', include('recipes.urls')),
]