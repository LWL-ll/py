"""
模块四：数据分析（analyzer.py）
依据前端所需，对清洗后的天气数据进行统计分析和月度汇总，
生成：月度统计、气候评分、穿衣建议、天气分布、热力图数据等。
"""

import pandas as pd
import numpy as np
import logging
from django.db.models import Avg, Max, Min, Count, Q
from app.models import WeatherData, MonthlyStats, ClothingAdvice

logger = logging.getLogger(__name__)


def generate_monthly_stats(year: int = None, month: int = None):
    """
    生成月度统计数据，包含前端所需的全部字段：
    温度统计、降雨天数、天气分布、5项气候综合评分。
    """
    qs = WeatherData.objects.all()
    if year:
        qs = qs.filter(date__year=year)
    if month:
        qs = qs.filter(date__month=month)

    df = pd.DataFrame(qs.values())
    if df.empty:
        logger.warning("无数据可分析")
        return

    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

    grouped = df.groupby(['year', 'month'])
    for (y, m), group in grouped:
        total_days = len(group)
        avg_max = group['max_temp'].mean()
        avg_min = group['min_temp'].mean()
        max_record = group['max_temp'].max()
        min_record = group['min_temp'].min()
        rainy_days = int(group['weather_desc'].astype(str).str.contains('雨').sum())
        avg_humidity = group['humidity'].mean() if 'humidity' in group.columns else None

        # --- 天气分布（JSON） ---
        weather_dist = group['weather_desc'].value_counts().to_dict()

        # --- 5项气候评分 ---
        temp_score = _calc_temp_comfort_score(group)
        humidity_score = _calc_humidity_comfort_score(avg_humidity)
        sunlight_score = _calc_sunlight_score(group)
        air_score = _calc_air_quality_score(group)
        precipitation_score = _calc_precipitation_score(rainy_days)

        MonthlyStats.objects.update_or_create(
            year=y,
            month=m,
            defaults={
                'avg_max_temp': round(avg_max, 2) if pd.notna(avg_max) else None,
                'avg_min_temp': round(avg_min, 2) if pd.notna(avg_min) else None,
                'max_temp_record': round(max_record, 2) if pd.notna(max_record) else None,
                'min_temp_record': round(min_record, 2) if pd.notna(min_record) else None,
                'rainy_days': rainy_days,
                'avg_humidity': round(avg_humidity, 2) if pd.notna(avg_humidity) else None,
                'weather_distribution': weather_dist,
                'temp_comfort_score': temp_score,
                'humidity_comfort_score': humidity_score,
                'sunlight_score': sunlight_score,
                'air_quality_score': air_score,
                'precipitation_score': precipitation_score,
            }
        )

        # 同步生成穿衣建议
        generate_clothing_advice(y, m)

    logger.info("月度统计与气候评分生成完成")


def generate_clothing_advice(year: int, month: int):
    """
    根据月度天气特征生成穿衣建议文本与标签。
    """
    stats = MonthlyStats.objects.filter(year=year, month=month).first()
    if not stats:
        return

    avg_max = stats.avg_max_temp or 0
    avg_min = stats.avg_min_temp or 0
    rainy = stats.rainy_days or 0

    tags = []
    advice_parts = []

    # 温度建议
    if avg_max > 32:
        advice_parts.append("气温较高，建议穿着轻薄透气的短袖、短裤，注意防晒补水。")
        tags.extend(["短袖", "防晒"])
    elif avg_max > 26:
        advice_parts.append("气温偏热，建议穿着透气舒适的短袖或薄长袖。")
        tags.append("短袖")
    elif avg_max > 20:
        advice_parts.append("气温适宜，可穿着薄外套或长袖衬衫，体感舒适。")
        tags.append("薄外套")
    elif avg_max > 12:
        advice_parts.append("气温偏凉，建议穿着保暖外套或毛衣，注意防风。")
        tags.extend(["厚外套", "毛衣"])
    else:
        advice_parts.append("气温较低，请注意保暖，建议穿着羽绒服或棉衣，佩戴围巾手套。")
        tags.extend(["羽绒服", "围巾"])

    # 最低温补充
    if avg_min < 5:
        advice_parts.append("早晚寒冷，建议内穿保暖内衣。")
        tags.append("保暖内衣")
    elif avg_min < 12:
        advice_parts.append("早晚温差较大，外出建议携带一件外套。")
        tags.append("外套")

    # 降雨建议
    if rainy > 12:
        advice_parts.append(f"本月降雨频繁（{rainy}天），请随身携带雨具，注意路面湿滑。")
        tags.append("雨具")
    elif rainy > 6:
        advice_parts.append(f"本月有{rainy}天降雨，出行建议备好雨伞或雨衣。")
        tags.append("雨具")

    # 湿度补充
    if stats.avg_humidity and stats.avg_humidity > 75:
        advice_parts.append("空气湿度较大，建议选择吸湿透气的面料。")
        tags.append("透气面料")

    advice_text = " ".join(advice_parts)

    ClothingAdvice.objects.update_or_create(
        month=f"{year}-{month:02d}",
        defaults={
            'advice_text': advice_text,
            'tags': list(set(tags)),  # 去重
        }
    )


