"""
URL configuration for dujiangyan_weather project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('lauth/', include('lauth.urls')),
    path('', include('app.urls')),
]
