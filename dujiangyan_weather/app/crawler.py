"""
模块一：网络爬虫（crawler.py）
用于抓取都江堰历史天气数据

功能：自动计算当前日期往前推12个月，逐月爬取都江堰每日天气
输出：list[dict]，字段：date, max_temp, min_temp, weather, wind, humidity
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from datetime import datetime
from django.utils import timezone as django_timezone

from app.models import WeatherData, CrawlTask

# ---------- 日志配置 ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------- 常量 ----------
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/131.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'X-Requested-With': 'XMLHttpRequest',
}
AREA_ID = 60407  # 都江堰（2345天气网城市编码）
BASE_URL = 'https://tianqi.2345.com/Pc/GetHistory'
# Referer 需要根据当前 AREA_ID 动态设置
REFERER_URL = f'https://tianqi.2345.com/wea_history/{AREA_ID}.htm'


def fetch_month(year: int, month: int) -> list:
    """
    抓取指定年月的天气数据。

    反爬策略：
        1. 请求头携带完整浏览器标识（User-Agent + Referer + X-Requested-With）
        2. try/except 包裹，超时/断网重试 1 次
        3. 失败记录日志并跳过该月

    返回：list[dict]
        字段：date, max_temp, min_temp, weather, wind, humidity
    """
    url = (
        f'{BASE_URL}?'
        f'areaInfo%5BareaId%5D={AREA_ID}&areaInfo%5BareaType%5D=2'
        f'&date%5Byear%5D={year}&date%5Bmonth%5D={month}'
    )
    max_attempts = 2  # 首次请求 + 重试 1 次

    # 构造包含 Referer 的请求头
    req_headers = {**HEADERS, 'Referer': REFERER_URL}

    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, headers=req_headers, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            html = payload.get('data', '')
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.find_all('tr')

            results = []
            for row in rows[1:]:  # 跳过表头
                tds = row.find_all('td')
                if len(tds) < 5:
                    continue

                # 数据格式：日期 | 最高温 | 最低温 | 天气 | 风向风力 | 湿度
                date_str = tds[0].get_text(strip=True)
                # 提取纯数字（温度值可能是 "25°" 或 "25℃" 格式）
                max_temp = re.sub(r'[^\d.-]', '', tds[1].get_text(strip=True))
                min_temp = re.sub(r'[^\d.-]', '', tds[2].get_text(strip=True))
                weather = tds[3].get_text(strip=True)
                wind = tds[4].get_text(strip=True)

                # 湿度是第 6 列（可能是 "37 优" 或 "-" 格式）
                humidity = ''
                if len(tds) >= 6:
                    humidity_text = tds[5].get_text(strip=True)
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
            return results

        except requests.exceptions.RequestException as e:
            logger.warning(f'请求 {year}-{month:02d} 失败（第 {attempt + 1} 次）: {e}')
            if attempt < max_attempts - 1:
                time.sleep(2)  # 重试前等待
            else:
                logger.error(f'抓取 {year}-{month:02d} 最终失败，跳过该月')
                return []
        except Exception as e:
            logger.error(f'解析 {year}-{month:02d} 数据失败: {e}')
            return []


def crawl_last_12_months() -> list:
    """
    自动计算当前日期往前推 12 个月，逐月爬取都江堰每日天气。

    反爬策略：
        每月请求间隔 time.sleep(2)

    返回：拼接后的 list[dict]
    """
    now = django_timezone.now()
    months = []

    # 构造过去 12 个月（含当前月）
    for i in range(12):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        months.append((year, month))

    months = sorted(months)  # 按时间正序排列，便于观察
    logger.info(f'计划爬取月份: {months}')

    all_data = []
    for year, month in months:
        logger.info(f'正在抓取 {year}-{month:02d} ...')
        month_data = fetch_month(year, month)
        if month_data:
            all_data.extend(month_data)
            logger.info(f'  成功获取 {len(month_data)} 条')
            # 逐月入库并追踪状态
            try:
                parse_and_save(month_data, year=year, month=month)
            except Exception as e:
                logger.error(f'  保存 {year}-{month:02d} 失败: {e}')
        else:
            # 标记该月爬取失败
            CrawlTask.objects.update_or_create(
                year=year,
                month=month,
                defaults={
                    'status': 'failed',
                    'error_message': '未获取到任何数据',
                    'completed_at': django_timezone.now(),
                }
            )
        time.sleep(2)  # 反爬：每月请求间隔 2 秒

    logger.info(f'总计获取 {len(all_data)} 条数据')
    return all_data


def parse_and_save(raw_list: list, year: int = None, month: int = None) -> int:
    """
    解析原始数据并保存到数据库。

    参数：
        raw_list: crawl_last_12_months() 的返回值
        year:     年份（用于更新 CrawlTask 状态）
        month:    月份（用于更新 CrawlTask 状态）

    返回：
        成功保存的记录数
    """
    # 更新 CrawlTask 状态为 running（如果有指定年月）
    task = None
    if year and month:
        task, _ = CrawlTask.objects.update_or_create(
            year=year,
            month=month,
            defaults={'status': 'running', 'error_message': ''}
        )

    saved_count = 0
    try:
        for item in raw_list:
            try:
                # 日期格式为 "2025-06-01 周六"，截取前 10 位 "2025-06-01"
                date_str = item['date'][:10] if len(item['date']) >= 10 else item['date']
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                max_temp = float(item['max_temp']) if item['max_temp'] else None
                min_temp = float(item['min_temp']) if item['min_temp'] else None

                wind_text = item.get('wind', '')
                wind_parts = wind_text.split(' ') if wind_text else ['', '']
                wind_direction = wind_parts[0]
                wind_level = wind_parts[1] if len(wind_parts) > 1 else ''

                # 湿度（字符串，可能为空或 '-'）
                humidity_str = item.get('humidity', '')
                humidity = float(humidity_str) if humidity_str and humidity_str != '-' else None

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
                logger.error(f'解析保存失败 {item}: {e}')

        # 标记 CrawlTask 为成功
        if task:
            task.status = 'success'
            task.records_count = saved_count
            task.completed_at = django_timezone.now()
            task.save()

    except Exception as e:
        # 整体异常，标记 CrawlTask 为失败
        if task:
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = django_timezone.now()
            task.save()
        raise

    logger.info(f'成功保存 {saved_count} 条数据到数据库')
    return saved_count


def crawl_range(start_year: int, start_month: int, end_year: int, end_month: int):
    """
    （保留）爬取指定时间范围的数据并直接入库，同时追踪 CrawlTask 状态。
    """
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
            CrawlTask.objects.update_or_create(
                year=year,
                month=month,
                defaults={
                    'status': 'failed',
                    'error_message': '未获取到任何数据',
                    'completed_at': django_timezone.now(),
                }
            )
        time.sleep(2)

        # 移动到下一个月
        if month == 12:
            current = datetime(year + 1, 1, 1)
        else:
            current = datetime(year, month + 1, 1)


def run_crawler():
    """
    一键运行：爬取近 12 个月数据并入库。
    """
    raw_data = crawl_last_12_months()
    if raw_data:
        parse_and_save(raw_data)
    else:
        logger.warning('未获取到任何数据')


if __name__ == '__main__':
    run_crawler()
