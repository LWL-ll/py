"""
================================================================================
数据模型（models.py）— 5 张核心业务表
================================================================================

【ORM 是什么？3 条映射规则】
  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
  │  Python 类   │ ←──→  │  Django ORM  │ ←──→  │  MySQL 数据库 │
  │  (models.py) │        │  (翻译引擎)   │        │  (SQL 引擎)   │
  └──────────────┘        └──────────────┘        └──────────────┘
  1. 一个 Python 类       =  数据库中的一张表
  2. 一个类属性(Field)    =  表中的一个列（字段）
  3. 一个类实例(obj)      =  表中的一行数据

【ORM vs 原生 SQL 对比】
  原生 SQL:   INSERT INTO weather_data (date, max_temp) VALUES ('2025-06-15', 28.5)
  Django ORM: WeatherData.objects.create(date='2025-06-15', max_temp=28.5)
  → ORM 让你用 Python 代码操作数据库，Django 自动翻译成 SQL，不用手写。

【Models.Field 核心参数速查（反复出现的参数含义）】
  verbose_name  = Django Admin 显示的中文名
  null=True     = 数据库允许存 NULL（数据库层面）
  blank=True    = Django 表单验证允许空值（Python 层面）
  unique=True   = 创建 UNIQUE 索引，该列值不可重复
  db_index=True = 创建普通索引，加速该列的查询（如 WHERE / GROUP BY）
  default=X     = 创建记录时如果没传值，默认填充 X
  choices=X     = 限定该列只能取枚举中的值（Django Admin 显示下拉框）
  auto_now_add  = 仅在第一次创建记录时自动填入当前时间
  auto_now      = 每次调用 save() 都自动更新为当前时间

【表关系总览】
  WeatherData (每日天气)  ──[聚合]──→  MonthlyStats (月度统计)
                                            │
                                            └──[AI生成]──→ ClothingAdvice (生活建议)
  CrawlTask (爬虫任务追踪) ──[记录]──→ WeatherData
  ForecastData (40天预报)  ──[独立]──→ 与 WeatherData 无外键，各自存储
================================================================================
"""

from django.db import models


# ================================================================================
# 表 1：weather_data — 每日天气数据（核心表）
# ================================================================================
# 一张表 ≈ 一个 Excel 工作表，列 = 字段，行 = 每天的天气记录。
# 爬虫写入 → 清洗修正 → 分析读取 → 前端展示，是整个系统的数据根基。
# ================================================================================

