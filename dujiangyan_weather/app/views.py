import json
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.db.models import Avg, Max, Min, Count
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_GET
from lauth.decorators import login_required

from .models import WeatherData, MonthlyStats, ClothingAdvice, CrawlTask, ForecastData
from .analyzer import (
    get_weather_distribution,
    get_climate_scores,
    get_heatmap_data,
    generate_monthly_stats,
    analyze_all,
)


# ==================== SPA 入口 ====================

@login_required
@ensure_csrf_cookie
def index(request):
    """主页面 - 返回打包后的 React SPA（需登录，同时设置 CSRF Cookie）"""
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

    # 计算晴天/雨天概率（按天气描述含关键词统计，复合天气如"多云~晴"同时计入）
    sunny_days = WeatherData.objects.filter(weather_desc__icontains='晴').count()
    rainy_days = WeatherData.objects.filter(weather_desc__icontains='雨').count()
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
            'categories': advice.advice_categories or {},
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

@login_required
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

@login_required
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


# ==================== 温度趋势（历史+预报） ====================

def api_temperature_trend(request):
    """获取温度趋势数据：历史月均 + 未来7天预报"""
    from datetime import date, timedelta
    from django.db.models.functions import TruncMonth

    # 历史月均温度
    monthly = list(
        WeatherData.objects
        .annotate(month_date=TruncMonth('date'))
        .values('month_date')
        .annotate(avg_max=Avg('max_temp'), avg_min=Avg('min_temp'))
        .order_by('month_date')
    )
    hist_data = []
    for m in monthly[-12:]:  # 近12个月
        dt = m['month_date']
        hist_data.append({
            'label': f"{dt.month}月",
            'avgMax': round(m['avg_max'], 1) if m['avg_max'] else None,
            'avgMin': round(m['avg_min'], 1) if m['avg_min'] else None,
            'type': 'history',
        })

    # 未来7天预报
    today = date.today()
    forecast_qs = ForecastData.objects.filter(
        date__gte=today, date__lte=today + timedelta(days=7)
    ).order_by('date')

    fc_data = []
    for f in forecast_qs:
        fc_data.append({
            'label': f"{f.date.month}/{f.date.day}",
            'avgMax': float(f.day_temp) if f.day_temp else None,
            'avgMin': float(f.night_temp) if f.night_temp else None,
            'type': 'forecast',
        })

    return JsonResponse({
        'code': 0,
        'data': {
            'history': hist_data,
            'forecast': fc_data,
        }
    })


# ==================== 40天预报 ====================

def api_forecast_list(request):
    """获取 40 天预报数据"""
    data = list(ForecastData.objects.all().order_by('date').values())
    return JsonResponse({'code': 0, 'data': data})


@login_required
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


# ==================== AI 智能模块 ====================

@require_POST
def api_ai_advice(request):
    """AI 生成智能生活建议"""
    try:
        import json as json_module
        body = json_module.loads(request.body)
        month = body.get('month', '')

        from app.ai_advisor import generate_ai_advice
        result = generate_ai_advice(month)

        if result:
            return JsonResponse({'code': 0, 'data': result})
        else:
            return JsonResponse({'code': 1, 'message': 'AI 生成失败'})
    except Exception as e:
        return JsonResponse({'code': 500, 'message': str(e)})


@require_POST
def api_ai_chat(request):
    """AI 天气问答（返回流式或普通文本）"""
    try:
        import json as json_module
        body = json_module.loads(request.body)
        question = body.get('question', '').strip()
        month = body.get('month', '')

        if not question:
            return JsonResponse({'code': 1, 'message': '请输入问题'})

        from app.ai_advisor import chat_about_weather
        answer = chat_about_weather(question, month)

        return JsonResponse({'code': 0, 'data': {'answer': answer}})
    except Exception as e:
        return JsonResponse({'code': 500, 'message': str(e)})


# ==================== 今日天气详情 ====================