def get_weather_distribution(year: int = None, month: int = None) -> list:
    """
    获取天气分布数据（饼图用）。
    返回: [{name, value, color}, ...]
    """
    qs = MonthlyStats.objects.all()
    if year:
        qs = qs.filter(year=year)
    if month:
        qs = qs.filter(month=month)

    # 汇总多个月的天气分布
    total_dist = {}
    for stat in qs:
        for desc, count in (stat.weather_distribution or {}).items():
            total_dist[desc] = total_dist.get(desc, 0) + count

    # 映射到前端所需的颜色与名称
    # 按子串归类：含"雨"→雨色，含"雪"→雪色，以此类推
    color_map = {
        '晴': '#D4A373',
        '多云': '#A8A29E',
        '阴': '#78716C',
        '雨': '#7FA3C1',
        '雪': '#B8C5D6',
    }
    default_color = '#9CA3AF'

    def get_color(desc: str) -> str:
        """根据天气描述子串匹配颜色"""
        if not desc:
            return default_color
        if '雪' in desc:
            return color_map['雪']
        if '雨' in desc:
            return color_map['雨']
        if '雾' in desc or '霾' in desc:
            return '#A8A29E'  # 雾霾用灰色
        if '多云' in desc:
            return color_map['多云']
        if '阴' in desc:
            return color_map['阴']
        if '晴' in desc:
            return color_map['晴']
        return default_color

    result = []
    for name, value in total_dist.items():
        result.append({
            'name': name,
            'value': value,
            'color': get_color(name),
        })

    # 按数量降序排列
    result.sort(key=lambda x: x['value'], reverse=True)
    return result


def get_climate_scores(year: int = None, month: int = None) -> list:
    """
    获取气候综合评分（雷达图用）。
    返回: [{category, value}, ...]
    """
    qs = MonthlyStats.objects.all()
    if year:
        qs = qs.filter(year=year)
    if month:
        qs = qs.filter(month=month)

    if not qs.exists():
        return []

    # 对多个月份取平均分
    avg = qs.aggregate(
        temp=Avg('temp_comfort_score'),
        humidity=Avg('humidity_comfort_score'),
        sunlight=Avg('sunlight_score'),
        air=Avg('air_quality_score'),
        precipitation=Avg('precipitation_score'),
    )

    categories = [
        ('温度舒适度', 'temp'),
        ('湿度适宜度', 'humidity'),
        ('日照充足度', 'sunlight'),
        ('空气质量', 'air'),
        ('降水适中度', 'precipitation'),
    ]

    result = []
    for label, key in categories:
        val = avg.get(key) or 0
        result.append({
            'category': label,
            'value': round(val),
        })
    return result


