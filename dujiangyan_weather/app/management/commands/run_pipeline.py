from django.core.management.base import BaseCommand
from app.data_cleaner import run_cleaning
from app.analyzer import analyze_all


class Command(BaseCommand):
    help = '一键运行数据清洗 + 分析全流程'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('开始数据清洗...'))
        run_cleaning()
        self.stdout.write(self.style.NOTICE('开始数据分析...'))
        analyze_all()
        self.stdout.write(self.style.SUCCESS('全流程执行完毕'))