class WeatherData(models.Model):
    """
    每日天气数据（核心数据表，爬虫写入、清洗修改、分析读取）。

    一行数据 = 都江堰某一天的实测天气快照。
    来源：2345 天气网历史天气页面（爬虫抓取）。
    """

    # ---- 天气类型枚举（weather_type 列的合法取值）----
    # choices 参数的格式：[(数据库存储值, 人类可读标签), ...]
    WEATHER_TYPE_CHOICES = [
        ('sunny',   '晴天'),
        ('cloudy',  '多云'),
        ('overcast','阴天'),
        ('rainy',   '雨天'),
        ('snowy',   '雪天'),
        ('foggy',   '雾/霾'),
    ]

    # =========================================================================
    # date：日期（唯一索引列）
    #   - DateField       → MySQL: DATE 类型（如 '2025-06-15'）
    #   - unique=True     → MySQL: UNIQUE 索引，同一个日期不能插入两次
    #   - 这是 update_or_create() 的去重依据：按 date 查找，存在则更新，不存在则创建
    # =========================================================================
    date = models.DateField(verbose_name='日期', unique=True)

    # =========================================================================
    # max_temp：最高温度(℃)
    #   - FloatField      → MySQL: DOUBLE 类型（双精度浮点）
    #   - null=True       → 数据库允许 NULL（爬虫可能漏数据，NULL 表示"暂无"）
    #   - blank=True      → Django 表单/Admin 后台可以不填
    #   - 为什么用 Float 不用 Integer？实测温度保留 1 位小数（如 28.5°C）
    # =========================================================================
    max_temp = models.FloatField(verbose_name='最高温度(℃)', null=True, blank=True)

    # =========================================================================
    # min_temp：最低温度(℃)
    #   - 同 max_temp，Float 类型，允许 NULL
    #   - NULL 值由清洗流程（data_cleaner.py）补全：取前后天均值插值
    # =========================================================================
    min_temp = models.FloatField(verbose_name='最低温度(℃)', null=True, blank=True)

    # =========================================================================
    # weather_desc：天气描述（爬虫拿到的原始中文文本）
    #   - CharField       → MySQL: VARCHAR(50)，变长字符串，最多 50 个字符
    #   - blank=True      → 允许空字符串（某天无描述时存 ''）
    #   - 示例值："多云~晴"、"小雨转阴"、"雷阵雨"、"阴天"
    #   - 这个字段是原始数据，weather_type 由它自动推断得出
    # =========================================================================
    weather_desc = models.CharField(max_length=50, verbose_name='天气状况', blank=True)

    # =========================================================================
    # weather_type：天气分类标签（自动推断，不需手动填写）
    #   - max_length=20   → VARCHAR(20)，容纳最长的枚举值 'overcast'（8 字符）
    #   - choices=...     → 限定只能取 6 种枚举值之一
    #   - db_index=True   → MySQL: CREATE INDEX，加速 GROUP BY weather_type（饼图查询）
    #   - blank=True      → 允许空字符串（weather_desc 也无法推断时）
    #   - 自动填充机制：见下方的 save() 方法和 infer_weather_type() 静态方法
    # =========================================================================
    weather_type = models.CharField(
        max_length=20,
        choices=WEATHER_TYPE_CHOICES,
        verbose_name='天气类型',
        blank=True,
        db_index=True,  # 建索引 → 饼图/热力图的分类查询更快
    )

    # =========================================================================
    # wind_direction：风向
    #   - CharField       → MySQL: VARCHAR(50)
    #   - 示例值："东南风"、"北风"、"西北风"
    #   - 爬虫层已按空格拆分原始字符串（如 "东南风 2级" → wind_direction="东南风"）
    # =========================================================================
    wind_direction = models.CharField(max_length=50, verbose_name='风向', blank=True)

    # =========================================================================
    # wind_level：风力等级
    #   - CharField       → MySQL: VARCHAR(20)
    #   - 示例值："2级"、"3-4级"、"5-6级"
    #   - 为什么用 CharField 而非 IntegerField？因为风力有 "3-4级" 这种范围格式
    # =========================================================================
    wind_level = models.CharField(max_length=20, verbose_name='风力', blank=True)

    # =========================================================================
    # humidity：相对湿度百分比
    #   - FloatField      → MySQL: DOUBLE NULL
    #   - 取值范围 0-100，NULL 表示该天无湿度数据
    #   - 爬虫来源可能缺失（某些天气页面不提供湿度），所以 null=True
    # =========================================================================
    humidity = models.FloatField(verbose_name='湿度(%)', null=True, blank=True)

    # =========================================================================
    # created_at：记录入库时间
    #   - DateTimeField   → MySQL: DATETIME 类型（如 '2025-06-15 14:30:00'）
    #   - auto_now_add=True → 只在第一次 INSERT 时自动填当前时间
    #   - 后续 UPDATE 不会改变这个值（与 auto_now 的区别）
    #   - 注意：这不是天气数据的"观测时间"，而是"写入数据库的时间"
    # =========================================================================
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    # =========================================================================
    # Meta 内部类 — 不映射为数据库列，而是控制表级别的元数据
    # =========================================================================
    class Meta:
        # db_table：自定义 MySQL 表名
        #   不写这一行 → 默认表名是 'app_weatherdata'（<应用名>_<类名小写>）
        #   写了这一行 → 表名固定为 'weather_data'，简洁且语义明确
        db_table = 'weather_data'

        # verbose_name：Django Admin 后台显示的单个对象名
        verbose_name = '天气数据'

        # verbose_name_plural：复数形式显示名（中文无复数，设为相同）
        verbose_name_plural = verbose_name

        # ordering：默认排序规则
        #   '-date' = 按日期降序（DESC），最新的记录排在前面
        #   去掉负号 'date' = 按日期升序（ASC），最早的在前面
        #   这里的 '-' 等价于 SQL 的 DESC
        ordering = ['-date']

    def __str__(self):
        """
        Python 对象的字符串表示（print(obj) / Django Admin 列表页 调用）。
        例如：print(weather_obj) → "2025-06-15 多云~晴"
        """
        return f"{self.date} {self.weather_desc}"

    # =========================================================================
    # save() — 重写父类的保存方法，实现"保存前自动推断天气类型"
    # =========================================================================
    def save(self, *args, **kwargs):
        """
        重写 save()：保存前自动根据天气描述推断 weather_type。

        执行流程：
          1. self.infer_weather_type(self.weather_desc) → 得到分类标签（如 'rainy'）
          2. 赋值给 self.weather_type
          3. super().save() → 调用 Django 原生的 save() → 执行 INSERT 或 UPDATE

        为什么重写 save() 而不是在别处处理？
          - 统一入口：无论数据从哪里进来（爬虫批量写入、Django Admin 手动添加、
            脚本导入、API 创建），weather_type 都会自动填充，保证一致性。
          - 防止遗漏：如果只在视图中处理，Admin 直接添加数据就会漏掉。
        """
        # 步骤 1：调用静态方法推断天气类型
        self.weather_type = self.infer_weather_type(self.weather_desc)
        # 步骤 2：调用 Django 原生 save()，执行实际的数据库写入
        super().save(*args, **kwargs)

    # =========================================================================
    # infer_weather_type() — 静态方法：根据天气描述文本推断分类标签
    # =========================================================================
    @staticmethod
    def infer_weather_type(desc: str) -> str:
        """
        根据天气描述文本推断分类标签（子串匹配，优先级从高到低）。

        优先级链设计原则：
          雪 > 雨 > 雾/霾 > 多云 > 阴 > 晴
          （影响越大、越极端 → 优先级越高）

        为什么这样排序？—— 用复合天气举例：
          "小雨转多云" 同时含 "雨" 和 "多云" → 归为 "rainy"（雨天）
          因为降雨对穿衣/出行/运动的影响远大于多云，应该归类为雨天。
          同理 "雨夹雪" 同时含 "雨" 和 "雪" → 归为 "snowy"（雪天），
          因为雪天比雨天更极端。

        为什么用子串搜索（'雨' in desc）而不是精确匹配？
          天气描述格式极多变："小雨"、"阵雨"、"雷阵雨"、"小雨转阴"、
          "中到大雨"、"零星阵雨"... 精确匹配需要穷举所有可能性，不可行。
          子串搜索用一个 '雪' 字就能覆盖所有含雪的情况。

        Args:
            desc: 天气描述原文（如 "小雨转阴"）

        Returns:
            分类标签字符串（如 'rainy'），无法判断时返回空字符串 ''
        """
        if not desc:
            return ''           # 空输入 → 返回空串（防御性编程）

        desc = str(desc)        # 确保是字符串类型（防御非 str 输入）

        # 优先级 1：含 "雪" → 雪天（最高优先级，雪对生活影响最大）
        if '雪' in desc:
            return 'snowy'

        # 优先级 2：含 "雨" → 雨天（降雨影响出行/运动/农业）
        if '雨' in desc:
            return 'rainy'

        # 优先级 3：含 "雾" 或 "霾" → 雾/霾（影响能见度和健康）
        if '雾' in desc or '霾' in desc:
            return 'foggy'

        # 优先级 4：含 "多云" → 多云（注意：必须在阴天之前，因为 "多云转阴" 也含 "阴"）
        if '多云' in desc:
            return 'cloudy'

        # 优先级 5：含 "阴" → 阴天
        if '阴' in desc:
            return 'overcast'

        # 优先级 6：含 "晴" → 晴天（放最后，因为 "多云转晴" 也含 "多云"，已在上方匹配）
        if '晴' in desc:
            return 'sunny'

        return ''  # 所有关键字都不匹配 → 返回空字符串