def get_heatmap_data(year: int = None) -> list:
    """
    生成年度温度热力分布数据（12个月 × 5个温度层级）。
    返回: [{month, row, temp}, ...]
    row 含义: 0=min, 1=25%, 2=median, 3=75%, 4=max
    """
    qs = WeatherData.objects.all()
    if year:
        qs = qs.filter(date__year=year)

    df = pd.DataFrame(qs.values('date', 'max_temp'))
    if df.empty:
        return []

    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month

    months = ['1月', '2月', '3月', '4月', '5月', '6月',
              '7月', '8月', '9月', '10月', '11月', '12月']

    result = []
    for month_idx, month_label in enumerate(months, 1):
        month_data = df[df['month'] == month_idx]['max_temp'].dropna()
        if len(month_data) == 0:
            continue

        stats = [
            month_data.min(),           # row 0: 最低温
            month_data.quantile(0.25),  # row 1: 25%分位
            month_data.median(),        # row 2: 中位数
            month_data.quantile(0.75),  # row 3: 75%分位
            month_data.max(),           # row 4: 最高温
        ]

        for row_idx, temp in enumerate(stats):
            result.append({
                'month': month_label,
                'row': row_idx,
                'temp': round(float(temp), 1) if pd.notna(temp) else None,
            })

    return result


def get_yearly_summary(year: int) -> dict:
    """
    获取某年的年度概览。
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
    获取极端天气统计。
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


def analyze_all():
    """
    一键分析：生成所有月度统计、气候评分与穿衣建议。
    """
    logger.info("开始生成月度统计...")
    generate_monthly_stats()
    logger.info("分析完成！")


# ==================== 内部评分算法 ====================

def _calc_temp_comfort_score(group: pd.DataFrame) -> int:
    """
    温度舒适度：基于每日最高温落在 [18, 30] 且最低温落在 [10, 25] 的天数比例。
    """
    if group.empty:
        return 50
    comfortable = group[
        (group['max_temp'] >= 18) & (group['max_temp'] <= 30) &
        (group['min_temp'] >= 10) & (group['min_temp'] <= 25)
    ]
    score = len(comfortable) / len(group) * 100
    return round(score)


def _calc_humidity_comfort_score(avg_humidity) -> int:
    """
    湿度适宜度：理想值 50%，偏离越大分数越低。
    """
    if avg_humidity is None or pd.isna(avg_humidity):
        return 50
    deviation = abs(float(avg_humidity) - 50)
    score = max(0, 100 - deviation * 2)
    return round(score)


def _calc_sunlight_score(group: pd.DataFrame) -> int:
    """
    日照充足度：晴天 + 多云 天数占比。
    """
    if group.empty or 'weather_type' not in group.columns:
        return 50
    sunny_cloudy = group[group['weather_type'].isin(['sunny', 'cloudy'])]
    score = len(sunny_cloudy) / len(group) * 100
    return round(score)


def _calc_air_quality_score(group: pd.DataFrame) -> int:
    """
    空气质量：综合晴天比例与降雨适中度计算。

    注意：由于本项目无实际 AQI/PM2.5 数据，此处使用天气类型作为空气质量
    的间接指标——晴天多表示大气扩散条件好，降雨适中（5-8天/月）有助于
    净化空气。评分范围为 0-100。
    """
    if group.empty or 'weather_type' not in group.columns:
        return 50
    total = len(group)
    sunny_days = len(group[group['weather_type'] == 'sunny'])
    rainy_days = len(group[group['weather_type'] == 'rainy'])

    # 晴天比例得分（权重 60%）：晴天越多，空气扩散条件越好
    sunny_ratio = sunny_days / total if total > 0 else 0
    sunny_score = sunny_ratio * 60  # 范围 [0, 60]

    # 降雨适中度得分（权重 40%）：每月 5-8 天降雨最佳，偏离越多分数越低
    rain_score_100 = max(0, 100 - abs(rainy_days - 6) * 12)  # 范围 [0, 100]
    rain_score = rain_score_100 * 0.4  # 缩放到 [0, 40]

    score = sunny_score + rain_score  # 范围 [0, 100]
    return round(score)


def _calc_precipitation_score(rainy_days: int) -> int:
    """
    降水适中度：每月 5-8 天降雨为最佳，偏离越多分数越低。
    """
    optimal = 6
    deviation = abs(rainy_days - optimal)
    score = max(0, 100 - deviation * 12)
    return round(score)