def api_today_weather(request):
    """获取今日天气详情（温度/湿度/风力/空气质量/体感）"""
    from datetime import date

    today = date.today()
    result = {
        'date': today.isoformat(),
        'max_temp': None,
        'min_temp': None,
        'weather_desc': '',
        'weather_type': '',
        'humidity': None,
        'wind_direction': '',
        'wind_level': '',
        'air_quality_score': None,
        'temp_comfort_score': None,
        'source': 'none',
    }

    # 1. 尝试从历史数据获取今天的记录
    hist = WeatherData.objects.filter(date=today).first()
    if hist:
        result.update({
            'max_temp': hist.max_temp,
            'min_temp': hist.min_temp,
            'weather_desc': hist.weather_desc,
            'weather_type': hist.weather_type,
            'humidity': hist.humidity,
            'wind_direction': hist.wind_direction,
            'wind_level': hist.wind_level,
            'source': 'history',
        })

    # 2. 如果历史数据没有温度，从预报补充
    fc = ForecastData.objects.filter(date=today).first()
    if fc:
        if result['max_temp'] is None:
            result['max_temp'] = float(fc.day_temp) if fc.day_temp else None
        if result['min_temp'] is None:
            result['min_temp'] = float(fc.night_temp) if fc.night_temp else None
        if not result['weather_desc']:
            result['weather_desc'] = fc.weather_desc
        if not result['source'] or result['source'] == 'none':
            result['source'] = 'forecast'

    # 3. 当月气候评分（空气质量和舒适度）
    stats = MonthlyStats.objects.filter(year=today.year, month=today.month).first()
    if stats:
        result['air_quality_score'] = stats.air_quality_score
        result['temp_comfort_score'] = stats.temp_comfort_score

    return JsonResponse({'code': 0, 'data': result})

# ==================== 天气月历 ====================

def api_weather_calendar(request):
    """获取指定月份的日历数据（每天一格）"""
    year = request.GET.get('year')
    month = request.GET.get('month')
    if not year or not month:
        return JsonResponse({'code': 1, 'message': '请提供 year 和 month 参数'})

    from datetime import date, timedelta
    import calendar

    y, m = int(year), int(month)

    # 当月所有天气数据
    data_map = {}
    for w in WeatherData.objects.filter(date__year=y, date__month=m):
        data_map[w.date.day] = {
            'max_temp': w.max_temp,
            'min_temp': w.min_temp,
            'weather_desc': w.weather_desc,
            'weather_type': w.weather_type,
        }

    # 当月预报数据
    fc_map = {}
    for f in ForecastData.objects.filter(date__year=y, date__month=m):
        fc_map[f.date.day] = {
            'max_temp': float(f.day_temp) if f.day_temp else None,
            'min_temp': float(f.night_temp) if f.night_temp else None,
            'weather_desc': f.weather_desc,
        }

    # 构建日历网格
    cal = calendar.Calendar(firstweekday=0)  # 周一开头
    weeks = []
    for week in cal.monthdatescalendar(y, m):
        week_data = []
        for d in week:
            day_info = {
                'date': d.isoformat(),
                'day': d.day,
                'is_current_month': d.month == m,
                'is_today': d == date.today(),
            }
            if d.month == m:
                hist = data_map.get(d.day)
                fc = fc_map.get(d.day)
                if hist:
                    day_info['max_temp'] = hist['max_temp']
                    day_info['min_temp'] = hist['min_temp']
                    day_info['weather_desc'] = hist['weather_desc']
                    day_info['weather_type'] = hist['weather_type']
                    day_info['source'] = 'history'
                elif fc:
                    day_info['max_temp'] = fc['max_temp']
                    day_info['min_temp'] = fc['min_temp']
                    day_info['weather_desc'] = fc['weather_desc']
                    day_info['weather_type'] = ''
                    day_info['source'] = 'forecast'
            week_data.append(day_info)
        weeks.append(week_data)

    return JsonResponse({'code': 0, 'data': {'weeks': weeks, 'year': y, 'month': m}})


# ==================== AI 天气日记 ====================

@require_POST
def api_ai_diary(request):
    """AI 生成每日天气叙事日记"""
    try:
        from datetime import date
        from app.ai_advisor import _build_weather_context, _call_ai

        context = _build_weather_context()
        prompt = f"""根据以下天气数据，写一段 100 字左右的天气日记。要求：
- 以"今天是{date.today().strftime('%Y年%m月%d日')}"开头
- 像讲故事一样描述最近的天气变化
- 语气温暖，有文学感
- 结合具体数字（温度、降雨天数等）
- 提到都江堰的气候特点

{context}"""

        diary = _call_ai([
            {'role': 'system', 'content': '你是一个有文学素养的天气记录者，用温暖细腻的笔触记录天气。'},
            {'role': 'user', 'content': prompt},
        ], temperature=0.8)

        return JsonResponse({'code': 0, 'data': {'diary': diary}})
    except Exception as e:
        return JsonResponse({'code': 500, 'message': str(e)})