# ================================================================================
# 表 2：monthly_stats — 月度天气统计（聚合表）
# ================================================================================
# 这张表的数据不是爬虫直接写入的，而是由 analyzer.py 的
# generate_monthly_stats() 从 weather_data 按 (year, month) 聚合生成。
# 一个月一行，存储该月的温度极值、降雨天数、天气分布、5项气候评分。
# ================================================================================

class MonthlyStats(models.Model):
    """
    月度统计数据（每月一行，由 analyzer.py 的 generate_monthly_stats() 生成）。

    数据来源：对 WeatherData 按 (year, month) 分组聚合。

    【4 个温度统计量区别——容易混淆！】
      avg_max_temp  = 当月每天"最高温"的平均值    （月均最高温，如 28.5°C）
      avg_min_temp  = 当月每天"最低温"的平均值    （月均最低温，如 20.3°C）
      max_temp_record = 当月"最高温"的最大值        （这个月最热那天，如 35°C）
      min_temp_record = 当月"最低温"的最小值        （这个月最冷那天，如 15°C）
      → avg_max_temp ≠ max_temp_record！前者是平均数，后者是极值。
    """

    # =========================================================================
    # year + month：联合唯一键
    #   两个 IntegerField 组合 = 联合唯一约束
    #   数据库中 (year=2025, month=6) 只能存在一条记录
    #   等同于 SQL: UNIQUE KEY (year, month)
    # =========================================================================
    year = models.IntegerField(verbose_name='年份')       # MySQL: INT，如 2025
    month = models.IntegerField(verbose_name='月份')      # MySQL: INT，如 6

    # ---- 温度统计（4 个字段，含义见上方 docstring）----
    avg_max_temp = models.FloatField(verbose_name='月均最高温', null=True, blank=True)
    #   ↑ MySQL: DOUBLE NULL。例如 6 月每天最高温加起来 / 30 = 28.5°C

    avg_min_temp = models.FloatField(verbose_name='月均最低温', null=True, blank=True)
    #   ↑ 例如 6 月每天最低温加起来 / 30 = 20.3°C

    max_temp_record = models.FloatField(verbose_name='月最高温记录', null=True, blank=True)
    #   ↑ 这个月里所有 max_temp 的最大值，如 6 月最热那天 35°C

    min_temp_record = models.FloatField(verbose_name='月最低温记录', null=True, blank=True)
    #   ↑ 这个月里所有 min_temp 的最小值，如 6 月最冷那天 15°C

    # ---- 降水与湿度 ----
    rainy_days = models.IntegerField(verbose_name='降雨天数', default=0)
    #   ↑ MySQL: INT DEFAULT 0。统计 weather_desc 中包含"雨"字的天数

    avg_humidity = models.FloatField(verbose_name='平均湿度', null=True, blank=True)
    #   ↑ 当月所有 humidity 非空值的平均值

    # ---- 天气分布（JSON 列，存储各天气描述的出现次数）----
    #   JSONField → MySQL: JSON 列，可以直接存储 Python dict
    #   default=dict → 新记录默认值为 {}（空字典）
    #   存储示例：
    #     {"多云~晴": 12, "小雨": 5, "阴天": 8, "阵雨": 3, "雷阵雨": 2}
    #   读取时 Django 自动反序列化为 Python dict，无需手动 json.loads()
    weather_distribution = models.JSONField(
        verbose_name='天气分布',
        default=dict,
        blank=True,
    )

    # ---- 5 项气候综合评分（0-100，前端雷达图直接使用）----
    #   每个评分由 analyzer.py 中对应的 _calc_* 函数独立计算
    #   都是 IntegerField，因为评分只需要整数（0-100）

    temp_comfort_score = models.IntegerField(
        verbose_name='温度舒适度', null=True, blank=True,
        help_text='0-100，越高越舒适。依据：月均温度距离人体舒适区间(18~26°C)的偏差'
    )
    humidity_comfort_score = models.IntegerField(
        verbose_name='湿度适宜度', null=True, blank=True,
        help_text='0-100，越高越适宜。依据：月均湿度与适宜区间(40%~70%)的匹配度'
    )
    sunlight_score = models.IntegerField(
        verbose_name='日照充足度', null=True, blank=True,
        help_text='0-100，越高阳光越充足。依据：晴天+多云天数占总天数的比例'
    )
    air_quality_score = models.IntegerField(
        verbose_name='空气质量', null=True, blank=True,
        help_text='0-100，越高越好。综合湿度、极端天气频率等间接指标估算'
    )
    precipitation_score = models.IntegerField(
        verbose_name='降水适中度', null=True, blank=True,
        help_text='0-100，越接近50越适中。太少=干旱，太多=洪涝。依据：降雨天数与理想值的偏差'
    )

    # ---- 时间戳 ----
    # auto_now_add=True：创建记录时自动填入当前时间，之后不再改变
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # auto_now=True：每次调用 save() 都自动更新为当前时间（追踪最后修改时间）
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        # 自定义表名（否则默认是 'app_monthlystats'）
        db_table = 'monthly_stats'
        verbose_name = '月度统计'
        verbose_name_plural = verbose_name
        # unique_together：联合唯一约束
        #   数据库层面保证 (year, month) 组合不重复
        #   例如：(2025, 6) 只能有一条，重复插入会报 IntegrityError
        #   等同于 SQL: UNIQUE KEY `year_month_unique` (`year`, `month`)
        unique_together = ['year', 'month']
        # 排序：新年月在前（如 2025-12, 2025-11, ..., 2024-1）
        ordering = ['-year', '-month']

    def __str__(self):
        """对象的字符串表示，如 "2025年6月统计" """
        return f"{self.year}年{self.month}月统计"

    @property
    def month_label(self) -> str:
        """
        计算属性（@property）：中文月份标签。
        不占数据库列，运行时动态计算。
        例如：self.month=6 → "6月"
        """
        return f"{self.month}月"

    @property
    def total_days(self) -> int:
        """
        计算属性（@property）：当月总天数。
        从 weather_distribution 中各天气的天数求和得出。
        例如：{"多云": 15, "小雨": 10, "阴天": 5} → 30 天
        注意：如果 weather_distribution 为空，返回 0。
        """
        if self.weather_distribution:
            return sum(self.weather_distribution.values())
        return 0


