from django.contrib import admin
from django.urls import path, include
from recipes.views import LandingPageView

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing_page'),
    path('admin/', admin.site.urls),
    path('recipes/', include('recipes.urls')),
    path('users/', include('users.urls')), # Assuming you kept the users logic
]