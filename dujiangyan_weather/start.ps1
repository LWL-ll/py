Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   启动成功！" -ForegroundColor Green
Write-Host "   主页:  http://127.0.0.1:8000/" -ForegroundColor Yellow
Write-Host "   后台:  http://127.0.0.1:8000/admin/" -ForegroundColor Yellow
Write-Host "   登录:  http://127.0.0.1:8000/lauth/login/" -ForegroundColor Yellow
Write-Host "   按 Ctrl+C 停止服务器" -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:8000/"

Set-Location $ProjectDir
python manage.py runserver 0.0.0.0:8000$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   都江堰天气数据分析平台 - 一键启动" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvFile = Join-Path (Split-Path -Parent $ProjectDir) ".env"
$StaticDir = Join-Path $ProjectDir "static"
$Requirements = Join-Path $ProjectDir "requirements.txt"

# ---- 检查 .env ----
if (-not (Test-Path $EnvFile)) {
    Write-Host "[错误] 未找到 .env 文件: $EnvFile" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}
Write-Host "[OK] .env 已找到" -ForegroundColor Green

# ---- 检查 Python ----
try {
    $pyVer = python --version 2>&1
    Write-Host "[OK] $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# ---- 检查 Node.js ----
try {
    $nodeVer = node --version 2>&1
    Write-Host "[OK] Node.js $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未找到 Node.js，请先安装 Node.js 18+" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# ============================================
# [1/5] 安装 Python 依赖
# ============================================
Write-Host ""
Write-Host "[1/5] 安装 Python 依赖..." -ForegroundColor Yellow
pip install -r $Requirements -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] pip install 失败" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}
Write-Host "[OK] Python 依赖已安装" -ForegroundColor Green

# ============================================
# [2/5] 构建前端
# ============================================
Write-Host ""
Write-Host "[2/5] 构建前端..." -ForegroundColor Yellow
Push-Location $StaticDir
if (-not (Test-Path (Join-Path $StaticDir "node_modules"))) {
    Write-Host "首次运行，安装前端依赖..." -ForegroundColor Gray
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] npm install 失败" -ForegroundColor Red
        Pop-Location
        Read-Host "按回车退出"
        exit 1
    }
}
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] npm run build 失败" -ForegroundColor Red
    Pop-Location
    Read-Host "按回车退出"
    exit 1
}
Pop-Location
Write-Host "[OK] 前端构建完成 -> static/dist/" -ForegroundColor Green

# ============================================
# [3/5] 数据库迁移
# ============================================
Write-Host ""
Write-Host "[3/5] 执行数据库迁移..." -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 数据库迁移失败，请检查 MySQL 连接" -ForegroundColor Red
    Write-Host "  数据库: 47.109.137.204:3306" -ForegroundColor Gray
    Write-Host "  用户名: 都江堰" -ForegroundColor Gray
    Write-Host "  密码:   来自 .env 的 DB_PASSWORD" -ForegroundColor Gray
    Read-Host "按回车退出"
    exit 1
}
Write-Host "[OK] 数据库迁移完成" -ForegroundColor Green

# ============================================
# [4/5] 检查数据 & 生成模拟数据
# ============================================
Write-Host ""
Write-Host "[4/5] 检查天气数据..." -ForegroundColor Yellow
$hasData = python -c @"
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dujiangyan_weather.settings')
django.setup()
from app.models import WeatherData
exit(0 if WeatherData.objects.exists() else 1)
"@
if ($LASTEXITCODE -ne 0) {
    $answer = Read-Host "数据库中暂无天气数据，是否生成模拟数据？ [Y/N]"
    if ($answer -eq "Y" -or $answer -eq "y") {
        Write-Host "生成 365 天模拟天气数据..." -ForegroundColor Gray
        python manage.py generate_mock_data --days 365
        Write-Host "运行数据清洗与分析..." -ForegroundColor Gray
        python manage.py run_pipeline
    } else {
        Write-Host "已跳过，可稍后手动运行:" -ForegroundColor Gray
        Write-Host "  python manage.py generate_mock_data --days 365" -ForegroundColor Gray
        Write-Host "  python manage.py run_pipeline" -ForegroundColor Gray
    }
} else {
    Write-Host "[OK] 数据库已有天气数据" -ForegroundColor Green
}

# ============================================
# [5/5] 检查管理员账户
# ============================================
Write-Host ""
Write-Host "[5/5] 检查管理员账户..." -ForegroundColor Yellow
$hasSu = python -c @"
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dujiangyan_weather.settings')
django.setup()
from django.contrib.auth.models import User
exit(0 if User.objects.filter(is_superuser=True).exists() else 1)
"@
if ($LASTEXITCODE -ne 0) {
    $answer = Read-Host "未检测到管理员账户，是否创建？ [Y/N]"
    if ($answer -eq "Y" -or $answer -eq "y") {
        $suUser = Read-Host "请输入用户名 [默认: admin]"
        if ([string]::IsNullOrWhiteSpace($suUser)) { $suUser = "admin" }
        $suEmail = Read-Host "请输入邮箱"
        $suPass = Read-Host "请输入密码" -AsSecureString
        $suPassPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($suPass)
        )
        python -c @"
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dujiangyan_weather.settings')
django.setup()
from django.contrib.auth.models import User
User.objects.create_superuser('$suUser', '$suEmail', '$suPassPlain')
print('[OK] 管理员创建成功')
"@
    }
} else {
    Write-Host "[OK] 管理员账户已存在" -ForegroundColor Green
}

# ============================================
# 启动！
# ============================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   启动成功！" -ForegroundColor Green
Write-Host "   主页:  http://127.0.0.1:8000/" -ForegroundColor White
Write-Host "   后台:  http://127.0.0.1:8000/admin/" -ForegroundColor White
Write-Host "   登录:  http://127.0.0.1:8000/lauth/login/" -ForegroundColor White
Write-Host "   按 Ctrl+C 停止服务器" -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectDir
python manage.py runserver 0.0.0.0:8000