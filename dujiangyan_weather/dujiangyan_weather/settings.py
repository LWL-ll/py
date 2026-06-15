"""
================================================================================
Django 项目配置文件（settings.py）
================================================================================
控制整个项目的运行参数：数据库连接、中间件链、静态文件、邮件、国际化等。

安全原则：
  - 所有敏感信息（密码/密钥/API Key）通过 .env 文件注入，不硬编码
  - .env 已加入 .gitignore，不会被提交到版本控制
  - DEBUG=True 仅用于开发环境，生产环境需改为 False
"""

import os
from pathlib import Path

# 项目根目录：dujiangyan_weather/dujiangyan_weather/
# BASE_DIR.parent 即 dujiangyan_weather/（manage.py 所在目录）
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== .env 文件加载 ====================
# 手动解析 .env 文件，不依赖 python-dotenv 第三方库。
# 解析逻辑：逐行读取 → 跳过空行/注释 → 按 = 拆分为 KEY=VALUE → 注入 os.environ。
# 这样后续 os.environ.get('KEY') 就能取到对应的值。
# 注意：不会覆盖已有的环境变量（setdefault），系统级变量优先。
ENV_FILE = BASE_DIR.parent / '.env'  # 项目根目录下的 .env
if ENV_FILE.exists():
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和 # 开头的注释行
            if not line or line.startswith('#'):
                continue
            # 解析 KEY=VALUE，partition 比 split 更安全（值里也可能有 =）
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")  # 去除引号（支持 "值" 或 '值'）
                os.environ.setdefault(key, value)


# ==================== Django 核心配置 ====================

# SECRET_KEY：Django 签名密钥（CSRF Token / Session 加密都依赖它）
# 开发环境用默认值，生产环境必须从 .env 读取
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-only-change-in-production')

# DEBUG：调试模式开关
# True  → 显示详细错误页面 + 自动重载代码（开发用）
# False → 隐藏错误详情，返回通用 500 页面（生产用）
DEBUG = True

# ALLOWED_HOSTS：允许访问的域名/IP 白名单
# '*' 表示允许所有（开发方便），生产环境应改为具体域名如 ['example.com']
ALLOWED_HOSTS = ['*']


# ==================== 应用注册 ====================
# Django 项目的"插件列表"，每新增一个 app 都要在这里注册
INSTALLED_APPS = [
    'django.contrib.admin',              # Django 自带后台管理
    'django.contrib.auth',               # 用户认证系统（User 模型）
    'django.contrib.contenttypes',       # 内容类型框架（admin 依赖）
    'django.contrib.sessions',           # Session 管理
    'django.contrib.messages',           # 消息框架（flash messages）
    'django.contrib.staticfiles',        # 静态文件管理
    'corsheaders',                       # 跨域请求支持（前后端分离必须）
    'lauth',                             # 自定义用户认证应用（登录/注册/找回密码）
    'app',                               # 核心业务应用（天气数据 + 爬虫 + 分析）
]

# ==================== 中间件链（请求 → 响应的处理管道）====================
# 中间件按顺序执行：请求从上往下，响应从下往上。
# 顺序很重要！例如 CsrfViewMiddleware 必须在 SessionMiddleware 之后。
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',          # 安全头（XSS/Content-Type 防护）
    'corsheaders.middleware.CorsMiddleware',                  # CORS 处理（必须在 CommonMiddleware 之前）
    'django.contrib.sessions.middleware.SessionMiddleware',   # Session 管理
    'django.middleware.common.CommonMiddleware',              # 通用中间件（URL 规范化等）
    'django.middleware.csrf.CsrfViewMiddleware',              # CSRF Token 验证（POST 请求必须带 Token）
    'django.contrib.auth.middleware.AuthenticationMiddleware',# 用户认证（request.user）
    'django.contrib.messages.middleware.MessageMiddleware',   # 消息框架
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # 防点击劫持（X-Frame-Options 头）
]

# 根 URL 路由配置文件
ROOT_URLCONF = 'dujiangyan_weather.urls'

