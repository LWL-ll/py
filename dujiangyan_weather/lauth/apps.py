from django.apps import AppConfig


class AuthConfig(AppConfig):
    """
    认证应用的配置类
    
    定义 lauth (Login Authentication) 应用的基本配置信息。
    
    该应用负责处理用户的认证相关功能，包括：
    - 用户注册（带邮箱验证码验证）
    - 用户登录（使用邮箱和密码）
    - 用户退出登录
    - 登录状态检查
    - 验证码管理
    
    Attributes:
        name: Django 应用的完整 Python 路径
        
    Note:
        - 该应用使用自定义的登录验证装饰器（decorators.py）
        - 验证码有效期为 5 分钟
        - 登录会话默认保持 5 天
    """
    # Django 应用的完整 Python 路径
    name = 'lauth'
    
    # 应用在后台管理中显示的友好名称（可选）
    verbose_name = '用户认证'
