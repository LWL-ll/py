"""
WSGI config for dujiangyan_weather project.

WSGI（Web Server Gateway Interface）配置文件
用于将 Django 应用部署到生产服务器（如 uWSGI、Gunicorn）。

用法：
    gunicorn dujiangyan_weather.wsgi:application
"""

import os

from django.core.wsgi import get_wsgi_application

# 默认使用项目 settings，可通过环境变量覆盖
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dujiangyan_weather.settings')

# WSGI 应用入口，由 Web 服务器调用
application = get_wsgi_application()