# ================================================================================
# 表 3：clothing_advice — 智能生活建议（AI 生成）
# ================================================================================
# 每月一条，由 AI 引擎（DeepSeek）或规则引擎根据天气数据生成。
# 包含 5 个维度：穿衣 / 出行 / 运动 / 健康 / 预警。
# ================================================================================

class ClothingAdvice(models.Model):
    """
    智能生活建议（每月一条，由 AI 或规则引擎生成）。

    数据流向：
      weather_data + forecast_data → ai_advisor.py → DeepSeek API → 存入此表。

    三个字段分别服务于不同的前端展示场景：
      - advice_text        → 概览页面，一次性展示所有建议
      - tags               → 标签云/快速浏览（如主页的标签泡泡）
      - advice_categories  → 分类卡片，5 个维度分开展示（穿衣页/出行页/运动页）
    """

    # =========================================================================
    # month：月份标识（唯一键）
    #   - CharField(max_length=7) → MySQL: VARCHAR(7)，如 '2025-06'
    #   - 为什么用 CharField 而不用 IntegerField？
    #     1. 格式 "YYYY-MM" 可以直接传给前端，无需拼接
    #     2. 字符串排序（'2025-01' < '2025-12'）天然正确
    #     3. unique=True 保证每月只存一份建议
    # =========================================================================
    month = models.CharField(
        max_length=7,
        verbose_name='月份',
        unique=True,
        help_text='格式：YYYY-MM，如 2025-06'
    )

    # =========================================================================
    # advice_text：综合建议文本
    #   - TextField → MySQL: TEXT 类型（长文本，无长度上限）
    #   - 与 CharField 的区别：TextField 不限制长度，适合存储 AI 生成的大段文字
    #   - 内容：将 5 个分类的建议拼接在一起，用于概览页一次性展示
    # =========================================================================
    advice_text = models.TextField(verbose_name='主要建议', blank=True)

    # =========================================================================
    # tags：推荐标签列表
    #   - JSONField(default=list) → MySQL: JSON 列，默认值为空数组 []
    #   - 存储 Python list，Django 自动序列化/反序列化 JSON
    #   - 示例值：["薄外套", "雨伞", "防晒霜", "运动鞋"]
    #   - 前端用法：标签云/标签泡泡，用户一眼看到要带什么
    # =========================================================================
    tags = models.JSONField(
        verbose_name='推荐标签',
        default=list,       # 默认空列表 []
        blank=True,
        help_text='示例：["薄外套", "雨具"]'
    )

    # =========================================================================
    # advice_categories：完整 5 维度建议（JSON 对象）
    #   - JSONField(default=dict) → MySQL: JSON 列，默认值为空对象 {}
    #   - 这是数据最"丰富"的字段，包含所有维度的详细建议
    #
    #   JSON 完整结构示例：
    #   {
    #     "clothing": {
    #       "advice": "气温 18~28°C，建议穿着薄外套或长袖T恤，早晚温差大需备开衫",
    #       "tags": ["薄外套", "长袖T恤", "开衫"]
    #     },
    #     "travel": {
    #       "advice": "未来两周降雨频繁，出行建议携带雨具，山区路段注意防滑",
    #       "tags": ["雨伞", "防水鞋"]
    #     },
    #     "exercise": {
    #       "advice": "温度适中，适合户外跑步、骑行。建议清晨或傍晚运动",
    #       "tags": ["跑步", "骑行", "登山"]
    #     },
    #     "health": {
    #       "advice": "昼夜温差约8°C，早晚偏凉，注意及时增减衣物，预防感冒",
    #       "tags": ["防感冒", "保暖"]
    #     },
    #     "alert": {
    #       "advice": "未来天气平稳，无极端天气预警",
    #       "tags": ["无预警"],
    #       "level": "normal"     ← level 字段：normal(正常) / caution(注意) / danger(危险)
    #     }
    #   }
    # =========================================================================
    advice_categories = models.JSONField(
        verbose_name='建议分类',
        default=dict,        # 默认空字典 {}
        blank=True,
        help_text='{"clothing": {...}, "travel": {...}, "exercise": {...}, "health": {...}, "alert": {...}}'
    )

    # ---- 时间戳 ----
    # auto_now_add=True：创建时间，只设一次
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # auto_now=True：更新时间，每次 save() 都刷新（用于追踪 AI 重新生成的时间）
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        # 自定义表名（否则默认是 'app_clothingadvice'）
        db_table = 'clothing_advice'
        verbose_name = '穿衣建议'
        verbose_name_plural = verbose_name
        # 按月份降序（最新月份在前，如 2025-06, 2025-05, ...）
        ordering = ['-month']

    def __str__(self):
        """对象的字符串表示，如 "2025-06 穿衣建议" """
        return f"{self.month} 穿衣建议"


