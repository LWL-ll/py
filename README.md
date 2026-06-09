# 🌿 都江堰天气数据分析平台

基于 Django + React 的天气数据可视化分析系统，支持历史天气爬取、40 天预报、数据分析与多维智能生活建议。需登录后使用。

---

## 技术栈

| 层次 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Django | 6.0+ |
| 数据库 | MySQL | 8.0+ |
| 前端框架 | React | 18.x |
| 构建工具 | Vite | 6.x |
| CSS 框架 | Tailwind CSS | 4.x |
| 图表库 | Recharts | 2.x |
| 图标库 | Lucide React | 0.487+ |
| 爬虫 | requests + BeautifulSoup4 | - |
| 数据处理 | pandas + numpy | - |
| 用户认证 | Django 自定义 lauth | - |

---

## 快速启动

### 1. 环境准备

- Python 3.10+
- MySQL 8.0+
- Node.js 18+（仅前端开发）

### 2. 安装依赖

```bash
cd dujiangyan_weather
pip install -r requirements.txt
```

### 3. 配置数据库

编辑项目根目录 `.env` 文件（已创建，按需修改）：

```env
DB_PASSWORD=你的MySQL密码
DJANGO_SECRET_KEY=你的密钥
```

创建数据库：

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS dujiangyan_weather CHARACTER SET utf8mb4;"
```

### 4. 初始化

```bash
python manage.py migrate          # 建表
python manage.py runserver        # 启动
```

### 5. 访问

浏览器打开 **http://localhost:8000**

> 首次访问会自动跳转到登录/注册页面。注册需要邮箱验证码（开发环境验证码打印在终端）。

---

## 使用流程

```
注册/登录 → 一键爬取 → 开始分析 → 查看图表 + 智能建议
                │
            └── 40天预报（可选）
```

### 管理命令

```bash
python manage.py run_pipeline         # 一键执行：清洗 + 分析
python manage.py generate_mock_data   # 生成模拟数据（无需爬虫）
```

### 前端开发

```bash
cd dujiangyan_weather/static
npm install          # 首次
npm run dev          # Vite 开发服务器
npm run build        # 生产构建
```

---

## 目录结构

```
dujiangyan_weather/
├── manage.py                         # Django 入口
├── requirements.txt                  # Python 依赖（7 个包）
│
├── dujiangyan_weather/               # 项目配置
│   ├── settings.py                   # 数据库 / 中间件 / 静态文件 / 邮件
│   ├── urls.py                       # 根路由（admin + lauth + app）
│   └── wsgi.py                       # 生产部署入口
│
├── app/                              # 核心业务应用
│   ├── models.py                     # 6 张表: WeatherData / MonthlyStats
│   │                                 #   ClothingAdvice / CrawlTask / ForecastData
│   ├── views.py                      # 17 个 API + SPA 首页
│   ├── urls.py                       # 路由: /api/weather/*
│   ├── admin.py                      # Django 后台管理（6 个 ModelAdmin）
│   ├── crawler.py                    # 2345 天气网爬虫（历史 + 40 天预报）
│   ├── analyzer.py                   # 数据分析 + 5 维度智能建议引擎
│   ├── data_cleaner.py               # 数据清洗（缺失值/异常值/去重）
│   ├── migrations/                   # 数据库迁移文件
│   └── management/commands/
│       ├── run_pipeline.py           # 一键清洗 + 分析
│       └── generate_mock_data.py     # 生成模拟天气数据
│
├── lauth/                            # 用户认证应用
│   ├── models.py                     # VerificationCode（邮箱验证码）
│   ├── views.py                      # 10 个 API（登录/注册/找回密码）
│   ├── urls.py                       # 认证路由 /lauth/*
│   ├── decorators.py                 # @login_required（AJAX 友好）
│   ├── admin.py                      # 验证码后台管理
│   ├── templates/                    # Django 模板（角色动画登录页）
│   │   ├── login.html                #   登录（4 角色眼珠跟踪动画）
│   │   ├── register.html             #   注册（含验证码倒计时）
│   │   └── forgot_password.html      #   忘记密码（两步流程）
│   └── static/
│       ├── css/auth.css              #   认证页面样式（与仪表板统一配色）
│       └── js/auth-common.js         #   角色动画引擎
│
└── static/                           # 前端 React SPA
    ├── index.html                    # Vite 开发入口
    ├── package.json                  # npm 依赖（8 个包）
    ├── vite.config.ts                # Vite 配置
    ├── dist/                         # 生产构建产物（Django 直接返回）
    └── src/
        ├── main.tsx                  # React 挂载点
        ├── app/
        │   ├── App.tsx               # 根组件（AuthProvider + MonthProvider）
        │   ├── context/
        │   │   ├── AuthContext.tsx    # 用户认证状态
        │   │   └── MonthContext.tsx   # 月份共享状态
        │   ├── utils/
        │   │   └── api.ts            # CSRF 安全的 fetch 封装
        │   └── components/
        │       ├── Navbar.tsx         # 顶部栏（月份选择 + 操作按钮 + 用户区）
        │       ├── StatsGrid.tsx      # 4 个统计卡片
        │       │   └── StatsCard.tsx  # 卡片 UI（响应式 + 悬停动画）
        │       ├── ForecastRow.tsx    # 8 天预报横向滚动卡片
        │       ├── PrimaryCharts.tsx  # 温度趋势（历史+预报） + 天气分布饼图
        │       ├── SecondaryCharts.tsx# 月度降雨柱图 + 气候评分雷达图
        │       ├── HeatmapChart.tsx   # 年度温度热力图
        │       ├── InsightAndTable.tsx# 5 标签智能建议 + 天气数据表格
        │       └── Footer.tsx         # 页脚
        └── styles/
            ├── index.css             # 样式入口
            └── tailwind.css          # Tailwind v4 + 自定义动画
