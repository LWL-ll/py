from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/weather/list/', views.api_weather_list, name='api_weather_list'),
    path('api/weather/monthly/', views.api_monthly_stats, name='api_monthly_stats'),
    path('api/weather/summary/', views.api_summary, name='api_summary'),
]
