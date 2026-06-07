from django.contrib import admin
from app.models import WeatherData, MonthlyStats, ClothingAdvice, CrawlTask


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ('date', 'weather_desc', 'weather_type', 'max_temp', 'min_temp', 'wind_direction', 'wind_level', 'humidity')
    list_filter = ('weather_type', 'date')
    search_fields = ('date', 'weather_desc')
    date_hierarchy = 'date'


@admin.register(MonthlyStats)
class MonthlyStatsAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'avg_max_temp', 'avg_min_temp', 'rainy_days', 'avg_humidity', 'updated_at')
    list_filter = ('year', 'month')
    search_fields = ('year', 'month')


@admin.register(ClothingAdvice)
class ClothingAdviceAdmin(admin.ModelAdmin):
    list_display = ('month', 'advice_text', 'tags', 'updated_at')
    search_fields = ('month', 'advice_text')


@admin.register(CrawlTask)
class CrawlTaskAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'status', 'records_count', 'created_at', 'completed_at')
    list_filter = ('status', 'year')
    search_fields = ('year', 'month')
