"""
================================================================================
模块四：数据分析（analyzer.py）
================================================================================
目标：对清洗后的天气数据做统计分析，生成前端仪表盘所需的全部数据。

核心功能：
  ① generate_monthly_stats()  — 月度统计（温度 / 降雨 / 天气分布 / 气候评分 / 建议）
  ② get_weather_distribution() — 天气分布（饼图数据）
  ③ get_climate_scores()       — 5 项气候评分（雷达图数据）
  ④ get_heatmap_data()         — 年度温度热力图（12 月 × 5 分位）
  ⑤ generate_comprehensive_advice() — 规则引擎 5 类生活建议（AI 失败时的兜底）

智能建议的双引擎策略：
  ┌─ AI 引擎（优先）  — 调用 DeepSeek v4-pro，结合实时数据生成 JSON 建议
  │  失败时 ↓
  └─ 规则引擎（兜底） — 纯 if/else 判断，稳定可靠，不依赖外部 API

气候评分算法：5 项评分统一归一化到 0-100
  ① 温度舒适度 — 日最高温∈[18,30] 且最低温∈[10,25] 的天数占比
  ② 湿度适宜度 — 偏离理想值 50% 的程度（每偏离 1% 扣 2 分）
  ③ 日照充足度 — 晴天 + 多云 天数占比
  ④ 空气质量   — 晴天比例(60%) + 降雨适中度(40%)
  ⑤ 降水适中度 — 月降雨天数距最佳值 6 天的偏离程度

================================================================================
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
    核心分析入口：生成月度统计 + 气候评分 + 智能建议。

    ========== 处理流程 ==========
    ① 从 WeatherData 按年月筛选 → pandas DataFrame
    ② 按 (year, month) 分组
    ③ 每组计算：
        - 温度统计（月均最高、月均最低、月极值）
        - 降雨天数（天气描述含"雨"的天数）
        - 平均湿度
        - 天气分布（value_counts → dict → JSONField）
        - 5 项气候评分（调用 5 个 _calc_* 函数）
    ④ 写入 MonthlyStats 表（update_or_create，以 year+month 为唯一键）
    ⑤ 生成智能建议：
        - 优先调用 AI 引擎（ai_advisor.generate_ai_advice）
        - AI 失败时自动回退规则引擎（generate_comprehensive_advice）

    ========== 为什么 AI 优先 + 规则兜底 ==========
    AI 建议更个性化、能结合具体数据（如"未来3天有雨"），
    但依赖外部 API（网络/欠费/限流都可能导致失败）。
    规则引擎虽然略显模板化，但 100% 可用，保证系统不死。

    参数：
        year  (int, 可选)：只分析指定年份
        month (int, 可选)：只分析指定月份（需同时传 year）

    输出：
        MonthlyStats 表 + ClothingAdvice 表（直接写库）
    """
    # ---- 步骤 ①：读取数据 ----
    qs = WeatherData.objects.all()
    if year:
        qs = qs.filter(date__year=year)
    if month:
        qs = qs.filter(date__month=month)

    df = pd.DataFrame(qs.values())
    if df.empty:
        logger.warning("无数据可分析")
        return

    # 提取年月用于分组
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

    # ---- 步骤 ②：按月分组分析 ----
    grouped = df.groupby(['year', 'month'])
    for (y, m), group in grouped:
        total_days = len(group)  # 当月有多少天数据

        # 温度统计
        avg_max = group['max_temp'].mean()      # 月均最高温（每日最高温的平均）
        avg_min = group['min_temp'].mean()      # 月均最低温（每日最低温的平均）
        max_record = group['max_temp'].max()    # 本月最高温极值
        min_record = group['min_temp'].min()    # 本月最低温极值

        # 降雨天数：天气描述中包含"雨"字即算（小雨/中雨/大雨/暴雨/阵雨）
        rainy_days = int(group['weather_desc'].astype(str).str.contains('雨').sum())

        # 平均湿度
        avg_humidity = group['humidity'].mean() if 'humidity' in group.columns else None

        # 天气分布（如 {"多云~晴": 12, "小雨": 5, "阴": 8}）
        # value_counts().to_dict() 自动按出现次数降序
        weather_dist = group['weather_desc'].value_counts().to_dict()

        # ---- 步骤 ③：5 项气候评分 ----
        temp_score = _calc_temp_comfort_score(group)
        humidity_score = _calc_humidity_comfort_score(avg_humidity)
        sunlight_score = _calc_sunlight_score(group)
        air_score = _calc_air_quality_score(group)
        precipitation_score = _calc_precipitation_score(rainy_days)

        # ---- 步骤 ④：写入 MonthlyStats ----
        # update_or_create 以 (year, month) 联合键去重
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

        # ---- 步骤 ⑤：生成智能建议（双引擎）----
        try:
            # 优先：AI 引擎
            ai_result = generate_ai_advice(f"{y}-{m:02d}")
            if ai_result:
                # AI 成功 → 直接写入 ClothingAdvice
                # 从 5 个分类中合并所有标签
                all_tags = []
                for cat in ai_result.values():
                    all_tags.extend(cat.get('tags', []))
                ClothingAdvice.objects.update_or_create(
                    month=f"{y}-{m:02d}",
                    defaults={
                        # 拼接 5 类建议为综合文本
                        'advice_text': ' '.join(c.get('advice', '') for c in ai_result.values()),
                        'tags': list(set(all_tags)),  # 去重标签
                        'advice_categories': ai_result,  # 完整 5 分类 JSON
                    }
                )
                logger.info(f"{y}-{m:02d} AI 建议已生成")
            else:
                raise Exception('AI 返回空')
        except Exception as e:
            # 兜底：规则引擎（本地纯计算，100% 可用）
            logger.warning(f"AI 建议失败({e})，回退规则引擎")
            generate_comprehensive_advice(y, m)

    logger.info("月度统计与气候评分生成完成")


