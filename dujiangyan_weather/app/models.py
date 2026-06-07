from django.db import models


class WeatherData(models.Model):
    """每日天气数据"""

    WEATHER_TYPE_CHOICES = [
        ('sunny', '晴天'),
        ('cloudy', '多云'),
        ('overcast', '阴天'),
        ('rainy', '雨天'),
        ('snowy', '雪天'),
        ('foggy', '雾/霾'),
    ]

    date = models.DateField(verbose_name='日期', unique=True)
    max_temp = models.FloatField(verbose_name='最高温度(℃)', null=True, blank=True)
    min_temp = models.FloatField(verbose_name='最低温度(℃)', null=True, blank=True)
    weather_desc = models.CharField(max_length=50, verbose_name='天气状况', blank=True)
    weather_type = models.CharField(
        max_length=20,
        choices=WEATHER_TYPE_CHOICES,
        verbose_name='天气类型',
        blank=True,
        db_index=True,
    )
    wind_direction = models.CharField(max_length=50, verbose_name='风向', blank=True)
    wind_level = models.CharField(max_length=20, verbose_name='风力', blank=True)
    humidity = models.FloatField(verbose_name='湿度(%)', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'weather_data'
        verbose_name = '天气数据'
        verbose_name_plural = verbose_name
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} {self.weather_desc}"

    def save(self, *args, **kwargs):
        """保存前自动映射 weather_type"""
        self.weather_type = self.infer_weather_type(self.weather_desc)
        super().save(*args, **kwargs)

    @staticmethod
    def infer_weather_type(desc: str) -> str:
        """根据天气描述推断天气类型"""
        if not desc:
            return ''
        desc = str(desc)
        if '雪' in desc:
            return 'snowy'
        if '雨' in desc:
            return 'rainy'
        if '雾' in desc or '霾' in desc:
            return 'foggy'
        if '多云' in desc:
            return 'cloudy'
        if '阴' in desc:
            return 'overcast'
        if '晴' in desc:
            return 'sunny'
        return ''


class MonthlyStats(models.Model):
    """月度统计数据"""

    year = models.IntegerField(verbose_name='年份')
    month = models.IntegerField(verbose_name='月份')

    # 温度统计
    avg_max_temp = models.FloatField(verbose_name='月均最高温', null=True, blank=True)
    avg_min_temp = models.FloatField(verbose_name='月均最低温', null=True, blank=True)
    max_temp_record = models.FloatField(verbose_name='月最高温记录', null=True, blank=True)
    min_temp_record = models.FloatField(verbose_name='月最低温记录', null=True, blank=True)

    # 降水与湿度
    rainy_days = models.IntegerField(verbose_name='降雨天数', default=0)
    avg_humidity = models.FloatField(verbose_name='平均湿度', null=True, blank=True)

    # 天气分布（JSON：{"晴天": 15, "多云": 8, "雨天": 5, "阴天": 2}）
    weather_distribution = models.JSONField(
        verbose_name='天气分布',
        default=dict,
        blank=True,
    )

    # 气候综合评分（0-100，雷达图用）
    temp_comfort_score = models.IntegerField(
        verbose_name='温度舒适度',
        null=True, blank=True,
        help_text='0-100，越高越舒适'
    )
    humidity_comfort_score = models.IntegerField(
        verbose_name='湿度适宜度',
        null=True, blank=True,
        help_text='0-100，越高越适宜'
    )
    sunlight_score = models.IntegerField(
        verbose_name='日照充足度',
        null=True, blank=True,
        help_text='0-100，越高越充足'
    )
    air_quality_score = models.IntegerField(
        verbose_name='空气质量',
        null=True, blank=True,
        help_text='0-100，越高越好'
    )
    precipitation_score = models.IntegerField(
        verbose_name='降水适中度',
        null=True, blank=True,
        help_text='0-100，越适中越高'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'monthly_stats'
        verbose_name = '月度统计'
        verbose_name_plural = verbose_name
        unique_together = ['year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.year}年{self.month}月统计"

    @property
    def month_label(self) -> str:
        return f"{self.month}月"

    @property
    def total_days(self) -> int:
        """当月总天数（从天气分布推算，若未计算则返回0）"""
        if self.weather_distribution:
            return sum(self.weather_distribution.values())
        return 0


class ClothingAdvice(models.Model):
    """智能穿衣建议"""

    month = models.CharField(
        max_length=7,
        verbose_name='月份',
        unique=True,
        help_text='格式：YYYY-MM'
    )
    advice_text = models.TextField(verbose_name='建议文本', blank=True)
    tags = models.JSONField(
        verbose_name='推荐标签',
        default=list,
        blank=True,
        help_text='示例：["薄外套", "雨具"]'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'clothing_advice'
        verbose_name = '穿衣建议'
        verbose_name_plural = verbose_name
        ordering = ['-month']

    def __str__(self):
        return f"{self.month} 穿衣建议"


class CrawlTask(models.Model):
    """爬虫任务记录"""

    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '进行中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]

    year = models.IntegerField(verbose_name='年份')
    month = models.IntegerField(verbose_name='月份')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='状态',
        db_index=True,
    )
    records_count = models.IntegerField(verbose_name='抓取条数', default=0)
    error_message = models.TextField(verbose_name='错误信息', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    completed_at = models.DateTimeField(verbose_name='完成时间', null=True, blank=True)

    class Meta:
        db_table = 'crawl_task'
        verbose_name = '爬虫任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.year}-{self.month:02d} ({self.get_status_display()})"