# ================================================================================
# 表 4：crawl_task — 爬虫任务追踪
# ================================================================================
# 每次爬取都记录一条，用于追踪状态、记录结果、避免重复爬取。
#
# 状态机（ASCII 图）：
#   ┌─────────┐     ┌─────────┐     ┌─────────────────────────┐
#   │ pending  │ ──→ │ running │ ──→ │ success (records_count, │
#   │ (等待中)  │     │ (进行中) │     │          completed_at)  │
#   └─────────┘     └─────────┘     └─────────────────────────┘
#                                        │
#                                        └──→ ┌────────────────────────┐
#                                             │ failed (error_message, │
#                                             │         completed_at)  │
#                                             └────────────────────────┘
# ================================================================================

class CrawlTask(models.Model):
    """
    爬虫任务追踪表（记录每次爬取的状态和结果）。

    设计目的：
      1. 前端展示"上次爬取结果"（成功 X 条 / 失败原因）
      2. 避免重复爬取已成功的月份（查询该月是否有 success 记录）
      3. 失败记录帮助调试（看 error_message 定位爬虫问题）
    """

    # ---- 状态枚举：数据库存左边英文，Django Admin 显示右边中文 ----
    STATUS_CHOICES = [
        ('pending', '等待中'),   # 任务刚创建，还没开始执行
        ('running', '进行中'),   # 爬虫正在抓取数据
        ('success', '成功'),     # 爬取完成，数据已入库
        ('failed',  '失败'),     # 爬取过程中出错（网络/解析/数据异常）
    ]

    # =========================================================================
    # year + month：爬取目标年月（非唯一，同一个年月可以重试多次）
    #   例如：爬 2025 年 6 月 → year=2025, month=6
    # =========================================================================
    year = models.IntegerField(verbose_name='年份')     # MySQL: INT
    month = models.IntegerField(verbose_name='月份')    # MySQL: INT

    # =========================================================================
    # status：任务当前状态
    #   - default='pending' → 新记录默认是 'pending'（等待执行）
    #   - db_index=True    → 建索引，加速"筛选所有失败的月份"这类查询
    # =========================================================================
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='状态',
        db_index=True,  # 加速按状态筛选（如 WHERE status = 'failed'）
    )

    # =========================================================================
    # records_count：本次成功抓取的数据条数
    #   - 成功时 = 该月的天数（如 30 条）
    #   - 失败/等待时 = 0（由 default=0 控制）
    # =========================================================================
    records_count = models.IntegerField(verbose_name='抓取条数', default=0)

    # =========================================================================
    # error_message：失败原因
    #   - TextField → MySQL: TEXT 长文本（失败原因可能很长，如堆栈跟踪）
    #   - blank=True → 成功时此列为空字符串
    #   - 示例值："连接超时"、"页面解析失败：未找到目标表格"、"HTTP 403 Forbidden"
    # =========================================================================
    error_message = models.TextField(verbose_name='错误信息', blank=True)

    # =========================================================================
    # created_at：任务创建时间（auto_now_add=True，只设一次）
    # =========================================================================
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    # =========================================================================
    # completed_at：任务完成时间
    #   - null=True → 任务创建时此列为 NULL（还没完成）
    #   - 成功或失败时才手动填入当前时间
    #   - 与 auto_now 的区别：auto_now 每次 save 都更新；这里是手动控制何时填入
    # =========================================================================
    completed_at = models.DateTimeField(verbose_name='完成时间', null=True, blank=True)

    class Meta:
        db_table = 'crawl_task'
        verbose_name = '爬虫任务'
        verbose_name_plural = verbose_name
        # 按创建时间降序（最新的任务在前）
        ordering = ['-created_at']

    def __str__(self):
        """
        对象的字符串表示。
        例如：status='success' → "2025-6 (成功)"
              status='failed'  → "2025-6 (失败)"
        注意：self.get_status_display() 是 Django 自动生成的方法，
        当你定义了 choices 参数后，Django 会生成 get_<字段名>_display() 方法，
        返回 choices 中对应的中文标签（如 'success' → '成功'）。
        """
        return f"{self.year}-{self.month:02d} ({self.get_status_display()})"