```

---

## API 接口文档

### 天气数据

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/api/weather/list/` | `year`, `month`, `page`, `page_size` | 天气数据列表（分页） |
| GET | `/api/weather/summary/` | - | 数据概览（总天数、均温、晴雨概率） |
| GET | `/api/weather/monthly/` | `year`, `month` | 月度统计数据 |
| GET | `/api/weather/months/` | - | 可用月份列表 |

### 图表数据

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/api/weather/distribution/` | `year`, `month` | 天气分布（饼图） |
| GET | `/api/weather/climate-score/` | `year`, `month` | 气候评分（雷达图） |
| GET | `/api/weather/heatmap/` | `year` | 温度热力图 |
| GET | `/api/weather/advice/` | `month` | 多维智能建议（5 分类） |
| GET | `/api/weather/temperature-trend/` | - | 历史月均 + 未来 7 天预报 |
| GET | `/api/weather/forecast/` | - | 40 天预报列表 |

### 操作

| 方法 | 路径 | 说明 | 需登录 |
|------|------|------|--------|
| POST | `/api/weather/crawl/` | 爬取近 12 个月历史数据 | ✅ |
| POST | `/api/weather/analyze/` | 生成月度统计 + 气候评分 + 建议 | ✅ |
| POST | `/api/weather/forecast/fetch/` | 爬取 40 天预报数据 | ✅ |

### 用户认证

| 方法 | 路径 | 请求体 | 说明 |
|------|------|--------|------|
| GET | `/lauth/login/` | - | 登录页面（角色动画） |
| GET | `/lauth/register/` | - | 注册页面 |
| POST | `/lauth/send-code/` | `{email}` | 发送注册验证码 |
| POST | `/lauth/verify-code/` | `{email, code}` | 验证验证码 |
| POST | `/lauth/register-user/` | `{username, email, password, verification_code}` | 注册（自动登录，5 天会话） |
| POST | `/lauth/user-login/` | `{email, password}` | 登录 |
| POST | `/lauth/user-logout/` | - | 退出 |
| POST | `/lauth/send-reset-code/` | `{email}` | 发送密码重置验证码 |
| POST | `/lauth/reset-password/` | `{email, code, new_password}` | 重置密码 |
| GET | `/lauth/check-login/` | - | 检查登录状态 |

---

## 数据模型

### WeatherData — 每日天气

| 字段 | 类型 | 说明 |
|------|------|------|
| date | DateField | 日期（唯一） |
| max_temp / min_temp | FloatField | 最高/最低温(℃) |
| weather_desc | CharField | 天气描述 |
| weather_type | CharField | 类型（sunny/cloudy/rainy/snowy/foggy/overcast） |
| wind_direction / wind_level | CharField | 风向 / 风力 |
| humidity | FloatField | 湿度(%) |

### ForecastData — 40 天预报

| 字段 | 类型 | 说明 |
|------|------|------|
| date | DateField | 日期（唯一） |
| day_temp / night_temp | IntegerField | 白天气温 / 夜间气温(℃) |
| weather_desc | CharField | 天气状况 |
| week | CharField | 星期 |

### MonthlyStats — 月度统计

| 字段 | 类型 | 说明 |
|------|------|------|
| year / month | IntegerField | 年月（联合唯一） |
| avg_max_temp / avg_min_temp | FloatField | 月均温度 |
| max_temp_record / min_temp_record | FloatField | 月极值 |
| rainy_days | IntegerField | 降雨天数 |
| avg_humidity | FloatField | 平均湿度 |
| weather_distribution | JSONField | 天气分布 |
| temp_comfort_score 等 ×5 | IntegerField | 气候评分(0-100) |

### ClothingAdvice — 多维建议

| 字段 | 类型 | 说明 |
|------|------|------|
| month | CharField | 月份 YYYY-MM（唯一） |
| advice_text | TextField | 综合建议 |
| tags | JSONField | 标签列表 |
| advice_categories | JSONField | 5 分类建议（clothing/travel/exercise/health/alert） |

### VerificationCode — 邮箱验证码

| 字段 | 类型 | 说明 |
|------|------|------|
| email | EmailField | 邮箱 |
| code | CharField(6) | 验证码 |
| is_used | BooleanField | 是否已使用 |
| created_at | DateTimeField | 创建时间（有效期 5 分钟） |

---

## 前端架构

### 组件树

```
App (AuthProvider → MonthProvider)
├── [未登录] → 重定向 /lauth/login/（角色动画登录页）
├── [已登录] Dashboard
│   ├── Navbar           ← 月份选择 + 一键爬取/分析/预报 + 用户区
│   ├── StatsGrid        ← 4 统计卡片
│   ├── ForecastRow      ← 8 天预报滚动卡片
│   ├── PrimaryCharts    ← 温度趋势（历史实线+预报虚线）+ 饼图（懒加载）
│   ├── SecondaryCharts  ← 降雨柱图 + 气候雷达（懒加载）
│   ├── HeatmapChart     ← 温度热力图（懒加载）
│   ├── InsightAndTable  ← 5 标签建议 + 数据表格（懒加载）
│   └── Footer
```

### 数据流

```
MonthContext
  ├── selectedMonth: "2025-06"
  ├── availableMonths: [{label, value, year, month}]
  └── refreshKey: 爬取/分析后 +1 → 所有图表重载

