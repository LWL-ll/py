"""
模块四：数据分析（analyzer.py）
依据前端所需，对清洗后的天气数据进行统计分析和月度汇总，
生成：月度统计、气候评分、穿衣建议、天气分布、热力图数据等。
"""

import pandas as pd
import numpy as np
import logging
from django.db.models import Avg, Max, Min, Count, Q
from app.models import WeatherData, MonthlyStats, ClothingAdvice, ForecastData
from app.ai_advisor import generate_ai_advice

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

        # 优先用 AI 生成智能建议，失败则回退规则引擎
        try:
            ai_result = generate_ai_advice(f"{y}-{m:02d}")
            if ai_result:
                # AI 成功，直接写入数据库
                all_tags = []
                for cat in ai_result.values():
                    all_tags.extend(cat.get('tags', []))
                ClothingAdvice.objects.update_or_create(
                    month=f"{y}-{m:02d}",
                    defaults={
                        'advice_text': ' '.join(c.get('advice', '') for c in ai_result.values()),
                        'tags': list(set(all_tags)),
                        'advice_categories': ai_result,
                    }
                )
                logger.info(f"{y}-{m:02d} AI 建议已生成")
            else:
                raise Exception('AI 返回空')
        except Exception as e:
            logger.warning(f"AI 建议失败({e})，回退规则引擎")
            generate_comprehensive_advice(y, m)

    logger.info("月度统计与气候评分生成完成")


