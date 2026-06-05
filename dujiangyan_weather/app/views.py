from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg, Max, Min, Count
from .models import WeatherData, MonthlyStats
import json


def index(request):
    """主页面"""
    return render(request, 'index.html')


def api_weather_list(request):
    """获取天气数据列表"""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 30))
    start = (page - 1) * page_size
    end = start + page_size

    queryset = WeatherData.objects.all()
    total = queryset.count()
    data = list(queryset[start:end].values())

    return JsonResponse({
        'code': 0,
        'data': data,
        'total': total,
        'page': page,
        'page_size': page_size
    })


def api_monthly_stats(request):
    """获取月度统计数据"""
    year = request.GET.get('year')
    queryset = MonthlyStats.objects.all()
    if year:
        queryset = queryset.filter(year=year)
    data = list(queryset.values())
    return JsonResponse({'code': 0, 'data': data})


def api_summary(request):
    """获取数据概览"""
    total_days = WeatherData.objects.count()
    latest = WeatherData.objects.first()
    earliest = WeatherData.objects.last()

    avg_max = WeatherData.objects.aggregate(avg=Avg('max_temp'))['avg']
    avg_min = WeatherData.objects.aggregate(avg=Avg('min_temp'))['avg']

    return JsonResponse({
        'code': 0,
        'data': {
            'total_days': total_days,
            'date_range': f"{earliest.date if earliest else '-'} ~ {latest.date if latest else '-'}",
            'avg_max_temp': round(avg_max, 2) if avg_max else None,
            'avg_min_temp': round(avg_min, 2) if avg_min else None,
        }
    })
