# 🌿 都江堰天气数据分析平台

基于 Django + React 的天气数据可视化分析系统，支持历史天气爬取、数据清洗、月度统计和智能穿衣建议。

---

## 技术栈

| 层次 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Django | 6.0.x |
| 数据库 | MySQL | 8.0+ |
| 前端框架 | React | 18.x |
| 构建工具 | Vite | 6.x |
| CSS 框架 | Tailwind CSS | 4.x |
| 图表库 | Recharts | 2.x |
| 爬虫 | requests + BeautifulSoup4 | - |
| 数据处理 | pandas + numpy | - |

---

## 快速启动

### 1. 环境准备

```bash
# Python 3.10+
# MySQL 8.0+
# Node.js 18+ (仅前端开发需要)
```

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

---

## 使用流程

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  一键爬取     │ ──→ │  开始分析     │ ──→ │  查看图表     │
│  (获取数据)   │     │  (生成统计)   │     │  (可视化)     │
└──────────────┘     └──────────────┘     └──────────────┘
```

1. 点击 **"一键爬取"** — 从 2345 天气网抓取近 12 个月数据
2. 点击 **"开始分析"** — 生成月度统计、气候评分、穿衣建议
3. 切换月份下拉框 — 所有图表联动刷新

### 管理命令

```bash
python manage.py run_pipeline         # 一键执行：清洗 + 分析
python manage.py generate_mock_data   # 生成模拟数据（无需爬虫）
```

---

## 目录结构

```
dujiangyan_weather/
├── manage.py                         # Django 入口
├── requirements.txt                  # Python 依赖
│
├── dujiangyan_weather/               # 项目配置
│   ├── settings.py                   # 数据库 / 中间件 / 静态文件
│   ├── urls.py                       # 根路由
│   └── wsgi.py                       # 生产部署入口
│
├── app/                              # 核心应用
│   ├── models.py                     # 数据模型 (4 张表)
│   ├── views.py                      # 视图函数 (11 个 API)
│   ├── urls.py                       # 路由配置
│   ├── admin.py                      # 后台管理
│   ├── crawler.py                    # 爬虫模块
│   ├── analyzer.py                   # 数据分析模块
│   ├── data_cleaner.py               # 数据清洗模块
│   ├── migrations/                   # 数据库迁移
│   └── management/commands/          # 管理命令
│
└── static/                           # 前端 (React)
    ├── index.html                    # 开发入口
    ├── package.json                  # npm 依赖
    ├── vite.config.ts                # Vite 配置
    ├── dist/                         # 生产构建产物
    └── src/
        ├── main.tsx                  # React 入口
        ├── app/
        │   ├── App.tsx               # 根组件
        │   ├── context/MonthContext.tsx  # 月份共享状态
        │   ├── utils/api.ts          # CSRF fetch 封装
        │   └── components/
        │       ├── Navbar.tsx        # 顶部控制栏
        │       ├── StatsGrid.tsx     # 统计卡片
        │       ├── PrimaryCharts.tsx # 温度趋势 + 天气分布
        │       ├── SecondaryCharts.tsx # 降雨统计 + 气候评分
        │       ├── HeatmapChart.tsx  # 温度热力图
        │       ├── InsightAndTable.tsx # 穿衣建议 + 数据表格
        │       ├── StatsCard.tsx     # 统计卡片组件
        │       └── Footer.tsx        # 页脚
        └── styles/
            ├── index.css             # 样式入口
            └── tailwind.css          # Tailwind 配置
```

---

## API 接口文档

### 数据获取

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/api/weather/list/` | `year`, `month`, `page`, `page_size` | 天气数据列表（分页） |
| GET | `/api/weather/summary/` | - | 数据概览（总天数、平均温、晴雨概率） |
| GET | `/api/weather/monthly/` | `year`, `month` | 月度统计数据 |
| GET | `/api/weather/months/` | - | 可用月份列表 |

### 图表数据

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/api/weather/distribution/` | `year`, `month` | 天气状况分布（饼图） |
| GET | `/api/weather/climate-score/` | `year`, `month` | 气候综合评分（雷达图） |
| GET | `/api/weather/heatmap/` | `year` | 温度热力分布（热力图） |
| GET | `/api/weather/advice/` | `month` | 智能穿衣建议 |

### 操作

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/weather/crawl/` | 触发爬虫抓取近 12 个月数据 |
| POST | `/api/weather/analyze/` | 生成月度统计 + 气候评分 + 穿衣建议 |

