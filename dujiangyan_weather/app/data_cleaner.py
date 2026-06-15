"""
================================================================================
模块二：数据清洗（data_cleaner.py）
================================================================================
目标：把爬虫写入的"原始数据"变成"干净可分析的数据"。

清洗对象：WeatherData 表（6 个字段：date / max_temp / min_temp / weather_desc /
           wind_direction / wind_level / humidity）

清洗步骤（6 步流水线）：
  ① get_dataframe()           — 从数据库读取 → pandas DataFrame
  ② standardize_and_dedup()   — 日期标准化（统一为 YYYY-MM-DD）+ 按 date 去重
  ③ clean_outliers()          — 异常值检测（>50°C 或 <-30°C → NaN → 月均值替换）
  ④ clean_missing_values()    — 缺失值填充（前向填充 + 中位数兜底）
  ⑤ add_month_column()        — 新增 month 列（"2025-06" 格式）
  ⑥ compute_monthly_stats()   — 按月聚合（仅日志输出，不入库）

设计原则：
  - 所有清洗函数接受 DataFrame，返回 DataFrame（纯函数风格，可插拔组合）
  - 异常值用月均值替换而非直接删除，保留数据完整性
  - 缺失值优先用前向填充（天气数据有时间连续性），中位数兜底
  - 单条数据异常不中断全局（errors='coerce' + try/except）

================================================================================
"""

import pandas as pd
import numpy as np
import logging
from django.db.models import Q
from app.models import WeatherData

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_dataframe() -> pd.DataFrame:
    """
    从数据库读取所有 WeatherData 行 → pandas DataFrame。

    ========== 日期处理 ==========
    `errors='coerce'` 是关键：
      - 正常日期 "2025-06-01" → Timestamp
      - 异常日期 "abc" / None → NaT（Not a Time）
      避免一条坏日期导致整个 read 失败。

    最终按日期升序排列，为后续的 ffill（前向填充）做准备。
    """
    # 只取分析需要的字段，减少内存占用
    qs = WeatherData.objects.all().values(
        'id', 'date', 'max_temp', 'min_temp',
        'weather_desc', 'wind_direction', 'wind_level', 'humidity'
    )
    df = pd.DataFrame(qs)
    if df.empty:
        return df

    # 日期统一转为 Timestamp，无法解析的变成 NaT（不会报错）
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    # 按日期升序 + 重置索引（删除旧 index，保证行号连续）
    df = df.sort_values('date').reset_index(drop=True)
    return df


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    缺失值处理：温度字段（max_temp / min_temp）为空时的填充策略。

    ========== 两级兜底策略 ==========

    第一级 — ffill（前向填充）：
      用"前一天同字段的值"填充当前 NaN。
      选择 ffill 而非均值的原因：天气数据有强时间连续性，
      今天温度和昨天温度通常相差不超过 2-3°C，用前一天的
      值比用全月均值更接近真实值。

      例：
        date       max_temp
        6月1日     28.0
        6月2日     NaN       ← 用 28.0 填充
        6月3日     26.0

    第二级 — 中位数兜底：
      如果数据开头就是 NaN（没有"前一天"），ffill 无法处理，
      此时用该列的全局中位数填充。
      选择中位数而非均值：中位数不受极端值影响（如某天 40°C
      会拉高均值但不会影响中位数）。

    参数：
        df: 包含 max_temp 和/或 min_temp 列的 DataFrame

    返回：
        填充后的 DataFrame（原地修改）
    """
    for col in ['max_temp', 'min_temp']:
        if col not in df.columns:
            continue
        # 第一级：前向填充（用前一天同字段的值）
        # ffill() 从上往下传播最后一个非空值
        df[col] = df[col].ffill()
        # 第二级：若开头仍有缺失（第一条记录就是 NaN），用中位数填
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
    return df


def clean_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    异常值处理：温度超出物理可能范围时，用该月平均值替换。

    ========== 阈值设定依据 ==========
    - 上限 50°C：都江堰历史上最高温约 38°C（2022年极端高温），
      50°C 远超此值，必然是爬虫解析错误或数据源异常。
    - 下限 -30°C：都江堰冬季极端低温约 -3°C，-30°C 在四川盆地
      不可能出现，必然是错误数据。

    ========== 替换策略 ==========
    异常值 → 标记为 NaN → 用该月平均值替换 → 整月缺失用全局中位数兜底。

    为什么不直接删除？
      删除会丢失一整天的数据，导致月度统计天数不准确。
      用月均值替换虽然不够精确，但比删除整行好。

    为什么是按月分组而非全局？
      各月温度差异大（1月和7月差 20°C+），按月分组保证替换值
      符合当月气候特征。

    参数：
        df: 含 date、max_temp、min_temp 列的 DataFrame

    返回：
        处理后的 DataFrame（原地修改）
    """
    # 临时生成月份分组键（"2025-06" 格式），用于按月取均值
    temp_month = df['date'].dt.to_period('M').astype(str) if 'month' not in df.columns else df['month']

    for col in ['max_temp', 'min_temp']:
        if col not in df.columns:
            continue
        # 步骤 1：异常值标记为 NaN（不直接赋值，等后续替换）
        # 条件：> 50°C（不可能的高温）或 < -30°C（不可能的低温）
        df.loc[(df[col] > 50) | (df[col] < -30), col] = np.nan

        # 步骤 2：用该月平均值填充 NaN
        # transform(lambda x: x.fillna(x.mean())) 对每组独立计算均值并填充
        df[col] = df.groupby(temp_month)[col].transform(lambda x: x.fillna(x.mean()))

        # 步骤 3：整月缺失的兜底（如某月全部是 NaN，mean() 仍为 NaN）
        # 此时用全局中位数填充
        df[col] = df[col].fillna(df[col].median())
    return df


