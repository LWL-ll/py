import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from app.models import WeatherData


class Command(BaseCommand):
    help = '生成近12个月的模拟天气数据（用于前端演示）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='生成多少天的数据（默认365天）'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='先清空现有数据再生成'
        )

    def handle(self, *args, **options):
        days = options['days']
        clear = options['clear']

        if clear:
            WeatherData.objects.all().delete()
            self.stdout.write(self.style.WARNING('已清空现有天气数据'))

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        weather_types = {
            1:  [('晴', 'sunny', 0.4), ('多云', 'cloudy', 0.3), ('阴', 'overcast', 0.2), ('小雨', 'rainy', 0.1)],
            2:  [('晴', 'sunny', 0.35), ('多云', 'cloudy', 0.3), ('阴', 'overcast', 0.2), ('小雨', 'rainy', 0.15)],
            3:  [('多云', 'cloudy', 0.35), ('晴', 'sunny', 0.25), ('阴', 'overcast', 0.2), ('小雨', 'rainy', 0.2)],
            4:  [('多云', 'cloudy', 0.3), ('晴', 'sunny', 0.25), ('小雨', 'rainy', 0.25), ('阴', 'overcast', 0.2)],
            5:  [('多云', 'cloudy', 0.3), ('晴', 'sunny', 0.25), ('小雨', 'rainy', 0.25), ('中雨', 'rainy', 0.15), ('阴', 'overcast', 0.05)],
            6:  [('多云', 'cloudy', 0.3), ('晴', 'sunny', 0.25), ('小雨', 'rainy', 0.25), ('中雨', 'rainy', 0.15), ('雷阵雨', 'rainy', 0.05)],
            7:  [('晴', 'sunny', 0.35), ('多云', 'cloudy', 0.3), ('小雨', 'rainy', 0.2), ('中雨', 'rainy', 0.1), ('雷阵雨', 'rainy', 0.05)],
            8:  [('晴', 'sunny', 0.4), ('多云', 'cloudy', 0.3), ('小雨', 'rainy', 0.15), ('中雨', 'rainy', 0.1), ('雷阵雨', 'rainy', 0.05)],
            9:  [('晴', 'sunny', 0.35), ('多云', 'cloudy', 0.3), ('小雨', 'rainy', 0.2), ('阴', 'overcast', 0.15)],
            10: [('晴', 'sunny', 0.4), ('多云', 'cloudy', 0.3), ('阴', 'overcast', 0.2), ('小雨', 'rainy', 0.1)],
            11: [('晴', 'sunny', 0.4), ('多云', 'cloudy', 0.25), ('阴', 'overcast', 0.25), ('小雨', 'rainy', 0.1)],
            12: [('晴', 'sunny', 0.45), ('多云', 'cloudy', 0.25), ('阴', 'overcast', 0.2), ('小雨', 'rainy', 0.1)],
        }

        wind_directions = ['北风', '东北风', '东风', '东南风', '南风', '西南风', '西风', '西北风']
        wind_levels = ['微风', '1级', '2级', '3级', '4级']

        created = 0
        current = start_date

        while current <= end_date:
            month = current.month
            templates = weather_types.get(month, weather_types[6])

            # 按概率选取天气描述
            total_prob = sum(t[2] for t in templates)
            r = random.uniform(0, total_prob)
            cumulative = 0
            weather_desc = templates[0][0]
            for desc, wtype, prob in templates:
                cumulative += prob
                if r <= cumulative:
                    weather_desc = desc
                    break

            # 季节性温度基准
            base_temps = {
                1: (8, 3), 2: (12, 5), 3: (18, 10), 4: (23, 14),
                5: (27, 19), 6: (30, 22), 7: (33, 24), 8: (32, 23),
                9: (27, 19), 10: (22, 14), 11: (16, 9), 12: (10, 4),
            }
            max_base, min_base = base_temps.get(month, (25, 15))

            # 添加随机波动
            max_temp = max_base + random.uniform(-3, 3)
            min_temp = min_base + random.uniform(-2, 2)

            # 确保最高温 > 最低温
            if min_temp >= max_temp:
                min_temp = max_temp - random.uniform(3, 8)

            # 湿度与天气相关
            if '雨' in weather_desc:
                humidity = random.uniform(70, 95)
            elif '晴' in weather_desc:
                humidity = random.uniform(40, 65)
            else:
                humidity = random.uniform(55, 80)

            wind_dir = random.choice(wind_directions)
            wind_lvl = random.choice(wind_levels)

            WeatherData.objects.update_or_create(
                date=current,
                defaults={
                    'max_temp': round(max_temp, 1),
                    'min_temp': round(min_temp, 1),
                    'weather_desc': weather_desc,
                    'wind_direction': wind_dir,
                    'wind_level': wind_lvl,
                    'humidity': round(humidity, 1),
                }
            )
            created += 1
            current += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f'成功生成 {created} 条模拟天气数据（{start_date} ~ {end_date}）'))
