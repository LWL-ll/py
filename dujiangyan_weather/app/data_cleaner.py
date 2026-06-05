"""
模块二：数据清洗模块
对原始天气数据进行清洗和补全
"""

import pandas as pd
from django.db.models import Q
from app.models import WeatherData


def get_dataframe() -> pd.DataFrame:
    """
    从数据库读取所有天气数据为 DataFrame
    """
    qs = WeatherData.objects.all().values()
    df = pd.DataFrame(qs)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    return df


def clean_temperature(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗温度数据：去除异常值，线性插值补全缺失
    """
    for col in ['max_temp', 'min_temp']:
        # 标记明显异常值（如超过 50 或低于 -30）
        df.loc[(df[col] > 50) | (df[col] < -30), col] = None
        # 线性插值
        df[col] = df[col].interpolate(method='linear')
    return df


def clean_humidity(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗湿度数据：限制 0-100 范围，填充缺失
    """
    if 'humidity' in df.columns:
        df.loc[(df['humidity'] > 100) | (df['humidity'] < 0), 'humidity'] = None
        df['humidity'] = df['humidity'].interpolate(method='linear')
        df['humidity'] = df['humidity'].fillna(df['humidity'].median())
    return df


def fill_missing_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    补齐缺失日期（如有），用于连续时间序列分析
    """
    if df.empty:
        return df
    df = df.set_index('date')
    df = df.asfreq('D')
    df = df.reset_index()
    # 对新增的空行进行简单填充
    for col in ['max_temp', 'min_temp']:
        if col in df.columns:
            df[col] = df[col].interpolate()
    return df


def save_cleaned(df: pd.DataFrame):
    """
    将清洗后的数据保存回数据库
    """
    for _, row in df.iterrows():
        if pd.isna(row.get('id')):
            continue
        try:
            obj = WeatherData.objects.get(id=int(row['id']))
            if 'max_temp' in row and pd.notna(row['max_temp']):
                obj.max_temp = round(float(row['max_temp']), 2)
            if 'min_temp' in row and pd.notna(row['min_temp']):
                obj.min_temp = round(float(row['min_temp']), 2)
            if 'humidity' in row and pd.notna(row['humidity']):
                obj.humidity = round(float(row['humidity']), 2)
            obj.save()
        except WeatherData.DoesNotExist:
            continue


def run_cleaning():
    """
    执行完整清洗流程
    """
    df = get_dataframe()
    if df.empty:
        print("数据库中无数据，跳过清洗")
        return
    print(f"原始数据量: {len(df)}")
    df = clean_temperature(df)
    df = clean_humidity(df)
    df = fill_missing_dates(df)
    save_cleaned(df)
    print("清洗完成并已保存")