def standardize_and_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """
    日期标准化 + 按日期去重。

    ========== 去重策略 ==========
    keep='first'：同一天保留第一条记录。
    为什么保留第一条而非最后？
      在重复爬取场景中，第一次爬的数据通常是干净的原始数据；
      如果因为 bug 重复入库，保留第一条比保留最后一条更安全。

    无效日期行（NaT）在去重前被移除，避免它们被当作有效数据参与分析。

    参数：
        df: 含 date 列的 DataFrame

    返回：
        去重后的 DataFrame（新对象，非原地修改）
    """
    # 日期标准化（errors='coerce' 保证无法解析的变成 NaT 而非报错）
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # 移除无效日期行（date 为 NaT 的行）
    df = df.dropna(subset=['date'])

    # 按 date 去重，保留第一条
    df = df.drop_duplicates(subset=['date'], keep='first')

    # 按日期升序 + 重置索引
    df = df.sort_values('date').reset_index(drop=True)
    return df


def add_month_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    新增月份列，方便后续按月分组分析。

    ========== 输出格式 ==========
    date=2025-06-15 → month="2025-06"

    使用 to_period('M') 取月份期间，再转字符串。
    这比手动拼接 f"{year}-{month:02d}" 更健壮，自动处理跨年等情况。

    参数：
        df: 含 date 列的 DataFrame

    返回：
        新增 month 列的 DataFrame
    """
    df['month'] = df['date'].dt.to_period('M').astype(str)
    return df


def compute_monthly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    按月聚合统计（轻量版，仅输出日志，不修改数据库）。

    ========== 聚合维度 ==========
    - avg_max_temp：月均最高温（每天最高温的均值）
    - avg_min_temp：月均最低温（每天最低温的均值）
    - weather_distribution：天气分布（{"晴天": 12, "多云": 8, ...})
    - rainy_days：降雨天数（天气描述含"雨"的天数）

    注意：这是给 run_cleaning() 中快速查看清洗效果的，
    真正的月度统计入库由 analyzer.py 的 generate_monthly_stats() 完成，
    那里还包含了 5 项气候评分和 AI 建议。

    参数：
        df: 含 month、max_temp、min_temp、weather_desc 列的 DataFrame

    返回：
        聚合后的 DataFrame（含 month / max_temp / min_temp /
        weather_distribution / rainy_days 列）
    """
    if 'month' not in df.columns:
        df = add_month_column(df)

    # 基础聚合：按月取温度的均值和天气分布
    grouped = df.groupby('month').agg({
        'max_temp': 'mean',                           # 月均最高温
        'min_temp': 'mean',                           # 月均最低温
        'weather_desc': lambda x: x.value_counts().to_dict(),  # 天气分布字典
    }).rename(columns={'weather_desc': 'weather_distribution'})

    # 扩展：统计每月降雨天数
    # 天气描述中包含"雨"字即算降雨日（小雨、中雨、大雨、暴雨、阵雨都含"雨"）
    def count_rainy(series):
        """统计天气描述中含'雨'的行数"""
        return series.astype(str).str.contains('雨').sum()

    rainy_counts = df.groupby('month')['weather_desc'].apply(count_rainy)
    grouped['rainy_days'] = rainy_counts

    grouped = grouped.reset_index()
    return grouped


