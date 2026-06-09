from django.urls import path
from . import views

urlpatterns = [
    # SPA 入口
    path('', views.index, name='index'),

    # 核心数据 API
    path('api/weather/list/', views.api_weather_list, name='api_weather_list'),
    path('api/weather/monthly/', views.api_monthly_stats, name='api_monthly_stats'),
    path('api/weather/summary/', views.api_summary, name='api_summary'),

    # 图表与分析 API（新增）
    path('api/weather/distribution/', views.api_weather_distribution, name='api_weather_distribution'),
    path('api/weather/climate-score/', views.api_climate_score, name='api_climate_score'),
    path('api/weather/heatmap/', views.api_heatmap, name='api_heatmap'),
    path('api/weather/advice/', views.api_clothing_advice, name='api_clothing_advice'),
    path('api/weather/months/', views.api_available_months, name='api_available_months'),

    # 操作 API
    path('api/weather/crawl/', views.api_crawl, name='api_crawl'),
    path('api/weather/analyze/', views.api_analyze, name='api_analyze'),

    # 温度趋势（历史+预报合并）
    path('api/weather/temperature-trend/', views.api_temperature_trend, name='api_temperature_trend'),

    # 40天预报 API
    path('api/weather/forecast/', views.api_forecast_list, name='api_forecast_list'),
    path('api/weather/forecast/fetch/', views.api_forecast_fetch, name='api_forecast_fetch'),

    # AI 智能模块
    path('api/weather/ai-advice/', views.api_ai_advice, name='api_ai_advice'),
    path('api/weather/ai-chat/', views.api_ai_chat, name='api_ai_chat'),
    path('api/weather/ai-diary/', views.api_ai_diary, name='api_ai_diary'),

    # 天气月历
    path('api/weather/calendar/', views.api_weather_calendar, name='api_weather_calendar'),
]
