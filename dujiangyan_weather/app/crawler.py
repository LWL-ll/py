"""
================================================================================
模块一：网络爬虫（crawler.py）
================================================================================
数据源：2345 天气网（tianqi.2345.com）
爬取目标：
  1. 历史天气 — 通过内部 API /Pc/GetHistory 获取，每次请求返回单月全部数据（HTML 表格）
  2. 40天预报 — 通过 /wea_forty/{areaId}.htm 页面内嵌 JSON 提取

反爬策略（4 层）：
  ① 完整浏览器请求头：User-Agent + Referer + X-Requested-With + Accept-Language
  ② 每月请求间隔 2 秒，避免频率过高被封
  ③ 每个请求重试 1 次（首次失败 → sleep(2) → 重试）
  ④ 失败不中断全局，跳过该月继续下一个，保证整体可用

核心函数调用链：
  crawl_last_12_months() → fetch_month() → parse_and_save()
  fetch_forecast() （独立使用）

输出格式：list[dict]
  字段：date（"2025-06-01 周六"）、max_temp、min_temp、weather、wind、humidity
================================================================================
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from datetime import datetime
from django.utils import timezone as django_timezone

from app.models import WeatherData, CrawlTask, ForecastData

# ==================== 日志配置 ====================
# 使用 INFO 级别输出爬取进度，方便在终端/日志文件中追踪每次抓取
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 爬虫常量配置 ====================

# ---- 请求头：伪装成 Chrome 浏览器 ----
# 2345 天气网的 API 会检查这些字段，缺一个就可能返回 403 或空数据
HEADERS = {
    # User-Agent：浏览器身份标识，必须与真实 Chrome 一致
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/131.0.0.0 Safari/537.36'
    ),
    # Accept：声明期望的响应格式（JSON 优先）
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    # Accept-Language：中文优先，让服务器返回中文天气描述
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    # X-Requested-With：标记为 AJAX 请求（2345 API 通过 JS 调用，必带此头）
    'X-Requested-With': 'XMLHttpRequest',
}

# AREA_ID：2345 天气网的城市编码，60407 = 四川省成都市都江堰市
# 换城市只需改这个数字（如成都=58321，北京=54511）
AREA_ID = 60407

# BASE_URL：历史天气 API 地址
# 通过 GET 请求，参数拼接在 query string 中（见 fetch_month 中的 url 构造）
BASE_URL = 'https://tianqi.2345.com/Pc/GetHistory'

# REFERER_URL：告诉服务器"我从历史天气页面来的"，增强请求合法性
# 缺少 Referer 会被识别为直接访问 API，可能触发反爬
REFERER_URL = f'https://tianqi.2345.com/wea_history/{AREA_ID}.htm'


def fetch_month(year: int, month: int) -> list:
    """
    抓取"指定年月"的天气数据（核心爬虫函数）。

    参数：
        year  (int)：4 位年份，如 2025
        month (int)：月份 1~12

    ========== URL 构造说明 ==========
    最终请求 URL 示例（2025年6月）：
      https://tianqi.2345.com/Pc/GetHistory
        ?areaInfo[areaId]=60407
        &areaInfo[areaType]=2           ← areaType=2 表示"城市级"
        &date[year]=2025
        &date[month]=6

    注意：URL 参数中用 %5B %5D 来编码方括号 [ ]，因为 RFC 3986 规定
    [ 和 ] 在 query string 中属于不安全字符，必须百分号编码。
    %5B = [ 、%5D = ]

    ========== 反爬策略 ==========
    1. 请求头携带完整浏览器标识（User-Agent + Referer + X-Requested-With）
    2. 每个请求最多 2 次尝试（首次 + 1 次重试），重试前等待 2 秒
    3. 失败不抛异常，返回空列表，由上层函数决定后续处理

    ========== 返回格式 ==========
    list[dict]，每个 dict 字段：
      date     — "2025-06-01 周六"（包含日期和星期）
      max_temp — "25"（纯数字字符串，已去除 °、℃ 符号）
      min_temp — "18"
      weather  — "多云~晴"（原始天气描述文本）
      wind     — "东南风 2级"
      humidity — "37"（纯数字，可能为空字符串或 "-"）
    """
    # 拼接 URL 参数（%5B = [、%5D = ]，百分号编码后的方括号）
    url = (
        f'{BASE_URL}?'
        f'areaInfo%5BareaId%5D={AREA_ID}&areaInfo%5BareaType%5D=2'
        f'&date%5Byear%5D={year}&date%5Bmonth%5D={month}'
    )
    max_attempts = 2  # 最多尝试次数 = 首次请求 + 1 次重试

    # 在基础请求头上追加 Referer，链式来源保持一致
    req_headers = {**HEADERS, 'Referer': REFERER_URL}

    for attempt in range(max_attempts):
        try:
            # ---- 步骤 1：发送 GET 请求 ----
            # timeout=30 秒，防止单次请求无限等待
            resp = requests.get(url, headers=req_headers, timeout=30)
            resp.raise_for_status()  # 若 HTTP 状态码非 2xx，抛出 HTTPError

            # ---- 步骤 2：从 JSON 响应中提取 HTML 片段 ----
            # 2345 API 返回格式：{"data": "<table>...</table>"}
            # data 字段是一段完整的 HTML 表格（<tr><td>...</td></tr>）
            payload = resp.json()
            html = payload.get('data', '')

            # ---- 步骤 3：用 BeautifulSoup 解析 HTML 表格 ----
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.find_all('tr')  # 每一行 <tr> 代表一天的数据

            results = []
            # 跳过第一行（rows[0] 是表头：日期/最高温/最低温/天气/风向风力/湿度）
            for row in rows[1:]:
                tds = row.find_all('td')
                # 至少需要 5 列才算有效行（日期+最高温+最低温+天气+风向风力）
                if len(tds) < 5:
                    continue

                # ===== 表格列映射（td 索引 → 数据含义） =====
                # tds[0]：日期，如 "2025-06-01 周六"
                # tds[1]：最高温，如 "25°" 或 "25℃"
                # tds[2]：最低温，如 "18°"
                # tds[3]：天气状况，如 "多云~晴"、"小雨转阴"
                # tds[4]：风向风力，如 "东南风 2级"
                # tds[5]：湿度+AQI，如 "37 优" 或 "-"（可能不存在）

                # 日期：保留原始文本（含星期信息，后续截取前10位即可）
                date_str = tds[0].get_text(strip=True)

                # 温度：用正则去除 °、℃ 等非数字字符，只保留数字和小数点
                # 如 "25°" → "25"、"25.5℃" → "25.5"
                max_temp = re.sub(r'[^\d.-]', '', tds[1].get_text(strip=True))
                min_temp = re.sub(r'[^\d.-]', '', tds[2].get_text(strip=True))

                # 天气描述：保留原始中文文本
                weather = tds[3].get_text(strip=True)

                # 风向风力：原始文本如 "东南风 2级"
                wind = tds[4].get_text(strip=True)

                # 湿度：第 6 列，原始可能是 "37 优"（带AQI）或 "-"（无数据）
                # 同样用正则只提取数字部分
                humidity = ''
                if len(tds) >= 6:
                    humidity_text = tds[5].get_text(strip=True)
                    # "-" 表示该天无湿度数据，跳过
                    if humidity_text != '-':
                        humidity = re.sub(r'[^\d.-]', '', humidity_text)

                results.append({
                    'date': date_str,
                    'max_temp': max_temp,
                    'min_temp': min_temp,
                    'weather': weather,
                    'wind': wind,
                    'humidity': humidity,
                })
            # 全部行解析完成，返回当月结果
            return results

        # ---- 异常处理：区分网络异常和数据解析异常 ----
        except requests.exceptions.RequestException as e:
            # 网络层异常（超时、DNS 失败、连接拒绝、403/500 等）
            logger.warning(f'请求 {year}-{month:02d} 失败（第 {attempt + 1} 次）: {e}')
            if attempt < max_attempts - 1:
                # 还有重试机会：等待 2 秒再试（给服务器喘息 + 绕过瞬时限流）
                time.sleep(2)
            else:
                # 最后一次尝试也失败，记录错误并返回空列表
                # 不抛异常 — 保证一个月的失败不影响其他月份的爬取
                logger.error(f'抓取 {year}-{month:02d} 最终失败，跳过该月')
                return []
        except Exception as e:
            # 非网络异常（JSON 解析失败、HTML 结构变化等）
            logger.error(f'解析 {year}-{month:02d} 数据失败: {e}')
            return []


def crawl_last_12_months() -> list:
    """
    自动计算"当前日期往前推 12 个月"，逐月爬取都江堰每日天气。

    这是用户点击"一键爬取"按钮时调用的入口函数。

    ========== 月份回推算法 ==========
    例：当前是 2025 年 6 月
      i=0  → year=2025, month=6    (6-0=6)
      i=1  → year=2025, month=5    (6-1=5)
      i=5  → year=2025, month=1    (6-5=1)
      i=6  → year=2024, month=12   (6-6=0 → while ≤0 → +12 → 12, year-1)
      i=11 → year=2024, month=7    (6-11=-5 → while ≤0 → +12×1→7, year-1)

    关键逻辑：while month <= 0 循环将负月份修正为合法的 1~12 月，
    同时年份减 1。这比 if/elif 判断所有情况更简洁。

    最后 sorted() 按时间正序排列（从最早的月份开始爬），便于观察进度。

    ========== 反爬措施 ==========
    每月爬取后 time.sleep(2)，两次请求间隔 2 秒，模拟人类浏览节奏。

    返回：所有 12 个月的原始数据拼接成的 list[dict]
    """
    # Django 的 now() 返回带时区的 datetime，保证时间与服务器所在地一致（Asia/Shanghai）
    now = django_timezone.now()
    months = []

    # 构造过去 12 个月（含当前月），生成 (year, month) 元组列表
    for i in range(12):
        year = now.year
        month = now.month - i
        # 如果月份 ≤ 0，说明跨年了，需要向去年借月份
        # 如 month=-2，+12 后变成 10，同时 year-1
        while month <= 0:
            month += 12  # 每次借 12 个月（即 1 年）
            year -= 1    # 年份相应减 1
        months.append((year, month))

    # 按时间正序排列（从最早的月份爬起），日志输出更清晰
    months = sorted(months)
    logger.info(f'计划爬取月份: {months}')

    all_data = []
    for year, month in months:
        logger.info(f'正在抓取 {year}-{month:02d} ...')
        month_data = fetch_month(year, month)
        if month_data:
            all_data.extend(month_data)  # 把当月数据拼接到总结果中
            logger.info(f'  成功获取 {len(month_data)} 条')
            # 逐月入库 + 更新 CrawlTask 状态（即使失败也记录）
            try:
                parse_and_save(month_data, year=year, month=month)
            except Exception as e:
                logger.error(f'  保存 {year}-{month:02d} 失败: {e}')
        else:
            # 该月无数据，在 CrawlTask 表中标记为 failed
            CrawlTask.objects.update_or_create(
                year=year,
                month=month,
                defaults={
                    'status': 'failed',
                    'error_message': '未获取到任何数据',
                    'completed_at': django_timezone.now(),
                }
            )
        # 反爬：每月请求间隔 2 秒，降低被识别为爬虫的概率
        time.sleep(2)

    logger.info(f'总计获取 {len(all_data)} 条数据')
    return all_data


def parse_and_save(raw_list: list, year: int = None, month: int = None) -> int:
    """
    解析原始爬取数据并保存到 WeatherData 表（入库函数）。

    ========== 数据清洗与类型转换 ==========
    原始字符串 → 目标类型：
      "2025-06-01 周六" → date 对象（截取前 10 位）
      "25" / "25.5"      → float
      "东南风 2级"       → wind_direction="东南风" / wind_level="2级"（按空格拆分）
      "37" / "-" / ""    → float 或 None

    ========== 去重策略 ==========
    使用 update_or_create()，以 date 为唯一键：
      - 数据库中已存在该日期 → 更新温度/天气/湿度等字段（防止数据更正后残留旧值）
      - 数据库中没有该日期 → 新增一行
    这保证了重复爬取同一月份不会产生重复数据。

    ========== CrawlTask 状态机 ==========
    pending → running → success（记录记录数）
                     → failed （记录错误信息）
    状态追踪的目的是让前端能展示"上次爬取结果"。

    参数：
        raw_list: fetch_month() 返回的原始数据列表
        year:     年份（用于创建/更新 CrawlTask 记录）
        month:    月份

    返回：
        int — 成功保存的 WeatherData 记录数
    """
    # ---- 步骤 1：初始化 CrawlTask，状态设为 running ----
    task = None
    if year and month:
        # update_or_create：有则更新状态为 running，无则创建
        task, _ = CrawlTask.objects.update_or_create(
            year=year,
            month=month,
            defaults={'status': 'running', 'error_message': ''}
        )

    saved_count = 0
    try:
        # ---- 步骤 2：逐条解析并保存 ----
        for item in raw_list:
            try:
                # 日期："2025-06-01 周六" → 截取前 10 位 "2025-06-01" → date 对象
                date_str = item['date'][:10] if len(item['date']) >= 10 else item['date']
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                # 温度："25" → 25.0；空串 → None
                max_temp = float(item['max_temp']) if item['max_temp'] else None
                min_temp = float(item['min_temp']) if item['min_temp'] else None

                # 风向风力："东南风 2级" → 按空格拆分为 ["东南风", "2级"]
                wind_text = item.get('wind', '')
                wind_parts = wind_text.split(' ') if wind_text else ['', '']
                wind_direction = wind_parts[0]  # 如 "东南风"
                wind_level = wind_parts[1] if len(wind_parts) > 1 else ''  # 如 "2级"

                # 湿度："37" → 37.0；"-" 或 "" → None
                humidity_str = item.get('humidity', '')
                humidity = float(humidity_str) if humidity_str and humidity_str != '-' else None

                # update_or_create：以 date 为唯一键去重
                # date 不存在 → 新建行；date 已存在 → 更新 defaults 中的字段
                WeatherData.objects.update_or_create(
                    date=date_obj,
                    defaults={
                        'max_temp': max_temp,
                        'min_temp': min_temp,
                        'weather_desc': item.get('weather', ''),
                        'wind_direction': wind_direction,
                        'wind_level': wind_level,
                        'humidity': humidity,
                    }
                )
                saved_count += 1
            except Exception as e:
                # 单条数据异常（日期格式错误、温度非数字等），记录日志但不中断
                # 这种"宽容解析"策略保证一个月中少数坏数据不影响整月的入库
                logger.error(f'解析保存失败 {item}: {e}')

        # ---- 步骤 3：标记 CrawlTask 为成功 ----
        if task:
            task.status = 'success'
            task.records_count = saved_count  # 记录本月成功入库的条数
            task.completed_at = django_timezone.now()
            task.save()

    except Exception as e:
        # 整体异常（如数据库连接断开），标记为失败
        if task:
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = django_timezone.now()
            task.save()
        raise  # 重新抛出，让上层调用者感知

    logger.info(f'成功保存 {saved_count} 条数据到数据库')
    return saved_count


def crawl_range(start_year: int, start_month: int, end_year: int, end_month: int):
    """
    （保留函数）爬取"指定时间范围"的数据并直接入库。

    与 crawl_last_12_months() 的区别：
      - crawl_last_12_months()：自动计算近 12 个月，无需传参（前端按钮调用）
      - crawl_range()：手动指定起止年月，适合补数据场景（管理后台/命令行调用）

    参数：
        start_year, start_month — 起始年月
        end_year,   end_month   — 结束年月（含）

    内部逐月循环，每月调用 fetch_month() → parse_and_save()，间隔 2 秒。
    月度跨越用 datetime 对象追加月份实现（12 月跨年到 1 月）。
    """
    # 构造起始日期对象（日固定为 1 号，只用到年月）
    current = datetime(start_year, start_month, 1)
    end = datetime(end_year, end_month, 1)

    while current <= end:
        year = current.year
        month = current.month
        logger.info(f'正在抓取 {year}-{month:02d} ...')
        raw = fetch_month(year, month)
        if raw:
            try:
                parse_and_save(raw, year=year, month=month)
                logger.info(f'  成功保存 {len(raw)} 条')
            except Exception as e:
                logger.error(f'  保存 {year}-{month:02d} 失败: {e}')
        else:
            # 当月无数据，记录失败
            CrawlTask.objects.update_or_create(
                year=year,
                month=month,
                defaults={
                    'status': 'failed',
                    'error_message': '未获取到任何数据',
                    'completed_at': django_timezone.now(),
                }
            )
        time.sleep(2)  # 反爬间隔

        # 移动到下一个月
        # 12 月 → 下一年 1 月；其余月份 → +1
        if month == 12:
            current = datetime(year + 1, 1, 1)
        else:
            current = datetime(year, month + 1, 1)


def run_crawler():
    """
    一键运行入口：爬取近 12 个月数据并入库。

    这是命令行 `python manage.py shell -c "from app.crawler import run_crawler; run_crawler()"`
    或脚本直接调用的便捷函数。等价于前端点击"一键爬取"按钮。
    """
    raw_data = crawl_last_12_months()
    if raw_data:
        parse_and_save(raw_data)
    else:
        logger.warning('未获取到任何数据')


def fetch_forecast(area_id: int = None) -> int:
    """
    爬取 2345 天气网"40 天预报"数据并入库。

    ========== 与历史天气爬虫的区别 ==========
    历史天气：API 返回 JSON → data 字段是 HTML 表格 → BeautifulSoup 解析
    40天预报：请求 HTML 页面 → 页面内嵌 JS 变量含 JSON → 正则提取 JSON

    ========== 数据来源 ==========
    页面地址：https://tianqi.2345.com/wea_forty/60407.htm
    该页面在 <script> 标签中内嵌了一段 JSON，格式类似：
      {
        "data": [
          {
            "time": 1717200000,      ← Unix 时间戳（秒）
            "day_temp": 28,          ← 白天气温
            "night_temp": 18,        ← 夜间气温
            "weather": "多云转晴",    ← 天气描述
            "week": "周一"            ← 星期
          },
          ...共 40 条
        ]
      }

    ========== JSON 提取逻辑（核心难点）==========
    页面中的 JSON 可能不止一层数组嵌套（如 "data":[[...], ...]），
    简单的 .*? 非贪婪匹配会在第一个 ] 处停止，导致截断。

    解决方案（括号计数法）：
      遍历每个字符，遇到 [ 计数器+1，遇到 ] 计数器-1，
      当计数器归零时，才找到完整数组的结束位置。
      这保证了嵌套结构不会导致 JSON 截断。

    参数：
        area_id: 城市编码，默认 60407（都江堰）

    返回：
        int — 成功保存的 ForecastData 记录数
    """
    import json as json_module

    # 默认使用都江堰的城市编码
    if area_id is None:
        area_id = AREA_ID

    url = f'https://tianqi.2345.com/wea_forty/{area_id}.htm'
    # 请求 40 天预报页面，Referer 设为自己（从预报页发起请求）
    req_headers = {**HEADERS, 'Referer': url}

    logger.info(f'正在爬取 40 天预报: {url}')

    # ---- 步骤 1：请求预报页面 ----
    try:
        resp = requests.get(url, headers=req_headers, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f'预报页面请求失败: {e}')
        return 0

    # ---- 步骤 2：从 HTML 中提取内嵌 JSON ----
    # 页面源码中某处有 "data":[{...40条预报...}]
    # 用正则匹配 "data" 键后面的数组部分
    # re.DOTALL 让 . 也匹配换行符（JSON 可能跨多行）
    match = re.search(r'"data"\s*:\s*(\[.*?\])', resp.text, re.DOTALL)
    if not match:
        logger.error('未在页面中找到预报数据')
        return 0

    # ---- 步骤 3：括号计数法找到完整 JSON 数组 ----
    # 简单的非贪婪匹配 .*? 会在遇到第一个 ] 时就停止，
    # 如果数组内有嵌套 JSON 对象（含 { } 内的 ] 字符），会导致 JSON 不完整。
    # 括号计数法：统计 [ 和 ] 的配对，只有当计数归零时才是数组的真正结束。
    raw = match.group(1)  # 从第一个 [ 开始
    bracket_count = 0
    end_idx = 0
    for i, c in enumerate(raw):
        if c == '[':
            bracket_count += 1   # 遇到 [ 计数+1
        elif c == ']':
            bracket_count -= 1   # 遇到 ] 计数-1
            if bracket_count == 0:
                # 计数归零 → 找到了与第一个 [ 配对的 ]
                end_idx = i + 1
                break

    # ---- 步骤 4：解析 JSON ----
    try:
        forecast_list = json_module.loads(raw[:end_idx])
    except json_module.JSONDecodeError as e:
        logger.error(f'预报 JSON 解析失败: {e}')
        return 0

    # ---- 步骤 5：逐条入库 ----
    saved_count = 0
    for item in forecast_list:
        try:
            # Unix 时间戳（秒）→ Python datetime → date 对象
            ts = item.get('time', 0)
            date_obj = datetime.fromtimestamp(ts).date()

            # 以 date 为唯一键去重（同历史数据）
            ForecastData.objects.update_or_create(
                date=date_obj,
                defaults={
                    'day_temp': item.get('day_temp'),       # 白天气温（整数°C）
                    'night_temp': item.get('night_temp'),   # 夜间气温（整数°C）
                    'weather_desc': item.get('weather', ''), # 天气状况描述
                    'week': item.get('week', ''),            # 星期几
                }
            )
            saved_count += 1
        except Exception as e:
            logger.error(f'预报保存失败 {item}: {e}')

    logger.info(f'40天预报保存完成，共 {saved_count} 条')
    return saved_count


# ==================== 模块直接运行入口 ====================
if __name__ == '__main__':
    # 直接 `python crawler.py` 即可启动爬虫
    run_crawler()
