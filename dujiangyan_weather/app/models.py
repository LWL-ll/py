from django.db import models


class WeatherData(models.Model):
    """每日天气数据"""
    date = models.DateField(verbose_name='日期')
    max_temp = models.FloatField(verbose_name='最高温度(℃)', null=True, blank=True)
    min_temp = models.FloatField(verbose_name='最低温度(℃)', null=True, blank=True)
    weather_desc = models.CharField(max_length=50, verbose_name='天气状况', blank=True)
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


class MonthlyStats(models.Model):
    """月度统计数据"""
    year = models.IntegerField(verbose_name='年份')
    month = models.IntegerField(verbose_name='月份')
    avg_max_temp = models.FloatField(verbose_name='月均最高温', null=True, blank=True)
    avg_min_temp = models.FloatField(verbose_name='月均最低温', null=True, blank=True)
    max_temp_record = models.FloatField(verbose_name='月最高温记录', null=True, blank=True)
    min_temp_record = models.FloatField(verbose_name='月最低温记录', null=True, blank=True)
    rainy_days = models.IntegerField(verbose_name='降雨天数', default=0)
    avg_humidity = models.FloatField(verbose_name='平均湿度', null=True, blank=True)
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
