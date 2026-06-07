"""
模块一：网络爬虫（crawler.py）
用于抓取都江堰历史天气数据

功能：自动计算当前日期往前推12个月，逐月爬取都江堰每日天气
输出：list[dict]，字段：date, max_temp, min_temp, weather, wind
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime

from app.models import WeatherData

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
        'Chrome/115.0.0.0 Safari/537.36'
    )
}
AREA_ID = 56290  # 都江堰
BASE_URL = 'https://tianqi.2345.com/Pc/GetHistory'


def fetch_month(year: int, month: int) -> list:
    """
    抓取指定年月的天气数据。

    反爬策略：
        1. 请求头携带 User-Agent 伪装浏览器
        2. try/except 包裹，超时/断网重试 1 次
        3. 失败记录日志并跳过该月

    返回：list[dict]
        字段：date, max_temp, min_temp, weather, wind
    """
    url = (
        f'{BASE_URL}?'
        f'areaInfo%5BareaId%5D={AREA_ID}&areaInfo%5BareaType%5D=2'
        f'&date%5Byear%5D={year}&date%5Bmonth%5D={month}'
    )
    max_attempts = 2  # 首次请求 + 重试 1 次

    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
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

                date_str = tds[0].get_text(strip=True)
                max_temp = tds[1].get_text(strip=True).replace('℃', '')
                min_temp = tds[2].get_text(strip=True).replace('℃', '')
                weather = tds[3].get_text(strip=True)
                wind = tds[4].get_text(strip=True)

                results.append({
                    'date': date_str,
                    'max_temp': max_temp,
                    'min_temp': min_temp,
                    'weather': weather,
                    'wind': wind,
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
    now = datetime.now()
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
        time.sleep(2)  # 反爬：每月请求间隔 2 秒

    logger.info(f'总计获取 {len(all_data)} 条数据')
    return all_data


def parse_and_save(raw_list: list) -> int:
    """
    解析原始数据并保存到数据库。

    参数：
        raw_list: crawl_last_12_months() 的返回值

    返回：
        成功保存的记录数
    """
    saved_count = 0
    for item in raw_list:
        try:
            date_obj = datetime.strptime(item['date'], '%Y-%m-%d').date()
            max_temp = float(item['max_temp']) if item['max_temp'] else None
            min_temp = float(item['min_temp']) if item['min_temp'] else None

            wind_text = item.get('wind', '')
            wind_parts = wind_text.split(' ') if wind_text else ['', '']
            wind_direction = wind_parts[0]
            wind_level = wind_parts[1] if len(wind_parts) > 1 else ''

            WeatherData.objects.update_or_create(
                date=date_obj,
                defaults={
                    'max_temp': max_temp,
                    'min_temp': min_temp,
                    'weather_desc': item.get('weather', ''),
                    'wind_direction': wind_direction,
                    'wind_level': wind_level,
                }
            )
            saved_count += 1
        except Exception as e:
            logger.error(f'解析保存失败 {item}: {e}')

    logger.info(f'成功保存 {saved_count} 条数据到数据库')
    return saved_count


def crawl_range(start_year: int, start_month: int, end_year: int, end_month: int):
    """
    （保留）爬取指定时间范围的数据并直接入库。
    """
    current = datetime(start_year, start_month, 1)
    end = datetime(end_year, end_month, 1)

    while current <= end:
        year = current.year
        month = current.month
        logger.info(f'正在抓取 {year}-{month:02d} ...')
        raw = fetch_month(year, month)
        if raw:
            parse_and_save(raw)
            logger.info(f'  成功保存 {len(raw)} 条')
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
