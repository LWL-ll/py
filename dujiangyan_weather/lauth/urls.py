from django.urls import path
from . import views

# 应用命名空间，用于在模板和视图中反向解析 URL
# 例如：{% url 'lauth:login' %} 或 reverse('lauth:login')
app_name = 'lauth'

urlpatterns = [
    # ===== 页面路由 =====
    
    # 登录页面：显示用户登录表单
    # 访问路径：/lauth/login/
    path('login/', views.login, name='login'),
    
    # 注册页面：显示用户注册表单
    # 访问路径：/lauth/register/
    path('register/', views.register, name='register'),

    # ===== API 路由 =====
    
    # 发送验证码接口：向用户邮箱发送注册验证码
    # 请求方法：POST
    # 请求体：{"email": "user@example.com"}
    # 访问路径：/lauth/send-code/
    path('send-code/', views.send_verification_code, name='send_code'),
    
    # 验证验证码接口：检查用户输入的验证码是否正确
    # 请求方法：POST
    # 请求体：{"email": "user@example.com", "code": "123456"}
    # 访问路径：/lauth/verify-code/
    path('verify-code/', views.verify_code, name='verify_code'),
    
    # 用户注册接口：处理用户注册逻辑，创建新用户
    # 请求方法：POST
    # 请求体：{"username": "...", "email": "...", "password": "...", "verification_code": "..."}
    # 访问路径：/lauth/register-user/
    path('register-user/', views.register_user, name='register_user'),
    
    # 用户登录接口：验证用户凭据并创建会话
    # 请求方法：POST
    # 请求体：{"email": "...", "password": "..."}
    # 访问路径：/lauth/user-login/
    path('user-login/', views.user_login, name='user_login'),
    
    # 用户退出接口：清除用户登录会话
    # 请求方法：POST 或 GET
    # 访问路径：/lauth/user-logout/
    path('user-logout/', views.user_logout, name='user_logout'),
    
    # 检查登录状态接口：返回当前用户的登录状态
    path('check-login/', views.check_login_status, name='check_login'),

    # ===== 忘记密码相关路由 =====

    # 忘记密码页面
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),

    # 发送密码重置验证码
    path('send-reset-code/', views.send_reset_code, name='send_reset_code'),

    # 重置密码
    path('reset-password/', views.reset_password, name='reset_password'),
]