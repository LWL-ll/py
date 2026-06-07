"""
模块二：数据清洗（data_cleaner.py）
对原始天气数据进行清洗、补全和按月统计
"""

import pandas as pd
import numpy as np
import logging
from django.db.models import Q
from app.models import WeatherData

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_dataframe() -> pd.DataFrame:
    """
    从数据库读取所有天气数据为 DataFrame，并统一日期格式。
    """
    qs = WeatherData.objects.all().values(
        'id', 'date', 'max_temp', 'min_temp', 'weather_desc', 'wind_direction', 'wind_level', 'humidity'
    )
    df = pd.DataFrame(qs)
    if df.empty:
        return df

    # 日期格式统一为 YYYY-MM-DD

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values('date').reset_index(drop=True)
    return df


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    缺失值处理：温度为空时，优先按前一天同字段填充，否则用列中位数填充。
    """
    for col in ['max_temp', 'min_temp']:
        if col not in df.columns:
            continue
        # 先尝试用前一天同字段填充（时间序列前向填充）
        df[col] = df[col].ffill()
        # 若开头仍有缺失，再用该列中位数填充
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
    return df


def clean_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    异常值处理：温度 > 50 或 < -30 时先标记为 NaN，再用该月平均值替换。
    需要先有 month 列，或在此函数内临时计算。
    """
    # 临时生成月份列用于分组替换（若不存在）
    temp_month = df['date'].dt.to_period('M').astype(str) if 'month' not in df.columns else df['month']

    for col in ['max_temp', 'min_temp']:
        if col not in df.columns:
            continue
        # 标记异常值为 NaN
        df.loc[(df[col] > 50) | (df[col] < -30), col] = np.nan
        # 用该月平均值替换
        df[col] = df.groupby(temp_month)[col].transform(lambda x: x.fillna(x.mean()))
        # 若整月缺失（如该月无数据），再用全局中位数兜底
        df[col] = df[col].fillna(df[col].median())
    return df


def standardize_and_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """
    日期格式标准化 + 按日期去重（保留第一条）。
    """
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    # 去除无效日期行
    df = df.dropna(subset=['date'])
    # 去重
    df = df.drop_duplicates(subset=['date'], keep='first')
    df = df.sort_values('date').reset_index(drop=True)
    return df


def add_month_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    新增月份列：df['month'] = df['date'].dt.to_period('M').astype(str)
    示例值：'2025-06'
    """
    df['month'] = df['date'].dt.to_period('M').astype(str)
    return df


def compute_monthly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    按月统计：
        df.groupby('month').agg({
            'max_temp': 'mean',
            'min_temp': 'mean',
            'weather_desc': lambda x: x.value_counts().to_dict()
        })
    返回聚合后的 DataFrame（含 rainy_days 等扩展字段）。
    """
    if 'month' not in df.columns:
        df = add_month_column(df)

    grouped = df.groupby('month').agg({
        'max_temp': 'mean',
        'min_temp': 'mean',
        'weather_desc': lambda x: x.value_counts().to_dict(),
    }).rename(columns={'weather_desc': 'weather_distribution'})

    # 扩展：统计降雨天数（天气描述含"雨"字的记录数）
    def count_rainy(series):
        return series.astype(str).str.contains('雨').sum()

    rainy_counts = df.groupby('month')['weather_desc'].apply(count_rainy)
    grouped['rainy_days'] = rainy_counts

    grouped = grouped.reset_index()
    return grouped


def save_cleaned(df: pd.DataFrame):
    """
    将清洗后的数据保存回数据库。
    """
    update_count = 0
    for _, row in df.iterrows():
        try:
            obj = WeatherData.objects.get(id=int(row['id']))
            if 'max_temp' in row and pd.notna(row['max_temp']):
                obj.max_temp = round(float(row['max_temp']), 2)
            if 'min_temp' in row and pd.notna(row['min_temp']):
                obj.min_temp = round(float(row['min_temp']), 2)
            if 'humidity' in row and pd.notna(row['humidity']):
                obj.humidity = round(float(row['humidity']), 2)
            # 若清洗过程中 weather_desc 被修正也可同步
            if 'weather_desc' in row and pd.notna(row['weather_desc']):
                obj.weather_desc = str(row['weather_desc'])
            obj.save()
            update_count += 1
        except (WeatherData.DoesNotExist, ValueError, TypeError):
            continue
    logger.info(f'清洗后数据回写完成，共更新 {update_count} 条记录')


def run_cleaning():
    """
    执行完整清洗流程：
        1. 从数据库读取原始数据
        2. 标准化日期并去重
        3. 异常值处理
        4. 缺失值填充
        5. 新增月份列
        6. （可选）按月统计
        7. 保存回数据库
    """
    df = get_dataframe()
    if df.empty:
        logger.warning('数据库中无数据，跳过清洗')
        return

    logger.info(f'原始数据量: {len(df)}')

    # 步骤 1：日期标准化 + 去重
    df = standardize_and_dedup(df)
    logger.info(f'去重后数据量: {len(df)}')

    # 步骤 2：异常值处理（>50 或 <-30 标记为 NaN，再用该月平均值替换）
    df = clean_outliers(df)

    # 步骤 3：缺失值填充（前一天同字段 → 中位数）
    df = clean_missing_values(df)

    # 步骤 4：新增月份列
    df = add_month_column(df)

    # 步骤 5：按月统计（仅输出日志，不入库）
    monthly = compute_monthly_stats(df)
    logger.info(f'按月统计完成，共 {len(monthly)} 个月份')
    logger.info('\n' + monthly.to_string(index=False))

    # 步骤 6：保存回数据库
    save_cleaned(df)
    logger.info('数据清洗流程全部完成')


if __name__ == '__main__':
    run_cleaning()