def generate_comprehensive_advice(year: int, month: int):
    """
    综合历史数据与未来预报，生成多维度智能建议。

    数据来源：
        - 历史数据：WeatherData（近 60 天实际观测）
        - 预报数据：ForecastData（未来 40 天预报）
        - 月度统计：MonthlyStats

    生成 5 类建议：穿衣/出行/运动/健康/预警
    """
    from datetime import date, timedelta

    stats = MonthlyStats.objects.filter(year=year, month=month).first()
    if not stats:
        return

    # ---------- 数据准备 ----------
    today = date.today()
    hist_start = today - timedelta(days=60)
    hist_qs = WeatherData.objects.filter(date__gte=hist_start).order_by('date')
    forecast_qs = ForecastData.objects.all().order_by('date')[:14]

    # 历史统计
    hist_count = hist_qs.count()
    hist_avg_max = hist_qs.aggregate(a=Avg('max_temp'))['a'] or 0
    hist_avg_min = hist_qs.aggregate(a=Avg('min_temp'))['a'] or 0
    hist_rain_days = hist_qs.filter(weather_desc__icontains='雨').count() if hist_count else 0
    hist_avg_humidity = hist_qs.aggregate(a=Avg('humidity'))['a'] or 50

    # 预报统计
    fc_count = forecast_qs.count()
    fc_avg_high = forecast_qs.aggregate(a=Avg('day_temp'))['a'] or 0
    fc_avg_low = forecast_qs.aggregate(a=Avg('night_temp'))['a'] or 0
    fc_rain_days = sum(1 for f in forecast_qs if f.weather_desc and '雨' in f.weather_desc)
    fc_max_temp = max((f.day_temp or 0) for f in forecast_qs) if fc_count else 0
    fc_min_temp = min((f.night_temp or 99) for f in forecast_qs) if fc_count else 99

    # 综合判断用：取历史+预报的"代表性"值
    rep_high = (hist_avg_max + fc_avg_high) / 2 if fc_count else hist_avg_max
    rep_low = (hist_avg_min + fc_avg_low) / 2 if fc_count else hist_avg_min
    temp_range = rep_high - rep_low

    categories = {}

    # ==================== 1. 穿衣建议 ====================
    clothing_tags = []
    clothing_parts = []

    if rep_high > 32:
        clothing_parts.append("气温较高，建议穿着轻薄透气的短袖短裤，注意防晒补水。")
        clothing_tags.extend(["短袖", "防晒霜", "遮阳帽"])
    elif rep_high > 26:
        clothing_parts.append("气温偏热，建议穿着透气舒适的短袖或薄长袖。")
        clothing_tags.extend(["短袖", "薄长袖"])
    elif rep_high > 20:
        clothing_parts.append("气温适宜，可穿着薄外套或长袖衬衫，体感舒适。")
        clothing_tags.append("薄外套")
    elif rep_high > 12:
        clothing_parts.append("气温偏凉，建议穿着保暖外套或毛衣，注意防风。")
        clothing_tags.extend(["厚外套", "毛衣"])
    else:
        clothing_parts.append("气温较低，请注意保暖，建议穿着羽绒服或棉衣。")
        clothing_tags.extend(["羽绒服", "围巾", "手套"])

    if rep_low < 5:
        clothing_parts.append("早晚寒冷，建议内穿保暖内衣。")
        clothing_tags.append("保暖内衣")
    elif temp_range > 10:
        clothing_parts.append(f"昼夜温差较大（约{temp_range:.0f}°C），外出建议携带一件外套。")
        clothing_tags.append("外套")

    if hist_avg_humidity > 75:
        clothing_parts.append("空气湿度较大，建议选择吸湿透气的面料。")
        clothing_tags.append("透气面料")

    categories['clothing'] = {
        'advice': ' '.join(clothing_parts),
        'tags': list(set(clothing_tags)),
    }

    # ==================== 2. 出行建议 ====================
    travel_tags = []
    travel_parts = []

    if fc_rain_days >= 5:
        travel_parts.append(f"未来两周降雨频繁（{fc_rain_days}天），出行务必携带雨具，注意路面湿滑。")
        travel_tags.extend(["雨伞", "防水鞋"])
    elif fc_rain_days >= 2:
        travel_parts.append(f"未来两周有{fc_rain_days}天可能降雨，建议随身携带折叠伞。")
        travel_tags.append("折叠伞")
    else:
        travel_parts.append("未来两周降雨较少，出行无需特别准备雨具。")
        travel_tags.append("晴好")

    if fc_max_temp > 35:
        travel_parts.append("将出现高温天气，避免中午时段户外活动，注意防暑降温。")
        travel_tags.append("防暑")
    elif fc_min_temp < 0:
        travel_parts.append("将出现零下低温，注意路面结冰，驾车减速慢行。")
        travel_tags.append("防滑")

    if rep_high >= 20 and fc_rain_days <= 2:
        travel_parts.append("天气条件适合短途旅行和户外郊游。")
        travel_tags.append("适合出游")

    categories['travel'] = {
        'advice': ' '.join(travel_parts),
        'tags': list(set(travel_tags)),
    }

    # ==================== 3. 运动建议 ====================
    exercise_tags = []
    exercise_parts = []

    if 15 <= rep_high <= 28 and rep_low >= 10 and fc_rain_days <= 3:
        exercise_parts.append("温度适中，降雨较少，非常适合户外运动：跑步、骑行、球类运动皆宜。")
        exercise_tags.extend(["跑步", "骑行", "户外运动"])
    elif rep_high > 28 and rep_high <= 33:
        exercise_parts.append("气温偏高，建议早晨或傍晚运动，避开正午高温时段，注意补充水分。")
        exercise_tags.extend(["晨跑", "夜跑", "游泳"])
    elif rep_high > 33:
        exercise_parts.append("高温天气，建议选择室内运动（游泳、健身、瑜伽），户外运动有中暑风险。")
        exercise_tags.extend(["游泳", "健身房", "瑜伽"])
    elif rep_high < 10:
        exercise_parts.append("气温偏低，户外运动前充分热身，建议选择室内运动保暖。")
        exercise_tags.extend(["热身", "室内运动"])
    else:
        exercise_parts.append("天气条件一般，适当运动即可，注意根据体感调整强度。")
        exercise_tags.append("适度运动")

    if fc_rain_days >= 4:
        exercise_parts.append("降雨较多时可选择室内运动替代。")
        exercise_tags.append("室内优先")

    categories['exercise'] = {
        'advice': ' '.join(exercise_parts),
        'tags': list(set(exercise_tags)),
    }

    # ==================== 4. 健康建议 ====================
    health_tags = []
    health_parts = []

    if hist_avg_humidity > 80:
        health_parts.append("空气湿度较高，容易滋生细菌，注意食品卫生和室内通风。")
        health_tags.extend(["通风", "除湿"])
    elif hist_avg_humidity < 30:
        health_parts.append("空气干燥，注意皮肤保湿，多喝水，可使用加湿器。")
        health_tags.extend(["保湿", "加湿器"])

    if temp_range > 12:
        health_parts.append(f"昼夜温差大（约{temp_range:.0f}°C），容易感冒，注意及时增减衣物。")
        health_tags.append("防感冒")

    if hist_rain_days > 8:
        health_parts.append("近期多雨潮湿，关节不适者注意保暖防潮。")
        health_tags.append("关节保暖")

    if rep_high > 30:
        health_parts.append("高温天气注意防暑降温，多饮温水，避免长时间日晒。")
        health_tags.extend(["防中暑", "多饮水"])

    if not health_parts:
        health_parts.append("当前天气状况良好，保持正常作息和适量运动即可。")
        health_tags.append("良好")

    categories['health'] = {
        'advice': ' '.join(health_parts),
        'tags': list(set(health_tags)),
    }

    # ==================== 5. 天气预警 ====================
    alert_tags = []
    alert_parts = []
    alert_level = 'normal'  # normal / warning / danger

    if fc_max_temp >= 38:
        alert_parts.append("⚠️ 高温红色预警：未来将出现 38°C 以上极端高温，注意防暑！")
        alert_tags.append("高温预警")
        alert_level = 'danger'
    elif fc_max_temp >= 35:
        alert_parts.append("⚠️ 高温橙色预警：未来将出现 35°C 以上高温天气。")
        alert_tags.append("高温预警")
        alert_level = 'warning'

    if fc_min_temp <= -5:
        alert_parts.append("⚠️ 低温预警：未来将出现 -5°C 以下极端低温，注意防寒保暖！")
        alert_tags.append("低温预警")
        alert_level = 'danger'
    elif fc_min_temp <= 0:
        alert_parts.append("⚠️ 低温预警：未来将出现零下低温，注意防寒防冻。")
        alert_tags.append("低温预警")
        alert_level = 'warning'

    # 强降雨预警（预报中连续多天有"大雨"或"暴雨"）
    heavy_rain = sum(1 for f in forecast_qs if f.weather_desc and ('大' in f.weather_desc or '暴' in f.weather_desc))
    if heavy_rain >= 2:
        alert_parts.append(f"⚠️ 强降雨预警：未来有{heavy_rain}天可能出现大雨或暴雨，注意防范。")
        alert_tags.append("暴雨预警")
        alert_level = 'warning'

    if temp_range > 15:
        alert_parts.append(f"⚠️ 温差预警：昼夜温差超过15°C，注意适时增减衣物。")
        alert_tags.append("温差预警")
        if alert_level == 'normal':
            alert_level = 'warning'

    if not alert_parts:
        alert_parts.append("未来天气平稳，无极端天气预警。")
        alert_tags.append("无预警")

    categories['alert'] = {
        'advice': ' '.join(alert_parts),
        'tags': list(set(alert_tags)),
        'level': alert_level,
    }

    # 生成综合摘要
    all_advice_texts = [c['advice'] for c in categories.values()]
    summary_text = ' '.join(all_advice_texts)

    # 合并所有标签
    all_tags = []
    for c in categories.values():
        all_tags.extend(c.get('tags', []))

    # 保存到数据库
    ClothingAdvice.objects.update_or_create(
        month=f"{year}-{month:02d}",
        defaults={
            'advice_text': summary_text,
            'tags': list(set(all_tags)),
            'advice_categories': categories,
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
