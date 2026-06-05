"""
模块一：爬虫模块
用于抓取都江堰历史天气数据
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from app.models import WeatherData


HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36'
    )
}


def fetch_month(year: int, month: int) -> list:
    """
    抓取指定年月的天气数据
    返回原始数据列表
    """
    url = f"https://tianqi.2345.com/Pc/GetHistory?areaInfo%5BareaId%5D=56290&areaInfo%5BareaType%5D=2&date%5Byear%5D={year}&date%5Bmonth%5D={month}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        html = data.get('data', '')
        soup = BeautifulSoup(html, 'html.parser')
        rows = soup.find_all('tr')
        results = []
        for row in rows[1:]:  # skip header
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
    except Exception as e:
        print(f"抓取 {year}-{month} 失败: {e}")
        return []


def parse_and_save(raw_list: list):
    """
    解析原始数据并保存到数据库
    """
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
        except Exception as e:
            print(f"解析保存失败 {item}: {e}")


def crawl_range(start_year: int, start_month: int, end_year: int, end_month: int):
    """
    爬取指定时间范围的数据
    """
    current = datetime(start_year, start_month, 1)
    end = datetime(end_year, end_month, 1)
    while current <= end:
        year = current.year
        month = current.month
        print(f"正在抓取 {year}-{month:02d} ...")
        raw = fetch_month(year, month)
        if raw:
            parse_and_save(raw)
            print(f"  成功保存 {len(raw)} 条")
        time.sleep(1)
        # 移动到下一个月
        if month == 12:
            current = datetime(year + 1, 1, 1)
        else:
            current = datetime(year, month + 1, 1)
