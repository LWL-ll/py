import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.db.models import Avg, Max, Min, Count
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_GET

from .models import WeatherData, MonthlyStats, ClothingAdvice, CrawlTask, ForecastData
from .analyzer import (
    get_weather_distribution,
    get_climate_scores,
    get_heatmap_data,
    generate_monthly_stats,
    analyze_all,
)


# ==================== SPA 入口 ====================

@ensure_csrf_cookie
def index(request):
    """主页面 - 返回打包后的 React SPA（同时设置 CSRF Cookie 供前端 POST 请求使用）"""
    index_path = settings.BASE_DIR / 'static' / 'dist' / 'index.html'
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse(
            '<h1>Frontend not built</h1><p>Please run <code>npm run build</code> in the static directory.</p>',
            content_type='text/html',
            status=404
        )


# ==================== 数据列表 ====================

def api_weather_list(request):
    """获取天气数据列表（支持分页、按年月筛选）"""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 30))
    year = request.GET.get('year')
    month = request.GET.get('month')

    queryset = WeatherData.objects.all()
    if year:
        queryset = queryset.filter(date__year=int(year))
    if month:
        queryset = queryset.filter(date__month=int(month))

    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    data = list(queryset[start:end].values())

    return JsonResponse({
        'code': 0,
        'data': data,
        'total': total,
        'page': page,
        'page_size': page_size
    })


# ==================== 月度统计 ====================

def api_monthly_stats(request):
    """获取月度统计数据（可按年、月筛选）"""
    year = request.GET.get('year')
    month = request.GET.get('month')
    queryset = MonthlyStats.objects.all()
    if year:
        queryset = queryset.filter(year=int(year))
    if month:
        queryset = queryset.filter(month=int(month))
    data = list(queryset.values())
    return JsonResponse({'code': 0, 'data': data})


# ==================== 数据概览 ====================

def api_summary(request):
    """获取数据概览（支撑 StatsGrid 等汇总组件）"""
    total_days = WeatherData.objects.count()
    latest = WeatherData.objects.order_by('-date').first()
    earliest = WeatherData.objects.order_by('date').first()

    avg_max = WeatherData.objects.aggregate(avg=Avg('max_temp'))['avg']
    avg_min = WeatherData.objects.aggregate(avg=Avg('min_temp'))['avg']

    # 计算晴天/雨天概率（基于 weather_type）
    sunny_days = WeatherData.objects.filter(weather_type='sunny').count()
    rainy_days = WeatherData.objects.filter(weather_type='rainy').count()
    sunny_prob = round(sunny_days / total_days * 100, 1) if total_days else 0
    rainy_prob = round(rainy_days / total_days * 100, 1) if total_days else 0

    # 月均最高/最低温（基于 MonthlyStats 的平均）
    monthly_avg = MonthlyStats.objects.aggregate(
        avg_max=Avg('avg_max_temp'),
        avg_min=Avg('avg_min_temp'),
    )

    return JsonResponse({
        'code': 0,
        'data': {
            'total_days': total_days,
            'date_range': f"{earliest.date if earliest else '-'} ~ {latest.date if latest else '-'}",
            'avg_max_temp': round(avg_max, 2) if avg_max else None,
            'avg_min_temp': round(avg_min, 2) if avg_min else None,
            'sunny_probability': sunny_prob,
            'rainy_probability': rainy_prob,
            'monthly_avg_max_temp': round(monthly_avg['avg_max'], 2) if monthly_avg['avg_max'] else None,
            'monthly_avg_min_temp': round(monthly_avg['avg_min'], 2) if monthly_avg['avg_min'] else None,
        }
    })


# ==================== 天气分布（饼图）====================

def api_weather_distribution(request):
    """获取天气状况分布数据（PrimaryCharts 饼图用）"""
    year = request.GET.get('year')
    month = request.GET.get('month')
    data = get_weather_distribution(
        year=int(year) if year else None,
        month=int(month) if month else None,
    )
    return JsonResponse({'code': 0, 'data': data})


# ==================== 气候评分（雷达图）====================

def api_climate_score(request):
    """获取气候综合评分（SecondaryCharts 雷达图用）"""
    year = request.GET.get('year')
    month = request.GET.get('month')
    data = get_climate_scores(
        year=int(year) if year else None,
        month=int(month) if month else None,
    )
    return JsonResponse({'code': 0, 'data': data})


# ==================== 热力图数据 ====================

def api_heatmap(request):
    """获取年度温度热力分布数据（HeatmapChart 用）"""
    year = request.GET.get('year')
    data = get_heatmap_data(year=int(year) if year else None)
    return JsonResponse({'code': 0, 'data': data})


# ==================== 穿衣建议 ====================

def api_clothing_advice(request):
    """获取穿衣建议（InsightAndTable 用）"""
    month = request.GET.get('month')  # 格式：YYYY-MM
    if month:
        advice = ClothingAdvice.objects.filter(month=month).first()
    else:
        # 默认返回最近一个月的建议
        advice = ClothingAdvice.objects.order_by('-month').first()

    if not advice:
        return JsonResponse({'code': 0, 'data': None})

    return JsonResponse({
        'code': 0,
        'data': {
            'month': advice.month,
            'advice_text': advice.advice_text,
            'tags': advice.tags,
        }
    })


# ==================== 可用月份列表 ====================

def api_available_months(request):
    """获取数据库中已有数据的可用月份列表（ControlPanel 下拉用）"""
    months = WeatherData.objects.dates('date', 'month', order='DESC')
    data = []
    for m in months:
        data.append({
            'label': f"{m.year}年{m.month:02d}月",
            'value': f"{m.year}-{m.month:02d}",
            'year': m.year,
            'month': m.month,
        })
    return JsonResponse({'code': 0, 'data': data})


# ==================== 一键爬虫 ====================

@require_POST
def api_crawl(request):
    """触发爬虫抓取近12个月数据"""
    try:
        from app.crawler import crawl_last_12_months, parse_and_save

        raw_data = crawl_last_12_months()
        if raw_data:
            saved = parse_and_save(raw_data)
            return JsonResponse({
                'code': 0,
                'message': '爬取完成',
                'data': {'saved_count': saved}
            })
        else:
            return JsonResponse({
                'code': 1,
                'message': '未获取到任何数据',
                'data': {}
            })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'爬取异常: {str(e)}',
            'data': {}
        })


# ==================== 一键分析 ====================

@require_POST
def api_analyze(request):
    """触发数据分析：生成月度统计、气候评分与穿衣建议"""
    try:
        analyze_all()
        return JsonResponse({
            'code': 0,
            'message': '分析完成',
            'data': {}
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'分析异常: {str(e)}',
            'data': {}
        })


# ==================== 40天预报 ====================

def api_forecast_list(request):
    """获取 40 天预报数据"""
    data = list(ForecastData.objects.all().order_by('date').values())
    return JsonResponse({'code': 0, 'data': data})


@require_POST
def api_forecast_fetch(request):
    """触发爬取 40 天预报数据"""
    try:
        from app.crawler import fetch_forecast
        count = fetch_forecast()
        return JsonResponse({
            'code': 0,
            'message': f'预报爬取完成，保存 {count} 条',
            'data': {'count': count}
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'预报爬取异常: {str(e)}',
            'data': {}
        })
