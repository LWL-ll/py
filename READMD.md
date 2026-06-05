dujiangyan_weather/
├── manage.py              ✅ Django 管理入口
├── dujiangyan_weather/
│   ├── __init__.py        ✅
│   ├── settings.py        ✅ MySQL 配置 + 静态文件 + 中文时区
│   ├── urls.py            ✅ 总路由（含 app 路由包含）
│   └── wsgi.py            ✅
├── app/
│   ├── __init__.py        ✅
│   ├── models.py          ✅ WeatherData / MonthlyStats ORM
│   ├── views.py           ✅ 页面视图 + 3 个 API 接口
│   ├── urls.py            ✅ 应用路由配置
│   ├── crawler.py         ✅ 2345天气网爬虫（可按年月范围抓取）
│   ├── data_cleaner.py    ✅ pandas 清洗：异常值处理、插值、补全
│   ├── analyzer.py        ✅ 月度统计生成 / 年度概览 / 极端天气
│   └── templates/
│       └── index.html     ✅ Bootstrap 5 + Chart.js 可视化大屏
├── static/
│   ├── css/               ✅ 空目录（可放自定义样式）
│   └── js/                ✅ 空目录（可放自定义脚本）
└── requirements.txt       ✅ Django + pandas + requests + bs4 + pymysql