---

## 数据模型

### WeatherData（每日天气）

| 字段 | 类型 | 说明 |
|------|------|------|
| date | DateField | 日期（唯一索引） |
| max_temp | FloatField | 最高温度(℃) |
| min_temp | FloatField | 最低温度(℃) |
| weather_desc | CharField | 天气描述（如"阴~多云"） |
| weather_type | CharField | 天气类型（sunny/cloudy/rainy/...） |
| wind_direction | CharField | 风向 |
| wind_level | CharField | 风力等级 |
| humidity | FloatField | 湿度(%) |

### MonthlyStats（月度统计）

| 字段 | 类型 | 说明 |
|------|------|------|
| year / month | IntegerField | 年月（联合唯一） |
| avg_max_temp / avg_min_temp | FloatField | 月均最高/最低温 |
| max_temp_record / min_temp_record | FloatField | 月极值温度 |
| rainy_days | IntegerField | 降雨天数 |
| avg_humidity | FloatField | 平均湿度 |
| weather_distribution | JSONField | 天气分布 `{"晴":15, "雨":8}` |
| temp_comfort_score 等 | IntegerField | 5 项气候评分(0-100) |

### ClothingAdvice（穿衣建议）

| 字段 | 类型 | 说明 |
|------|------|------|
| month | CharField | 月份 `YYYY-MM`（唯一） |
| advice_text | TextField | 建议文本 |
| tags | JSONField | 推荐标签 `["薄外套","雨具"]` |

### CrawlTask（爬虫任务）

| 字段 | 类型 | 说明 |
|------|------|------|
| year / month | IntegerField | 爬取目标年月 |
| status | CharField | pending / running / success / failed |
| records_count | IntegerField | 抓取条数 |
| error_message | TextField | 错误信息 |

---

## 前端架构

### 组件树

```
App (MonthProvider)
├── Navbar           ← 月份选择 + 爬取/分析按钮
├── StatsGrid        ← 4 个统计卡片（懒加载）
│   └── StatsCard ×4
├── PrimaryCharts    ← 温度折线 + 天气饼图（懒加载）
├── SecondaryCharts  ← 降雨柱图 + 气候雷达（懒加载）
├── HeatmapChart     ← 年度温度热力图（懒加载）
├── InsightAndTable  ← 穿衣建议 + 数据表格（懒加载）
└── Footer
```

### 数据流

```
MonthContext (共享月份状态)
    │
    ├── selectedMonth: "2025-06"
    ├── refreshKey: 0 (爬取/分析后 +1 触发重载)
    │
    └── 每个组件: useMonth() → useEffect → fetch API → setState → 渲染图表
```

### 性能优化

- 4 个图表组件使用 `React.lazy` + `Suspense` 懒加载
- 首屏 JS 158 KB，Recharts 共享库 399 KB 按需加载
- 月份切换自动请求对应数据，无全局刷新

---

## 设计说明

### 气候评分算法

5 项评分均归一化到 0-100：

| 评分 | 计算方法 |
|------|---------|
| 温度舒适度 | 最高温 18-30°C 且最低温 10-25°C 的天数占比 |
| 湿度适宜度 | 偏离理想值 50% 越远分数越低 |
| 日照充足度 | 晴天 + 多云天数占比 |
| 空气质量 | 晴天比例(60%) + 降雨适中度(40%) |
| 降水适中度 | 偏离最佳值 6 天/月 越远分数越低 |

### 爬虫反爬策略

- 完整浏览器请求头（User-Agent / Referer / X-Requested-With）
- 每月请求间隔 2 秒
- 失败自动重试 1 次
- 逐月追踪 CrawlTask 状态

---

## 安全

- [x] 密码通过 `.env` 环境变量管理，不提交 git
- [x] CSRF Token 保护所有 POST 接口
- [x] `.gitignore` 排除敏感文件和构建产物
- [x] `DEBUG = True` 仅开发环境

---

## 前端开发

如需修改前端代码：

```bash
cd dujiangyan_weather/static
npm install          # 首次
npm run dev          # 启动 Vite 开发服务器
```

修改完成后：

```bash
npm run build        # 构建生产版本
```

Django 自动从 `static/dist/` 返回最新构建产物。