def generate_comprehensive_advice(year: int, month: int):
    """
    规则引擎：综合历史数据与未来预报，生成 5 维度生活建议。

    ========== 为什么要规则引擎 ==========
    当 AI API 不可用时（网络超时 / 欠费 / 限流），必须有一个纯本地
    计算的兜底方案。规则引擎虽然建议略显模板化，但 100% 可靠。

    ========== 数据来源 ==========
    - 近 60 天历史数据（WeatherData）：实际观测值，代表"最近真实天气"
    - 未来 14 天预报（ForecastData）：预测值，代表"即将到来的天气"
    - 当月统计（MonthlyStats）：该月的整体画像

    为什么是 60 天 + 14 天？
      60 天 ≈ 2 个月，足够捕捉季节变化趋势；
      14 天 ≈ 2 周，是可参考预报的上限（超过 14 天预报准确度骤降）。

    ========== 5 类建议生成规则 ==========

    ① 穿衣建议 (clothing)
       判断维度：温度区间 + 昼夜温差 + 湿度
       - >32°C → 短袖短裤 + 防晒
       - 26~32°C → 短袖/薄长袖
       - 20~26°C → 薄外套
       - 12~20°C → 厚外套/毛衣
       - <12°C → 羽绒服/棉衣
       - 低温<5°C → 追加保暖内衣提示
       - 温差>10°C → 追加"携带外套"提示
       - 湿度>75% → 追加"吸湿透气面料"提示

    ② 出行建议 (travel)
       判断维度：降雨频率 + 极端温度
       - ≥5天雨 → 必带雨具 + 防水鞋
       - 2~4天雨 → 建议带折叠伞
       - <2天雨 → 无需雨具
       - >35°C → 避免中午出行 + 防暑
       - <0°C → 注意路面结冰
       - 温度20~30°C + 少雨 → 适合出游

    ③ 运动建议 (exercise)
       判断维度：温度舒适度 + 降雨
       - 15~28°C + 少雨 → 户外运动（跑步/骑行/球类）
       - 28~33°C → 早晚运动 + 游泳
       - >33°C → 室内运动（游泳/健身/瑜伽）
       - <10°C → 室内运动 + 充分热身
       - ≥4天雨 → 室内优先

    ④ 健康建议 (health)
       判断维度：湿度 + 温差 + 高温
       - >80% 湿度 → 防霉通风 + 除湿
       - <30% 湿度 → 保湿 + 加湿器
       - 温差>12°C → 防感冒 + 及时增减衣物
       - 降雨>8天 → 关节防潮保暖
       - >30°C → 防中暑 + 多饮水
       - 无特殊情况 → "天气良好"

    ⑤ 天气预警 (alert)
       三级预警体系：
       - danger  (红色)：极端高温≥38°C / 极端低温≤-5°C
       - warning (橙色)：高温≥35°C / 低温≤0°C / 暴雨≥2天 / 温差>15°C
       - normal  (绿色)：天气平稳，无极端情况

    参数：
        year  (int)：年份
        month (int)：月份

    输出：
        写入 ClothingAdvice 表（以 YYYY-MM 为键）
    """
    from datetime import date, timedelta

    # 先取月度统计（当月整体画像）
    stats = MonthlyStats.objects.filter(year=year, month=month).first()
    if not stats:
        return

    # ==================== 数据准备 ====================
    today = date.today()

    # 历史范围：向前推 60 天（约 2 个月）
    hist_start = today - timedelta(days=60)
    hist_qs = WeatherData.objects.filter(date__gte=hist_start).order_by('date')
    # 预报范围：取未来 14 天
    forecast_qs = ForecastData.objects.all().order_by('date')[:14]

    # ---- 历史数据统计 ----
    hist_count = hist_qs.count()
    hist_avg_max = hist_qs.aggregate(a=Avg('max_temp'))['a'] or 0      # 近60天日均最高温
    hist_avg_min = hist_qs.aggregate(a=Avg('min_temp'))['a'] or 0      # 近60天日均最低温
    hist_rain_days = hist_qs.filter(weather_desc__icontains='雨').count() if hist_count else 0
    hist_avg_humidity = hist_qs.aggregate(a=Avg('humidity'))['a'] or 50  # 默认 50%

    # ---- 预报数据统计 ----
    fc_count = forecast_qs.count()
    fc_avg_high = forecast_qs.aggregate(a=Avg('day_temp'))['a'] or 0    # 未来14天白天均温
    fc_avg_low = forecast_qs.aggregate(a=Avg('night_temp'))['a'] or 0   # 未来14天夜间均温
    fc_rain_days = sum(1 for f in forecast_qs if f.weather_desc and '雨' in f.weather_desc)
    fc_max_temp = max((f.day_temp or 0) for f in forecast_qs) if fc_count else 0
    fc_min_temp = min((f.night_temp or 99) for f in forecast_qs) if fc_count else 99

    # ---- 综合判断值 ----
    # 取历史均值和预报均值的平均，作为"代表性温度"做决策
    # 如果无预报数据（fc_count=0），纯靠历史数据
    rep_high = (hist_avg_max + fc_avg_high) / 2 if fc_count else hist_avg_max
    rep_low = (hist_avg_min + fc_avg_low) / 2 if fc_count else hist_avg_min
    temp_range = rep_high - rep_low  # 昼夜温差

    categories = {}

    # ================================================
    # ① 穿衣建议：基于温度区间 + 昼夜温差 + 湿度
    # ================================================
    clothing_tags = []
    clothing_parts = []

    # 主判断：根据"代表性高温"确定基础穿着
    if rep_high > 32:
        # >32°C = 炎热（四川盆地夏季常见），短袖 + 防晒
        clothing_parts.append("气温较高，建议穿着轻薄透气的短袖短裤，注意防晒补水。")
        clothing_tags.extend(["短袖", "防晒霜", "遮阳帽"])
    elif rep_high > 26:
        # 26~32°C = 偏热，短袖或薄长袖即可
        clothing_parts.append("气温偏热，建议穿着透气舒适的短袖或薄长袖。")
        clothing_tags.extend(["短袖", "薄长袖"])
    elif rep_high > 20:
        # 20~26°C = 舒适（春秋季典型），薄外套最佳
        clothing_parts.append("气温适宜，可穿着薄外套或长袖衬衫，体感舒适。")
        clothing_tags.append("薄外套")
    elif rep_high > 12:
        # 12~20°C = 偏凉（深秋/初冬），需要厚外套
        clothing_parts.append("气温偏凉，建议穿着保暖外套或毛衣，注意防风。")
        clothing_tags.extend(["厚外套", "毛衣"])
    else:
        # ≤12°C = 寒冷（冬季），羽绒服 + 保暖配件
        clothing_parts.append("气温较低，请注意保暖，建议穿着羽绒服或棉衣。")
        clothing_tags.extend(["羽绒服", "围巾", "手套"])

    # 附加判断 1：夜间低温（<5°C 需保暖内衣）
    if rep_low < 5:
        clothing_parts.append("早晚寒冷，建议内穿保暖内衣。")
        clothing_tags.append("保暖内衣")
    # 附加判断 2：昼夜温差 > 10°C（如"早晚冬天中午夏天"的过渡季）
    elif temp_range > 10:
        clothing_parts.append(f"昼夜温差较大（约{temp_range:.0f}°C），外出建议携带一件外套。")
        clothing_tags.append("外套")

    # 附加判断 3：湿度 > 75%（都江堰地处四川盆地，常年潮湿）
    if hist_avg_humidity > 75:
        clothing_parts.append("空气湿度较大，建议选择吸湿透气的面料。")
        clothing_tags.append("透气面料")

    categories['clothing'] = {
        'advice': ' '.join(clothing_parts),
        'tags': list(set(clothing_tags)),  # set 去重（如"外套"可能被两次触发）
    }

    # ================================================
    # ② 出行建议：基于降雨频率 + 极端温度
    # ================================================
    travel_tags = []
    travel_parts = []

    # 主判断：未来 14 天降雨天数
    if fc_rain_days >= 5:
        # ≥5 天雨 → 必须带雨具（降雨频繁，不带会淋）
        travel_parts.append(f"未来两周降雨频繁（{fc_rain_days}天），出行务必携带雨具，注意路面湿滑。")
        travel_tags.extend(["雨伞", "防水鞋"])
    elif fc_rain_days >= 2:
        # 2~4 天雨 → 建议带折叠伞（偶有降雨）
        travel_parts.append(f"未来两周有{fc_rain_days}天可能降雨，建议随身携带折叠伞。")
        travel_tags.append("折叠伞")
    else:
        # <2 天雨 → 无需特别准备
        travel_parts.append("未来两周降雨较少，出行无需特别准备雨具。")
        travel_tags.append("晴好")

    # 附加判断：极端高温 > 35°C
    if fc_max_temp > 35:
        travel_parts.append("将出现高温天气，避免中午时段户外活动，注意防暑降温。")
        travel_tags.append("防暑")
    # 附加判断：极端低温 < 0°C
    elif fc_min_temp < 0:
        travel_parts.append("将出现零下低温，注意路面结冰，驾车减速慢行。")
        travel_tags.append("防滑")

    # 正面提示：天气好时主动推荐出游
    if rep_high >= 20 and fc_rain_days <= 2:
        travel_parts.append("天气条件适合短途旅行和户外郊游。")
        travel_tags.append("适合出游")

    categories['travel'] = {
        'advice': ' '.join(travel_parts),
        'tags': list(set(travel_tags)),
    }

    # ================================================
    # ③ 运动建议：基于温度舒适度 + 降雨
    # ================================================
    exercise_tags = []
    exercise_parts = []

    # 最佳运动温度：15~28°C，且低温不低于 10°C，且少雨
    if 15 <= rep_high <= 28 and rep_low >= 10 and fc_rain_days <= 3:
        exercise_parts.append("温度适中，降雨较少，非常适合户外运动：跑步、骑行、球类运动皆宜。")
        exercise_tags.extend(["跑步", "骑行", "户外运动"])
    # 偏热：28~33°C → 避开正午，推荐晨跑/夜跑/游泳
    elif rep_high > 28 and rep_high <= 33:
        exercise_parts.append("气温偏高，建议早晨或傍晚运动，避开正午高温时段，注意补充水分。")
        exercise_tags.extend(["晨跑", "夜跑", "游泳"])
    # 炎热：>33°C → 室内为主（游泳算室内运动）
    elif rep_high > 33:
        exercise_parts.append("高温天气，建议选择室内运动（游泳、健身、瑜伽），户外运动有中暑风险。")
        exercise_tags.extend(["游泳", "健身房", "瑜伽"])
    # 寒冷：<10°C → 室内为主 + 充分热身
    elif rep_high < 10:
        exercise_parts.append("气温偏低，户外运动前充分热身，建议选择室内运动保暖。")
        exercise_tags.extend(["热身", "室内运动"])
    else:
        # 落在 10~15°C 或 33°C 以上已覆盖，剩余情况通用建议
        exercise_parts.append("天气条件一般，适当运动即可，注意根据体感调整强度。")
        exercise_tags.append("适度运动")

    # 附加判断：降雨较多时追加室内提示
    if fc_rain_days >= 4:
        exercise_parts.append("降雨较多时可选择室内运动替代。")
        exercise_tags.append("室内优先")

    categories['exercise'] = {
        'advice': ' '.join(exercise_parts),
        'tags': list(set(exercise_tags)),
    }

    # ================================================
    # ④ 健康建议：基于湿度 + 温差 + 高温
    # ================================================
    health_tags = []
    health_parts = []

    # 湿度判断：>80% 太潮（都江堰夏季常见），<30% 太干（冬季取暖导致）
    if hist_avg_humidity > 80:
        health_parts.append("空气湿度较高，容易滋生细菌，注意食品卫生和室内通风。")
        health_tags.extend(["通风", "除湿"])
    elif hist_avg_humidity < 30:
        health_parts.append("空气干燥，注意皮肤保湿，多喝水，可使用加湿器。")
        health_tags.extend(["保湿", "加湿器"])

    # 温差判断：>12°C 容易感冒（免疫系统适应不过来）
    if temp_range > 12:
        health_parts.append(f"昼夜温差大（约{temp_range:.0f}°C），容易感冒，注意及时增减衣物。")
        health_tags.append("防感冒")

    # 潮湿判断：降雨 > 8 天 → 关节不适者注意（都江堰湿度大，关节问题高发）
    if hist_rain_days > 8:
        health_parts.append("近期多雨潮湿，关节不适者注意保暖防潮。")
        health_tags.append("关节保暖")

    # 高温判断：>30°C 防中暑
    if rep_high > 30:
        health_parts.append("高温天气注意防暑降温，多饮温水，避免长时间日晒。")
        health_tags.extend(["防中暑", "多饮水"])

    # 都不触发 = 天气良好
    if not health_parts:
        health_parts.append("当前天气状况良好，保持正常作息和适量运动即可。")
        health_tags.append("良好")

    categories['health'] = {
        'advice': ' '.join(health_parts),
        'tags': list(set(health_tags)),
    }

    # ================================================
    # ⑤ 天气预警：三级体系（normal / warning / danger）
    #    级别会升级：先 normal → 有预警条件触发 warning → 极端条件触发 danger
    # ================================================
    alert_tags = []
    alert_parts = []
    alert_level = 'normal'  # 初始：绿色，无预警

    # 高温预警
    if fc_max_temp >= 38:
        # ≥38°C = 红色预警（danger），四川盆地 2022 年出现过
        alert_parts.append("⚠️ 高温红色预警：未来将出现 38°C 以上极端高温，注意防暑！")
        alert_tags.append("高温预警")
        alert_level = 'danger'
    elif fc_max_temp >= 35:
        # ≥35°C = 橙色预警（warning），高温黄色预警线
        alert_parts.append("⚠️ 高温橙色预警：未来将出现 35°C 以上高温天气。")
        alert_tags.append("高温预警")
        alert_level = 'warning'

    # 低温预警（都江堰极少 ≤ -5°C，此条件保守设计）
    if fc_min_temp <= -5:
        alert_parts.append("⚠️ 低温预警：未来将出现 -5°C 以下极端低温，注意防寒保暖！")
        alert_tags.append("低温预警")
        alert_level = 'danger'  # 极端低温直接 danger
    elif fc_min_temp <= 0:
        alert_parts.append("⚠️ 低温预警：未来将出现零下低温，注意防寒防冻。")
        alert_tags.append("低温预警")
        # 低温 warning：如果前面已经 danger 则不降级
        if alert_level != 'danger':
            alert_level = 'warning'

    # 强降雨预警：预报中含"大"或"暴"字的天气 ≥2 天
    # "大"匹配大雨/大暴雨，"暴"匹配暴雨/暴雪
    heavy_rain = sum(1 for f in forecast_qs if f.weather_desc and ('大' in f.weather_desc or '暴' in f.weather_desc))
    if heavy_rain >= 2:
        alert_parts.append(f"⚠️ 强降雨预警：未来有{heavy_rain}天可能出现大雨或暴雨，注意防范。")
        alert_tags.append("暴雨预警")
        # 暴雨至少是 warning 级别（不降已有 danger）
        if alert_level == 'normal':
            alert_level = 'warning'

    # 温差预警：>15°C 说明早晚温差极端（如早上 5°C 中午 22°C）
    if temp_range > 15:
        alert_parts.append(f"⚠️ 温差预警：昼夜温差超过15°C，注意适时增减衣物。")
        alert_tags.append("温差预警")
        # 温差是辅助预警，从 normal 升级到 warning 但不升级到 danger
        if alert_level == 'normal':
            alert_level = 'warning'

    # 无任何预警触发 → 天气平稳
    if not alert_parts:
        alert_parts.append("未来天气平稳，无极端天气预警。")
        alert_tags.append("无预警")

    categories['alert'] = {
        'advice': ' '.join(alert_parts),
        'tags': list(set(alert_tags)),
        'level': alert_level,  # normal / warning / danger → 前端据此显示绿/橙/红色
    }

    # ==================== 汇总并入库 ====================
    # 拼接 5 分类建议为综合文本
    all_advice_texts = [c['advice'] for c in categories.values()]
    summary_text = ' '.join(all_advice_texts)

    # 合并所有标签（set 去重）
    all_tags = []
    for c in categories.values():
        all_tags.extend(c.get('tags', []))

    # 写入 ClothingAdvice 表（以 YYYY-MM 为唯一键）
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
    获取天气分布数据（前端饼图用）。

    ========== 颜色映射规则 ==========
    从天气描述中按子串匹配颜色，匹配优先级从高到低：
      雪 > 雨 > 雾/霾 > 多云 > 阴 > 晴 → 无匹配用灰色 #9CA3AF

    为什么按这个优先级？
      复合天气如"小雨转阴"含"雨"也含"阴"，优先级保证它归为"雨"色
      而非"阴"色，因为降雨对用户感知更重要。

    颜色选用暖色系（黄/棕/灰/蓝）：
      晴 #D4A373 暖黄  — 温暖的阳光感
      多云 #A8A29E 浅灰 — 中性过渡
      阴 #78716C 深灰  — 阴沉压抑
      雨 #7FA3C1 蓝色  — 水/雨滴的联想
      雪 #B8C5D6 淡蓝  — 冰雪冷色调

    参数：
        year  (int, 可选)：筛选年份
        month (int, 可选)：筛选月份

    返回：
        [{name: "多云~晴", value: 12, color: "#A8A29E"}, ...]
        按数量降序排列
    """
    qs = MonthlyStats.objects.all()
    if year:
        qs = qs.filter(year=year)
    if month:
        qs = qs.filter(month=month)

    # 汇总多个月的 weather_distribution JSON 字段
    # 如 6月{"多云": 8, "小雨": 5} + 7月{"多云": 10, "晴天": 3}
    # → {"多云": 18, "小雨": 5, "晴天": 3}
    total_dist = {}
    for stat in qs:
        for desc, count in (stat.weather_distribution or {}).items():
            total_dist[desc] = total_dist.get(desc, 0) + count

    # 颜色映射表：按匹配优先级排序
    color_map = {
        '晴': '#D4A373',   # 暖黄色
        '多云': '#A8A29E', # 浅灰色
        '阴': '#78716C',   # 深灰色
        '雨': '#7FA3C1',   # 蓝色
        '雪': '#B8C5D6',   # 淡蓝色
    }
    default_color = '#9CA3AF'  # 无法归类的默认灰色

    def get_color(desc: str) -> str:
        """根据天气描述子串匹配颜色（优先级：雪>雨>雾霾>多云>阴>晴）"""
        if not desc:
            return default_color
        # 按优先级依次检查，命中即返回（不继续往下）
        if '雪' in desc:
            return color_map['雪']
        if '雨' in desc:
            return color_map['雨']
        if '雾' in desc or '霾' in desc:
            return '#A8A29E'  # 雾霾用灰色，视觉上表示"看不清"
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
            'name': name,           # 原始天气描述
            'value': value,         # 出现次数
            'color': get_color(name),  # 对应颜色
        })

    # 按数量降序 → 饼图最大的扇区排在最前面
    result.sort(key=lambda x: x['value'], reverse=True)
    return result


def get_climate_scores(year: int = None, month: int = None) -> list:
    """
    获取 5 项气候综合评分（前端雷达图用）。

    参数：
        year  (int, 可选)：筛选年份
        month (int, 可选)：筛选月份

    返回：
        [
          {category: "温度舒适度", value: 85},
          {category: "湿度适宜度", value: 62},
          {category: "日照充足度", value: 70},
          {category: "空气质量",   value: 75},
          {category: "降水适中度", value: 58},
        ]
        每项 value ∈ [0, 100]

    多个月份时取各项的平均值（Django 的 Avg 聚合）。
    """
    qs = MonthlyStats.objects.all()
    if year:
        qs = qs.filter(year=year)
    if month:
        qs = qs.filter(month=month)

    if not qs.exists():
        return []

    # 对多个月份的各维度取平均值
    avg = qs.aggregate(
        temp=Avg('temp_comfort_score'),
        humidity=Avg('humidity_comfort_score'),
        sunlight=Avg('sunlight_score'),
        air=Avg('air_quality_score'),
        precipitation=Avg('precipitation_score'),
    )

    # 雷达图的 5 个轴（顺序决定雷达图上的顺时针排列）
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
            'value': round(val),  # 整数展示，雷达图标签更简洁
        })
    return result


def get_heatmap_data(year: int = None) -> list:
    """
    生成年度温度热力分布数据（12 个月 × 5 个温度层级）。

    ========== 数据结构 ==========
    每行代表某月某个分位上的温度值：
      row 0 → min   (当月最低温)
      row 1 → Q25   (25% 分位 — 偏冷的日子)
      row 2 → median (中位数 — 典型温度)
      row 3 → Q75   (75% 分位 — 偏热的日子)
      row 4 → max   (当月最高温)

    前端用这 5×12=60 个数据点渲染热力图：
      X 轴 = 12 个月
      Y 轴 = 5 个温度层级
      颜色深浅 = 温度高低（冷色蓝 → 暖色红）

    ========== 为什么用分位数而非均值 ==========
    均值只能反映"平均情况"，分位数能展示温度分布的范围和形态：
    如 7 月 min=22°C, Q75=35°C, max=38°C → 用户一眼看出夏季温差大。

    参数：
        year (int, 可选)：筛选年份

    返回：
        [{month: "1月", row: 0, temp: -2.0}, {month: "1月", row: 1, temp: 4.5}, ...]
    """
    qs = WeatherData.objects.all()
    if year:
        qs = qs.filter(date__year=year)

    # 只取出 date 和 max_temp，减少数据传输量
    df = pd.DataFrame(qs.values('date', 'max_temp'))
    if df.empty:
        return []

    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month  # 提取月份 1~12

    months = ['1月', '2月', '3月', '4月', '5月', '6月',
              '7月', '8月', '9月', '10月', '11月', '12月']

    result = []
    for month_idx, month_label in enumerate(months, 1):
        # 筛选该月所有最高温数据（去掉 NaN）
        month_data = df[df['month'] == month_idx]['max_temp'].dropna()
        if len(month_data) == 0:
            continue

        # 计算 5 个统计值
        stats = [
            month_data.min(),           # row 0: 该月最低温
            month_data.quantile(0.25),  # row 1: 下四分位数
            month_data.median(),        # row 2: 中位数
            month_data.quantile(0.75),  # row 3: 上四分位数
            month_data.max(),           # row 4: 该月最高温
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
    获取某年的年度概要（年均温、最热/最冷日、总降雨天数）。

    参数：
        year (int)：目标年份

    返回：
        {
          year: 2025,
          avg_max_temp: 22.5,
          avg_min_temp: 14.3,
          hottest_day: "2025-07-15",
          coldest_day: "2025-01-08",
          total_rainy_days: 142
        }
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
    获取极端天气记录（历史最高温 / 最低温）。

    参数：
        year (int, 可选)：限定年份，不传则全局查询

    返回：
        {
          hottest: {date: "2022-08-14", temp: 38.5},
          coldest: {date: "2021-01-07", temp: -2.0}
        }
    """
    qs = WeatherData.objects.all()
    if year:
        qs = qs.filter(date__year=year)

    # 降序取第一条 = 最高温记录
    hottest = qs.order_by('-max_temp').first()
    # 升序取第一条 = 最低温记录
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
    一键分析入口：生成所有月度统计 + 气候评分 + 智能建议。

    这是前端"一键分析"按钮和命令行 `python manage.py run_pipeline`
    共同调用的入口函数。
    """
    logger.info("开始生成月度统计...")
    generate_monthly_stats()
    logger.info("分析完成！")


# ==================== 5 项气候评分算法（内部函数）====================
# 每项评分归一化到 0-100，供给 MonthlyStats 表和前端雷达图使用。

def _calc_temp_comfort_score(group: pd.DataFrame) -> int:
    """
    ① 温度舒适度评分

    算法：统计"舒适天数"占当月总天数的比例 × 100。

    舒适天定义（同时满足）：
      - 日最高温 ∈ [18, 30]°C  → 不冷不热，体感舒适
      - 日最低温 ∈ [10, 25]°C  → 夜间不冻，也不闷热

    为什么是这个区间？
      18-30°C 是大多数人的"热中性"温度区间，不需要额外穿衣或降温；
      低于 10°C 需要暖气/厚衣，高于 30°C 需要空调/风扇。

    都江堰典型值：春/秋季 70-90 分，夏季 30-50 分，冬季 10-30 分。

    参数：
        group: 某个月的数据子集（pd.DataFrame）
    返回：
        0-100 的整数评分
    """
    if group.empty:
        return 50  # 无数据时返回中位数
    comfortable = group[
        (group['max_temp'] >= 18) & (group['max_temp'] <= 30) &
        (group['min_temp'] >= 10) & (group['min_temp'] <= 25)
    ]
    score = len(comfortable) / len(group) * 100
    return round(score)


def _calc_humidity_comfort_score(avg_humidity) -> int:
    """
    ② 湿度适宜度评分

    算法：以 50% 为理想湿度，偏离越大分数越低。

    公式：score = max(0, 100 - |actual - 50| × 2)

    扣分速率：每偏离理想值 1%，扣 2 分 → 偏离 50% 时归零。

    为什么 50% 是理想值？
      30%-60% 是 WHO 推荐的室内湿度范围，50% 是中心点。
      >70% → 闷热、霉菌滋生；<30% → 皮肤干燥、静电。

    都江堰典型值：全年偏高，夏季常 80%+ → 分数偏低（30-50 分）。

    参数：
        avg_humidity: 当月平均湿度（float 或 NaN）
    返回：
        0-100 的整数评分
    """
    if avg_humidity is None or pd.isna(avg_humidity):
        return 50  # 无数据返回中位数
    deviation = abs(float(avg_humidity) - 50)
    score = max(0, 100 - deviation * 2)
    return round(score)


def _calc_sunlight_score(group: pd.DataFrame) -> int:
    """
    ③ 日照充足度评分

    算法：(晴天 + 多云天数) / 总天数 × 100。

    基于 weather_type 字段（由 WeatherData.save() 自动推断分类）：
      - sunny  → 晴天（日照充足）
      - cloudy → 多云（有阳光但不完整）
      - overcast / rainy / snowy / foggy → 不计入

    多云为什么算"有日照"？
      多云天气仍有间歇性阳光，不完全是阴天。对户外活动和心情
      影响远小于纯阴天或雨天。

    都江堰典型值：冬季阴天多分数低（30-50），夏季晴天多分数高（60-80）。

    参数：
        group: 含 weather_type 列的 DataFrame
    返回：
        0-100 的整数评分
    """
    if group.empty or 'weather_type' not in group.columns:
        return 50
    # 只统计 sunny 和 cloudy 的天数
    sunny_cloudy = group[group['weather_type'].isin(['sunny', 'cloudy'])]
    score = len(sunny_cloudy) / len(group) * 100
    return round(score)


def _calc_air_quality_score(group: pd.DataFrame) -> int:
    """
    ④ 空气质量评分（间接指标）

    算法：晴天比例得分(60%) + 降雨适中度得分(40%)。

    ========== 为什么用天气类型估算空气质量 ==========
    本项目无实际 AQI / PM2.5 数据，使用天气作为间接指标：
      - 晴天多 → 大气垂直扩散条件好 → 污染物不易积聚
      - 降雨适中 → 雨水冲刷空气中的颗粒物 → 净化效果

    ========== 公式拆解 ==========
    晴天比例得分 = (晴天数 / 总天数) × 60        → 范围 [0, 60]
    降雨得分     = max(0, 100 - |rain-6| × 12) × 0.4  → 范围 [0, 40]
    总分         = 晴天得分 + 降雨得分            → 范围 [0, 100]

    最佳降雨天数 = 6 天/月（适度降雨净化空气，又不至于太潮）

    参数：
        group: 含 weather_type 列的 DataFrame
    返回：
        0-100 的整数评分
    """
    if group.empty or 'weather_type' not in group.columns:
        return 50
    total = len(group)
    sunny_days = len(group[group['weather_type'] == 'sunny'])
    rainy_days = len(group[group['weather_type'] == 'rainy'])

    # 晴天得分（权重 60%）：晴天越多空气越好
    sunny_ratio = sunny_days / total if total > 0 else 0
    sunny_score = sunny_ratio * 60  # [0, 60]

    # 降雨得分（权重 40%）：偏离 6 天越远分数越低
    rain_score_100 = max(0, 100 - abs(rainy_days - 6) * 12)
    rain_score = rain_score_100 * 0.4  # 缩放到 [0, 40]

    score = sunny_score + rain_score
    return round(score)


def _calc_precipitation_score(rainy_days: int) -> int:
    """
    ⑤ 降水适中度评分

    算法：月降雨天数距最佳值 6 天的偏离程度。

    公式：score = max(0, 100 - |rainy_days - 6| × 12)

    扣分速率：每偏离最佳值 1 天，扣 12 分 → 偏离 9 天时归零。

    为什么最佳值是 6 天？
      - 每 5 天下一次雨 → 适度滋润，不影响出行
      - <3 天 → 偏干燥（都江堰不常见）
      - >10 天 → 偏潮湿，影响户外活动

    都江堰典型值：年均降雨约 150 天，每月约 12 天 → 分数偏低（30-50）。

    参数：
        rainy_days (int): 当月降雨天数
    返回：
        0-100 的整数评分
    """
    optimal = 6  # 最佳月降雨天数
    deviation = abs(rainy_days - optimal)
    score = max(0, 100 - deviation * 12)
    return round(score)