def save_cleaned(df: pd.DataFrame):
    """
    将清洗后的数据逐行回写到 WeatherData 表。

    ========== 回写策略 ==========
    - 逐行更新（非批量），因为清洗场景数据量通常不大（几百到几千行）
    - 只更新有 NaN 被修复的字段：max_temp / min_temp / humidity
    - 保留 2 位小数（round(..., 2)），统一数据库内精度
    - 单条异常（DoesNotExist / 类型错误）跳过不中断，日志中可追踪

    ========== 为什么逐行而非批量 ==========
    Django 的 bulk_update 虽然快，但需要提前知道要更新哪些字段，
    而这里每行被修复的字段可能不同（有的只缺温度，有的只缺湿度）。
    数据量小时逐行更新差异可忽略。

    参数：
        df: 已清洗的 DataFrame（必须含 id 列）
    """
    update_count = 0
    for _, row in df.iterrows():
        try:
            # 通过 id 精确定位原始记录
            obj = WeatherData.objects.get(id=int(row['id']))
            # 只覆盖被修复的字段（有值且非 NaN）
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
            # 记录不存在或类型转换失败，跳过该行
            continue
    logger.info(f'清洗后数据回写完成，共更新 {update_count} 条记录')


def run_cleaning():
    """
    一键执行完整清洗流水线（命令行或 Django management command 调用）。

    ========== 执行顺序（不可调换）==========
    ① 读取原始数据     → get_dataframe()
    ② 日期标准化 + 去重 → standardize_and_dedup()   （先去重，避免脏数据影响统计）
    ③ 异常值处理        → clean_outliers()           （检测 >50 或 <-30，用月均值替换）
    ④ 缺失值填充        → clean_missing_values()     （前向填充 + 中位数兜底）
    ⑤ 新增月份列        → add_month_column()          （为后续分析提供分组键）
    ⑥ 按月聚合          → compute_monthly_stats()     （仅日志输出，验证清洗效果）
    ⑦ 回写数据库        → save_cleaned()              （把修复后的值写回 WeatherData）

    为什么顺序是 ③→④ 而非 ④→③？
      先处理异常值（标记为 NaN），再统一做缺失值填充。
      这样异常值和真实缺失值走同一套填充逻辑，代码更简洁。
    """
    # 步骤 ①：读取
    df = get_dataframe()
    if df.empty:
        logger.warning('数据库中无数据，跳过清洗')
        return

    logger.info(f'原始数据量: {len(df)}')

    # 步骤 ②：日期标准化 + 去重
    df = standardize_and_dedup(df)
    logger.info(f'去重后数据量: {len(df)}')

    # 步骤 ③：异常值处理（>50°C 或 <-30°C → NaN → 月均值替换）
    df = clean_outliers(df)

    # 步骤 ④：缺失值填充（前向填充 → 中位数兜底）
    df = clean_missing_values(df)

    # 步骤 ⑤：新增月份列
    df = add_month_column(df)

    # 步骤 ⑥：按月统计（仅日志，验证清洗效果）
    monthly = compute_monthly_stats(df)
    logger.info(f'按月统计完成，共 {len(monthly)} 个月份')
    logger.info('\n' + monthly.to_string(index=False))

    # 步骤 ⑦：回写数据库
    save_cleaned(df)
    logger.info('数据清洗流程全部完成')


# ==================== 模块直接运行入口 ====================
if __name__ == '__main__':
    run_cleaning()
