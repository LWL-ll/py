from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings


def login_required(view_func):
    """
    登录验证装饰器
    
    这是一个自定义的登录验证装饰器，用于保护需要登录才能访问的视图。
    与 Django 内置的 @login_required 相比，它提供了更好的 AJAX 支持。
    
    功能特性：
    - 如果用户未登录，根据请求类型采取不同处理方式：
      * AJAX 请求：返回 401 JSON 响应，包含重定向 URL
      * 普通请求：重定向到登录页面，并保留原始 URL
    - 如果用户已登录，正常执行视图函数
    - 使用 @wraps 保持原视图函数的元信息（如 __name__、__doc__）
    
    Args:
        view_func: 需要保护的视图函数
        
    Returns:
        wrapper: 包装后的视图函数，包含登录验证逻辑
        
    Usage Examples:
        # 在视图中使用
        @login_required
        def my_view(request):
            return render(request, 'my_template.html')
        
        # 在 URL 配置中使用
        path('protected/', login_required(MyView.as_view()))
        
    Response Examples:
        # AJAX 请求未登录时的响应
        {
            "success": false,
            "message": "请先登录",
            "need_login": true,
            "redirect_url": "/lauth/login/"
        }
        
        # 普通请求未登录时
        # 重定向到：/lauth/login/?next=/protected/page/
        
    Note:
        - 依赖 settings.LOGIN_URL 配置项
        - AJAX 检测通过 X-Requested-With 头或 Content-Type 判断
        - 重定向时会保存原始 URL 到 next 参数，登录后可以返回
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        """
        包装函数，在实际执行视图前进行登录验证
        
        Args:
            request: HTTP 请求对象
            *args: 位置参数，传递给原视图函数
            **kwargs: 关键字参数，传递给原视图函数
            
        Returns:
            HttpResponse: 根据登录状态返回不同的响应
        """
        # 检查用户是否已登录
        # request.user.is_authenticated 是 Django 提供的属性
        # 已登录返回 True，未登录返回 False
        if not request.user.is_authenticated:
            # 判断是否是 AJAX 请求
            # 方法1: 检查 X-Requested-With 请求头（jQuery 等库会自动添加）
            # 方法2: 检查 Content-Type 是否为 application/json
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               request.content_type == 'application/json':
                # AJAX 请求：返回 JSON 格式的 401 响应
                # 前端可以根据 need_login 字段判断需要登录
                # redirect_url 告诉前端应该跳转到哪个页面
                return JsonResponse({
                    'success': False,
                    'message': '请先登录',
                    'need_login': True,
                    'redirect_url': settings.LOGIN_URL
                }, status=401)
            else:
                # 普通请求：重定向到登录页面
                # ?next={request.path} 保存原始 URL
                # 登录成功后可以读取这个参数并跳转回去
                # 例如：/lauth/login/?next=/community/bilei/
                return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        
        # 用户已登录，执行原视图函数
        # 将所有参数原样传递给原视图
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