每个组件: useMonth() → useEffect → fetch API → setState → 渲染
```

### 性能优化

- 4 个图表组件 React.lazy + Suspense 懒加载
- 首屏 JS 163 KB，Recharts 共享库 399 KB 按需加载
- 月份切换仅请求对应数据，无全局刷新
- 移动端响应式：自适应字号、间距、最小宽度

---

## 智能建议引擎

基于近 60 天历史数据 + 未来 14 天预报生成 5 类建议：

| 分类 | 分析维度 | 示例 |
|------|---------|------|
| 🧥 穿衣 | 温度区间 + 温差 + 湿度 | "气温偏热，建议短袖" |
| 🌂 出行 | 降雨概率 + 极端天气 | "未来两周降雨频繁，携带雨具" |
| 🏃 运动 | 温度舒适度 + 降雨 | "降雨较多，选择室内运动" |
| 🌿 健康 | 湿度 + 温差 + 关节 | "昼夜温差大，注意防感冒" |
| ⚠️ 预警 | 极端温度 + 暴雨 | normal / warning / danger 三级 |

---

## 气候评分算法

5 项评分统一归一化到 0-100：

| 评分 | 计算逻辑 |
|------|---------|
| 温度舒适度 | 最高温 18-30°C 且最低温 10-25°C 天数占比 |
| 湿度适宜度 | 偏离 50% 理想值越远分数越低 |
| 日照充足度 | 晴天 + 多云天数占比 |
| 空气质量 | 晴天比例(60%) + 降雨适中度(40%) |
| 降水适中度 | 月降雨距最佳值 6 天的偏离程度 |

---

## 爬虫

### 历史数据

- 数据源：2345 天气网 `Pc/GetHistory` API
- 城市编码：60407（都江堰）
- 反爬：完整浏览器头 + Referer + 2 秒间隔 + 失败重试
- 字段：日期 / 最高温 / 最低温 / 天气 / 风向风力 / 湿度

### 40 天预报

- 数据源：`/wea_forty/60407.htm` 页面内嵌 JSON
- 提取 `"data":[...]` 中的 40 条预报
- 字段：日期 / 白天气温 / 夜间气温 / 天气 / 星期

---

## 邮件配置

开发环境使用控制台后端（验证码打印到终端）：

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

生产环境切换 SMTP（`settings.py` 中取消注释）：

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@qq.com'
EMAIL_HOST_PASSWORD = 'your-smtp-password'
```

---

## 安全措施

- [x] 密码通过 `.env` 管理，不提交 git
- [x] CSRF Token 保护所有 POST 接口（`apiFetch` 自动携带）
- [x] `@login_required` 保护所有关键视图
- [x] `.gitignore` 排除 node_modules / \_\_pycache\_\_ / .env / db.sqlite3
- [x] 登录失败不区分"邮箱不存在"和"密码错误"（防枚举）
- [x] 验证码 5 分钟过期 + 一次性使用
