"""
AI 智能模块：天气建议引擎 + 问答助手

使用 DeepSeek v4-pro API（兼容 OpenAI 格式）
"""

import os
import requests
import json
import logging
from datetime import date, timedelta
from django.db.models import Avg, Max, Min

logger = logging.getLogger(__name__)

# API 配置
API_URL = 'https://api.deepseek.com/v1/chat/completions'
API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
MODEL = 'deepseek-v4-pro'


def _call_ai(messages: list, max_tokens: int = 8000, temperature: float = 0.7) -> str:
    """调用 AI API，返回文本回复"""
    try:
        resp = requests.post(
            API_URL,
            json={
                'model': MODEL,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
            },
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        msg = data['choices'][0]['message']
        content = msg.get('content', '').strip()
        # Mimo 推理模型：content 为空时用 reasoning_content 兜底
        if not content:
            content = msg.get('reasoning_content', '').strip()
        return content
    except Exception as e:
        logger.error(f'AI 调用失败: {e}')
        return ''


def _build_weather_context(month_str: str = None) -> str:
    """构建天气数据上下文（历史 + 预报），供 AI 使用"""
    from app.models import WeatherData, MonthlyStats, ForecastData

    parts = []

    # 1. 最近 30 天实际数据
    today = date.today()
    recent = WeatherData.objects.filter(
        date__gte=today - timedelta(days=30)
    ).order_by('date')

    if recent.exists():
        avg_max = recent.aggregate(a=Avg('max_temp'))['a']
        avg_min = recent.aggregate(a=Avg('min_temp'))['a']
        max_t = recent.aggregate(m=Max('max_temp'))['m']
        min_t = recent.aggregate(m=Min('min_temp'))['m']
        rainy = recent.filter(weather_desc__icontains='雨').count()
        sunny = recent.filter(weather_type='sunny').count()
        avg_h = recent.aggregate(a=Avg('humidity'))['a']

        parts.append('=== 近30天都江堰实际天气 ===')
        parts.append(f'日均最高温: {avg_max:.1f}°C, 日均最低温: {avg_min:.1f}°C')
        parts.append(f'极端最高: {max_t}°C, 极端最低: {min_t}°C')
        parts.append(f'降雨天数: {rainy}, 晴天: {sunny}')
        if avg_h:
            parts.append(f'平均湿度: {avg_h:.0f}%')

        # 最近 7 天明细
        parts.append('最近7天:')
        for w in recent.order_by('-date')[:7]:
            parts.append(f'  {w.date} | {w.min_temp}~{w.max_temp}°C | {w.weather_desc} | 湿度{w.humidity}%')

    # 2. 未来 7 天预报
    from app.models import ForecastData
    forecast = ForecastData.objects.filter(
        date__gte=today, date__lte=today + timedelta(days=7)
    ).order_by('date')

    if forecast.exists():
        parts.append('\n=== 未来7天预报 ===')
        for f in forecast:
            parts.append(f'  {f.date} {f.week} | {f.night_temp}°C~{f.day_temp}°C | {f.weather_desc}')

    # 3. 月度统计
    if month_str:
        try:
            y, m = month_str.split('-')
            stats = MonthlyStats.objects.filter(year=int(y), month=int(m)).first()
            if stats:
                parts.append(f'\n=== {month_str} 月度统计 ===')
                parts.append(f'月均最高: {stats.avg_max_temp}°C, 月均最低: {stats.avg_min_temp}°C')
                parts.append(f'降雨: {stats.rainy_days}天, 均湿度: {stats.avg_humidity}%')
                parts.append(f'温度舒适度: {stats.temp_comfort_score}, 日照: {stats.sunlight_score}')
        except Exception:
            pass

    return '\n'.join(parts)


def generate_ai_advice(month_str: str = None) -> dict:
    """
    AI 生成 5 维度智能建议。
    返回: {clothing: {advice, tags}, travel: {...}, ...}
    """
    context = _build_weather_context(month_str)

    prompt = f"""你是一个天气生活顾问。根据以下都江堰天气数据，生成 5 类生活建议。

{context}

请严格按以下 JSON 格式输出（不要输出其他内容）：

{{
  "clothing": {{"advice": "穿衣建议，1-2句话，50字内", "tags": ["标签1", "标签2"]}},
  "travel":   {{"advice": "出行建议，1-2句话，50字内", "tags": ["标签1", "标签2"]}},
  "exercise": {{"advice": "运动建议，1-2句话，50字内", "tags": ["标签1", "标签2"]}},
  "health":   {{"advice": "健康建议，1-2句话，50字内", "tags": ["标签1", "标签2"]}},
  "alert":    {{"advice": "预警信息（无则说天气平稳）", "tags": ["标签1"], "level": "normal/warning/danger"}}
}}

要求：
- 具体结合温度、降雨、湿度数据
- 提到具体数字（如"未来7天降雨3次"）
- 标签用中文，2-4个字
- 都江堰是四川成都的县级市，气候湿润多雨
"""

    try:
        resp_text = _call_ai([
            {'role': 'system', 'content': '你是一个专业的生活顾问，输出严格的 JSON，不输出其他内容。'},
            {'role': 'user', 'content': prompt},
        ], temperature=0.5)

        # 提取 JSON（可能在 ```json ... ``` 中）
        if '```json' in resp_text:
            resp_text = resp_text.split('```json')[1].split('```')[0]
        elif '```' in resp_text:
            resp_text = resp_text.split('```')[1].split('```')[0]

        return json.loads(resp_text)
    except Exception as e:
        logger.error(f'AI 建议解析失败: {e}')
        return {}


def chat_about_weather(question: str, month_str: str = None) -> str:
    """
    AI 天气问答：根据实时天气数据回答用户问题。

    参数：
        question: 用户问题
        month_str: 当前选中月份 YYYY-MM

    返回：AI 回复文本
    """
    context = _build_weather_context(month_str)

    system_prompt = f"""你是一个友好的都江堰天气助手，名字叫"小堰"。
你要根据以下实时天气数据回答用户问题。

回答规则：
1. 结合具体数据，提到具体数字和日期
2. 语气亲切自然，像朋友聊天
3. 如果问题超出天气范围，礼貌说明你只能回答天气相关问题
4. 回答简洁，3句话以内，除非用户要求详细
5. 都江堰是四川成都的县级市，有著名的都江堰水利工程和青城山
6. 禁止使用任何 emoji 表情符号

当前天气数据：
{context}"""

    return _call_ai([
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': question},
    ], temperature=0.7)