# ==================== 模板引擎 ====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],            # 全局模板目录（空 = 只用各 app 的 templates/ 子目录）
        'APP_DIRS': True,      # 自动在每个已注册 app 下查找 templates/ 目录
        'OPTIONS': {
            'context_processors': [  # 模板全局变量处理器
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI 入口（生产部署用，如 gunicorn + wsgi.py）
WSGI_APPLICATION = 'dujiangyan_weather.wsgi.application'


# ==================== 数据库配置 ====================
# 使用 MySQL 8.0+，连接远端服务器 47.109.137.204。
#
# 连接参数说明：
#   ENGINE   — 数据库引擎（mysql / sqlite3 / postgresql）
#   NAME     — 数据库名（事先用 CREATE DATABASE 建好）
#   USER     — 数据库用户名
#   PASSWORD — 从 .env 文件读取（不硬编码）
#   HOST     — 远端服务器地址
#   PORT     — MySQL 默认端口 3306
#   OPTIONS  — charset: utf8mb4（支持 emoji 和中文生僻字）
#
# 安全提醒：PASSWORD 绝对不能硬编码在代码中，必须走环境变量。
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # MySQL 后端
        'NAME': '都江堰',                        # 数据库名称
        'USER': '都江堰',                        # 数据库用户
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),  # 从 .env 读取密码
        'HOST': '47.109.137.204',              # 远端 MySQL 服务器 IP
        'PORT': '3306',                         # MySQL 默认端口
        'OPTIONS': {
            'charset': 'utf8mb4',               # 字符集（完整 Unicode 支持）
        },
    }
}


# ==================== 密码验证规则 ====================
# Django 内置的密码强度校验器
AUTH_PASSWORD_VALIDATORS = [
    {
        # 禁止密码与用户名/邮箱等个人信息相似
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        # 密码最小长度（默认 8 位）
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        # 禁止使用常见弱密码（如 "12345678"、"password"）
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        # 禁止纯数字密码
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==================== 国际化 ====================
# 中文环境 + 上海时区（UTC+8）
LANGUAGE_CODE = 'zh-hans'      # 简体中文
TIME_ZONE = 'Asia/Shanghai'    # 东八区（都江堰所在时区）
USE_I18N = True                # 启用国际化翻译
USE_TZ = True                  # 启用时区感知（数据库存储 UTC，显示转本地）


# ==================== 静态文件 ====================
# STATIC_URL：浏览器访问静态文件的 URL 前缀
# STATICFILES_DIRS：开发时静态文件的实际存放目录
# STATIC_ROOT：生产环境 collectstatic 收集后的目标目录
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # dujiangyan_weather/static/（React 前端构建产物 + 源文件）
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # 运行 collectstatic 后的输出目录

# ==================== CORS 配置 ====================
# 开发环境允许所有来源访问（前后端分离时不同端口需要跨域）
# 生产环境应改为具体域名
CORS_ALLOW_ALL_ORIGINS = True     # 允许任意来源
CORS_ALLOW_CREDENTIALS = True     # 允许携带 Cookie（Session 认证需要）

# ==================== 主键默认类型 ====================
# BigAutoField = 64 位自增整数，比默认的 32 位 AutoField 容量更大
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== 认证配置 ====================
# LOGIN_URL：未登录用户被重定向的登录页面
# LOGIN_REDIRECT_URL：登录成功后的跳转地址
LOGIN_URL = '/lauth/login/'
LOGIN_REDIRECT_URL = '/'  # 根路径 → React SPA 仪表盘

# ==================== 邮件配置（QQ 邮箱 SMTP） ====================
# 用于发送注册/重置密码的验证码。
# 开发环境可用控制台后端打印验证码（替代真实发送）：
#   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# 生产环境使用 QQ 邮箱 SMTP：
#   1. 登录 QQ 邮箱 → 设置 → 账户 → 开启 SMTP 服务 → 获取授权码
#   2. 授权码填入 .env 的 EMAIL_HOST_PASSWORD
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 真实 SMTP 发送
EMAIL_HOST = 'smtp.qq.com'       # QQ 邮箱 SMTP 服务器
EMAIL_PORT = 587                 # TLS 加密端口
EMAIL_USE_TLS = True             # 启用 TLS 传输加密
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')        # 发件邮箱（从 .env 读取）
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '') # SMTP 授权码（从 .env 读取）
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER  # 发件人地址 = 登录邮箱
