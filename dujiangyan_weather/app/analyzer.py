"""
模块四：分析模块
对清洗后的天气数据进行统计分析和月度汇总
"""

import pandas as pd
from django.db.models import Avg, Max, Min, Count, Q
from app.models import WeatherData, MonthlyStats


def generate_monthly_stats(year: int = None, month: int = None):
    """
    生成月度统计数据
    可指定年月，否则处理所有数据
    """
    qs = WeatherData.objects.all()
    if year:
        qs = qs.filter(date__year=year)
    if month:
        qs = qs.filter(date__month=month)

    df = pd.DataFrame(qs.values())
    if df.empty:
        print("无数据可分析")
        return

    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

    grouped = df.groupby(['year', 'month'])
    for (y, m), group in grouped:
        avg_max = group['max_temp'].mean()
        avg_min = group['min_temp'].mean()
        max_record = group['max_temp'].max()
        min_record = group['min_temp'].min()
        rainy_days = group['weather_desc'].str.contains('雨').sum()
        avg_humidity = group['humidity'].mean() if 'humidity' in group.columns else None

        MonthlyStats.objects.update_or_create(
            year=y,
            month=m,
            defaults={
                'avg_max_temp': round(avg_max, 2) if pd.notna(avg_max) else None,
                'avg_min_temp': round(avg_min, 2) if pd.notna(avg_min) else None,
                'max_temp_record': round(max_record, 2) if pd.notna(max_record) else None,
                'min_temp_record': round(min_record, 2) if pd.notna(min_record) else None,
                'rainy_days': int(rainy_days),
                'avg_humidity': round(avg_humidity, 2) if pd.notna(avg_humidity) else None,
            }
        )
    print("月度统计生成完成")


def get_yearly_summary(year: int) -> dict:
    """
    获取某年的年度概览
    """
    qs = WeatherData.objects.filter(date__year=year)
    if not qs.exists():
        return {}

    return {
        'year': year,
        'avg_max_temp': qs.aggregate(v=Avg('max_temp'))['v'],
        'avg_min_temp': qs.aggregate(v=Avg('min_temp'))['v'],
        'hottest_day': qs.order_by('-max_temp').first().date if qs.exists() else None,
        'coldest_day': qs.order_by('min_temp').first().date if qs.exists() else None,
        'total_rainy_days': qs.filter(weather_desc__icontains='雨').count(),
    }


def get_extreme_weather(year: int = None) -> dict:
    """
    获取极端天气统计
    """
    qs = WeatherData.objects.all()
    if year:
        qs = qs.filter(date__year=year)

    hottest = qs.order_by('-max_temp').first()
    coldest = qs.order_by('min_temp').first()

    return {
        'hottest': {
            'date': hottest.date if hottest else None,
            'temp': hottest.max_temp if hottest else None,
        },
        'coldest': {
            'date': coldest.date if coldest else None,
            'temp': coldest.min_temp if coldest else None,
        },
    }