# ================================================================================
# 表 5：forecast_data — 40 天天气预报
# ================================================================================
# 数据来源：2345 天气网 /wea_forty/60407.htm 页面内嵌 JSON。
# 每次爬取 40 条（约未来 5-6 周），以 date 为唯一键去重。
#
# 【与 WeatherData 的核心区别】
#   ┌──────────────┬─────────────────────┬─────────────────────┐
#   │              │  WeatherData        │  ForecastData        │
#   ├──────────────┼─────────────────────┼─────────────────────┤
#   │ 数据性质      │ 历史实测数据         │ 未来预测数据          │
#   │ 温度精度      │ Float（小数，如28.5）│ Integer（整数，如28） │
#   │ 温度维度      │ 最高温 / 最低温      │ 白天温度 / 夜间温度   │
#   │ 天气描述      │ 有                   │ 有                   │
#   │ 星期          │ 无                   │ 有（week 字段）       │
#   │ 数据来源      │ 2345 历史天气页面    │ 2345 40天预报页面     │
#   │ 更新方式      │ 逐月追加              │ 全部替换（40条）      │
#   └──────────────┴─────────────────────┴─────────────────────┘
# ================================================================================

class ForecastData(models.Model):
    """
    40 天天气预报数据（每次爬取全部替换，以 date 为唯一键去重）。

    温度用 IntegerField 的原因：
      天气预报只给整数（如 "白天28°C"），用 Integer 比 Float 更准确——
      避免存储假精度（28.0 暗示有小数位，但实际上预报就是整数）。
    """

    # =========================================================================
    # date：预报日期（唯一键）
    #   - 同一个日期只存一条预报，再次爬取时 update_or_create 自动覆盖
    # =========================================================================
    date = models.DateField(verbose_name='日期', unique=True)

    # =========================================================================
    # day_temp：白天气温（预报只给整数）
    #   - IntegerField → MySQL: INT NULL
    #   - 示例：28 表示白天 28°C
    # =========================================================================
    day_temp = models.IntegerField(verbose_name='白天气温(℃)', null=True, blank=True)

    # =========================================================================
    # night_temp：夜间气温（预报只给整数）
    #   - IntegerField → MySQL: INT NULL
    #   - 示例：18 表示夜间 18°C
    # =========================================================================
    night_temp = models.IntegerField(verbose_name='夜间气温(℃)', null=True, blank=True)

    # =========================================================================
    # weather_desc：天气预报描述
    #   - 与 WeatherData 同名字段，含义不同：那边是实测，这边是预测
    #   - 示例："多云"、"小雨"、"晴天"
    # =========================================================================
    weather_desc = models.CharField(max_length=50, verbose_name='天气状况', blank=True)

    # =========================================================================
    # week：星期几
    #   - 示例："周一"、"周二"..."周日"
    #   - 这是 ForecastData 独有的字段，WeatherData 没有（历史数据不需要星期）
    # =========================================================================
    week = models.CharField(max_length=10, verbose_name='星期', blank=True)

    # =========================================================================
    # created_at：记录入库时间（auto_now_add=True，创建时自动填入）
    # =========================================================================
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'forecast_data'
        verbose_name = '预报数据'
        verbose_name_plural = verbose_name
        # 按日期升序：最近的预报在后，方便取"未来 N 天"
        ordering = ['date']

    def __str__(self):
        """对象的字符串表示，如 "2025-06-20 预报 多云" """
        return f"{self.date} 预报 {self.weather_desc}"
