# ===== 导入模块 =====
# 导入正则表达式模块，用于邮箱格式验证
import re
# 导入 JSON 模块，用于解析前端传来的 JSON 数据
import json
# 导入日志模块，用于记录程序运行状态和错误信息
import logging
# 从 Django 快捷方式模块导入 render 函数，用于渲染 HTML 模板
from django.shortcuts import render
# 从 Django HTTP 模块导入 JsonResponse 类，用于返回 JSON 格式的响应
from django.http import JsonResponse
# 从 Django 邮件模块导入 send_mail 函数，用于发送电子邮件
from django.core.mail import send_mail
# 从 Django 配置模块导入 settings 对象，用于访问项目配置（如邮件设置）
from django.conf import settings
# 从 Django 认证模块导入 User 模型，这是 Django 内置的用户表模型
from django.contrib.auth.models import User
# 从 Django 认证模块导入 authenticate（验证用户）和 login（创建会话）函数
from django.contrib.auth import authenticate, login as auth_login
# 从 Django 数据库模块导入 IntegrityError 异常，用于捕获数据库完整性错误
from django.db import IntegrityError
# 从当前应用的 models 模块导入 VerificationCode 验证码模型
from .models import VerificationCode

# ===== 配置日志 =====
# 创建一个日志记录器实例
# __name__ 的值是 'lauth.views'，这样可以在日志中区分不同模块的输出
logger = logging.getLogger(__name__)

# ===== 页面视图函数 =====
def login(request):
    """
    显示登录页面
    
    Args:
        request: HTTP 请求对象，包含请求的所有信息
        
    Returns:
        HttpResponse: 渲染后的 login.html 页面
    """
    # 使用 render 函数渲染 templates/login.html 模板并返回
    # request 参数会传递给模板，使其可以访问 CSRF token 等信息
    return render(request, 'login.html')


def register(request):
    """
    显示注册页面
    
    Args:
        request: HTTP 请求对象
        
    Returns:
        HttpResponse: 渲染后的 register.html 页面
    """
    # 渲染 templates/register.html 模板并返回
    return render(request, 'register.html')


# ===== 辅助函数（私有函数，以下划线开头）=====
def _validate_email(email):
    """
    验证邮箱格式是否符合标准
    
    使用正则表达式检查邮箱是否包含：
    - @ 符号前有非空白字符
    - @ 符号
    - @ 符号后有非空白字符
    - 一个点号 .
    - 点号后有非空白字符
    
    Args:
        email (str): 待验证的邮箱地址字符串
        
    Returns:
        bool: 
            - True: 邮箱格式正确
            - False: 邮箱格式错误或为空
    """
    # 定义邮箱验证的正则表达式模式
    # ^           : 字符串开始
    # [^\s@]+     : 一个或多个非空白、非@的字符（用户名部分）
    # @           : @ 符号
    # [^\s@]+     : 一个或多个非空白、非@的字符（域名部分）
    # \.          : 点号（需要转义）
    # [^\s@]+     : 一个或多个非空白、非@的字符（顶级域名部分）
    # $           : 字符串结束
    email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    
    # 使用 re.match() 从字符串开头匹配正则表达式
    # 如果匹配成功返回 Match 对象，失败返回 None
    # bool() 将结果转换为布尔值（Match 对象为 True，None 为 False）
    return bool(re.match(email_pattern, email))


def _get_latest_verification(email):
    """
    获取指定邮箱最新的未使用验证码记录
    
    查询条件：
    1. 邮箱地址匹配
    2. is_used 字段为 False（未使用）
    3. 按创建时间倒序排列，取第一条（最新的）
    
    Args:
        email (str): 邮箱地址
        
    Returns:
        VerificationCode 或 None:
            - 找到则返回 VerificationCode 对象
            - 未找到则返回 None
    """
    # 使用 Django ORM 查询数据库
    # objects.filter(): 筛选符合条件的记录
    return VerificationCode.objects.filter(
        email=email,        # 条件1: 邮箱地址匹配
        is_used=False       # 条件2: 验证码未被使用
    ).order_by('-created_at').first()  # 按创建时间降序排列，取第一条
    # order_by('-created_at'): 负号表示降序（最新的在前）
    # first(): 返回查询集的第一条记录，如果没有则返回 None


# ===== API 视图函数 =====
def send_verification_code(request):
    """
    发送邮箱验证码接口
    
    工作流程：
    1. 验证请求方法是否为 POST
    2. 解析并验证邮箱地址
    3. 检查邮箱是否已被注册
    4. 生成验证码并存入数据库
    5. 发送邮件到用户邮箱
    6. 返回成功或失败信息
    
    Args:
        request: HTTP 请求对象，body 中包含 JSON 格式的邮箱地址
        
    Returns:
        JsonResponse: JSON 格式的响应
            成功: {'success': True, 'message': '验证码已发送到您的邮箱'}
            失败: {'success': False, 'message': 错误信息}
    """
    # 检查请求方法是否为 POST
    # 如果不是 POST 请求，返回 405 状态码（Method Not Allowed）
    if request.method != 'POST':
        # status=405 表示请求方法不被允许
        return JsonResponse({'success': False, 'message': '请求方法错误'}, status=405)
    
    # 使用 try-except 捕获可能的异常
    try:
        # 解析请求体中的 JSON 数据
        # request.body 是原始的字节数据，需要用 json.loads() 解析
        data = json.loads(request.body)
        
        # 从解析后的数据中获取 email 字段
        # .get('email', ''): 如果不存在则返回空字符串
        # .strip(): 去除首尾空格
        email = data.get('email', '').strip()
        
        # 验证邮箱是否为空
        if not email:
            # 返回错误信息
            return JsonResponse({'success': False, 'message': '请输入邮箱地址'})
        
        # 调用辅助函数验证邮箱格式
        if not _validate_email(email):
            return JsonResponse({'success': False, 'message': '邮箱格式不正确'})
        
        # 检查邮箱是否已经被注册
        # User.objects.filter(email=email).exists() 返回布尔值
        # exists() 比 count() 更高效，因为它只检查是否存在，不统计数量
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': '该邮箱已被注册'})
        
        # 调用模型的类方法创建验证码记录
        # 这会生成 6 位随机验证码并保存到数据库
        verification = VerificationCode.create_code(email)
        
        # 准备邮件主题
        subject = '注册验证码'
        
        # 准备邮件内容，使用 f-string 格式化验证码
        # \n\n 表示两个换行符，使邮件内容更易读
        message = f'您的验证码是：{verification.code}\n\n验证码有效期为5分钟，请勿泄露给他人。'
        
        # 嵌套的 try-except 用于捕获邮件发送过程中的异常
        try:
            # 调用 Django 的 send_mail 函数发送邮件
            send_mail(
                subject,                        # 邮件主题
                message,                        # 邮件正文
                settings.DEFAULT_FROM_EMAIL,    # 发件人邮箱（在 settings.py 中配置）
                [email],                        # 收件人列表（可以是多个）
                fail_silently=False,            # 发送失败时抛出异常（而不是静默失败）
            )
            
            # 邮件发送成功，记录日志
            # logger.info 记录一般信息
            logger.info(f'验证码发送成功: {email}')
            
            # 返回成功响应
            return JsonResponse({'success': True, 'message': '验证码已发送到您的邮箱'})
        
        except Exception as e:
            # 邮件发送失败，执行清理操作
            
            # 删除刚才创建的验证码记录
            # 因为邮件没发送成功，这个验证码没有意义，避免数据库垃圾数据
            verification.delete()
            
            # 记录错误日志
            # logger.error 记录错误信息，包含具体的异常信息
            logger.error(f'邮件发送失败: {email}, 错误: {str(e)}')
            
            # 返回失败响应，但不暴露具体错误细节（安全考虑）
            return JsonResponse({'success': False, 'message': '邮件发送失败，请稍后重试'})
    
    except json.JSONDecodeError:
        # 捕获 JSON 解析错误（前端发送的数据格式不正确）
        # logger.warning 记录警告信息
        logger.warning('无效的 JSON 请求数据')
        return JsonResponse({'success': False, 'message': '无效的请求数据'})
    
    except Exception as e:
        # 捕获其他所有未预期的异常
        # 记录详细的错误信息，方便调试
        logger.error(f'发送验证码时发生错误: {str(e)}')
        # 返回通用的错误信息，不暴露系统内部细节
        return JsonResponse({'success': False, 'message': '服务器错误，请稍后重试'})


def verify_code(request):
    """
    验证邮箱验证码是否正确
    
    工作流程：
    1. 验证请求方法
    2. 解析邮箱和验证码
    3. 从数据库获取最新的未使用验证码
    4. 检查验证码是否存在、是否过期、是否匹配
    5. 验证成功后标记为已使用
    
    Args:
        request: HTTP 请求对象，body 中包含 JSON 格式的邮箱和验证码
        
    Returns:
        JsonResponse: JSON 格式的验证结果
            成功: {'success': True, 'message': '验证成功'}
            失败: {'success': False, 'message': 错误信息}
    """
    # 验证请求方法是否为 POST
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法错误'}, status=405)
    
    try:
        # 解析请求体中的 JSON 数据
        data = json.loads(request.body)
        
        # 获取邮箱和验证码字段，去除空格
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        
        # 验证两个参数都不能为空
        if not email or not code:
            return JsonResponse({'success': False, 'message': '请提供邮箱和验证码'})
        
        # 调用辅助函数获取最新的未使用验证码
        verification = _get_latest_verification(email)
        
        # 检查是否找到验证码
        # 如果返回 None，说明没有未使用的验证码
        if not verification:
            return JsonResponse({'success': False, 'message': '验证码不存在或已使用'})
        
        # 调用模型方法检查验证码是否有效（未过期）
        # is_valid() 会检查创建时间是否在 5 分钟内
        if not verification.is_valid():
            return JsonResponse({'success': False, 'message': '验证码已过期'})
        
        # 检查用户输入的验证码是否与数据库中的一致
        if verification.code != code:
            return JsonResponse({'success': False, 'message': '验证码错误'})
        
        # 验证通过，标记验证码为已使用
        # 这样可以防止同一个验证码被重复使用
        verification.is_used = True
        
        # 保存修改到数据库
        verification.save()
        
        # 记录成功日志
        logger.info(f'验证码验证成功: {email}')
        
        # 返回成功响应
        return JsonResponse({'success': True, 'message': '验证成功'})
    
    except Exception as e:
        # 捕获所有异常
        logger.error(f'验证验证码时发生错误: {str(e)}')
        return JsonResponse({'success': False, 'message': '服务器错误，请稍后重试'})


def register_user(request):
    """
    处理用户注册（核心功能：将用户信息存入数据库）
    
    工作流程：
    1. 验证请求方法
    2. 解析并验证所有输入字段
    3. 验证验证码有效性
    4. 检查用户名和邮箱的唯一性
    5. 创建新用户记录
    6. 标记验证码为已使用
    
    Args:
        request: HTTP 请求对象，body 中包含 JSON 格式的注册信息
        
    Returns:
        JsonResponse: JSON 格式的注册结果
            成功: {'success': True, 'message': '注册成功！请登录'}
            失败: {'success': False, 'message': 错误信息}
    """
    # 验证请求方法
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法错误'}, status=405)
    
    try:
        # 解析 JSON 数据
        data = json.loads(request.body)
        
        # 获取各个字段，去除空格
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')  # 密码不去除空格，保留原始输入
        verification_code = data.get('verification_code', '').strip()
        
        # ===== 第一层验证：基本字段验证 =====
        
        # 验证用户名不能为空且至少 3 个字符
        if not username or len(username) < 3:
            return JsonResponse({'success': False, 'message': '用户名至少需要3个字符'})
        
        # 验证用户名不超过 150 个字符（Django User 模型的默认限制）
        if len(username) > 150:
            return JsonResponse({'success': False, 'message': '用户名过长'})
        
        # 验证邮箱不能为空
        if not email:
            return JsonResponse({'success': False, 'message': '请输入邮箱地址'})
        
        # 验证邮箱格式
        if not _validate_email(email):
            return JsonResponse({'success': False, 'message': '邮箱格式不正确'})
        
        # 验证密码不能为空且至少 6 个字符
        if not password or len(password) < 6:
            return JsonResponse({'success': False, 'message': '密码至少需要6个字符'})
        
        # 验证密码不超过 128 个字符（合理的安全限制）
        if len(password) > 128:
            return JsonResponse({'success': False, 'message': '密码过长'})
        
        # 验证验证码不能为空
        if not verification_code:
            return JsonResponse({'success': False, 'message': '请输入验证码'})
        
        # ===== 第二层验证：验证码验证 =====
        
        # 获取最新的未使用验证码
        verification = _get_latest_verification(email)
        
        # 综合判断验证码是否有效：
        # 1. verification 不为 None（存在未使用的验证码）
        # 2. verification.is_valid() 为 True（未过期）
        # 3. verification.code == verification_code（验证码匹配）
        if not verification or not verification.is_valid() or verification.code != verification_code:
            return JsonResponse({'success': False, 'message': '验证码无效或已过期'})
        
        # ===== 第三层验证：唯一性检查 =====
        
        # 检查用户名是否已存在
        # exists() 返回布尔值，效率高于 count()
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': '用户名已被使用'})
        
        # 检查邮箱是否已注册
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': '该邮箱已被注册'})
        
        # ===== 核心操作：创建用户 =====
        
        try:
            # 调用 Django 内置的 create_user 方法创建用户
            # 这个方法会：
            # 1. 自动加密密码（使用 PBKDF2 算法）
            # 2. 创建 User 对象并保存到数据库
            # 3. 返回创建的用户对象
            user = User.objects.create_user(
                username=username,   # 用户名
                email=email,         # 邮箱
                password=password    # 密码（会自动加密）
            )
        except IntegrityError:
            # 捕获数据库完整性错误
            # 例如：违反唯一性约束（理论上前面已经检查过，但作为双重保障）
            return JsonResponse({'success': False, 'message': '注册失败，请稍后重试'})
        
        # ===== 后续操作：标记验证码为已使用 =====

        # 将验证码标记为已使用，防止被再次使用
        verification.is_used = True
        verification.save()

        # ===== 注册后自动登录 =====
        auth_login(request, user)
        request.session.set_expiry(5 * 24 * 60 * 60)  # 5天有效期

        logger.info(f'用户注册并登录成功: {username} ({email})')

        return JsonResponse({
            'success': True,
            'message': '注册成功！',
            'username': user.username
        })
    
    except Exception as e:
        # 捕获所有未预期的异常
        logger.error(f'用户注册失败: {str(e)}')
        # 返回通用错误信息，不暴露系统内部细节
        return JsonResponse({'success': False, 'message': '注册失败，请稍后重试'})


def user_login(request):
    """
    处理用户登录（从数据库验证用户身份并创建会话）
    
    工作流程：
    1. 验证请求方法
    2. 解析邮箱和密码
    3. 根据邮箱查找用户
    4. 验证密码
    5. 创建登录会话（session）
    6. 返回登录结果
    
    Args:
        request: HTTP 请求对象，body 中包含 JSON 格式的登录信息
        
    Returns:
        JsonResponse: JSON 格式的登录结果
            成功: {'success': True, 'message': '登录成功', 'username': 用户名}
            失败: {'success': False, 'message': '邮箱或密码错误'}
    """
    # 验证请求方法
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法错误'}, status=405)
    
    # 如果用户已登录，直接返回
    if request.user.is_authenticated:
        return JsonResponse({
            'success': True,
            'message': '已登录',
            'username': request.user.username
        })
    
    try:
        # 解析 JSON 数据
        data = json.loads(request.body)
        
        # 获取邮箱和密码
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # ===== 基本验证 =====
        
        # 验证邮箱不能为空
        if not email:
            return JsonResponse({'success': False, 'message': '请输入邮箱地址'})
        
        # 验证密码不能为空
        if not password:
            return JsonResponse({'success': False, 'message': '请输入密码'})
        
        # ===== 查找并验证用户 =====
        
        # 定义统一的错误响应
        # 安全考虑：不区分"邮箱不存在"和"密码错误"，防止攻击者枚举邮箱
        error_message = {'success': False, 'message': '邮箱或密码错误'}
        
        try:
            # 根据邮箱查找用户
            user = User.objects.get(email=email)
        
        except User.DoesNotExist:
            # 用户不存在
            logger.warning(f'登录失败 - 邮箱不存在: {email}')
            return JsonResponse(error_message)
        
        except User.MultipleObjectsReturned:
            # 多个用户使用同一邮箱
            logger.error(f'登录失败 - 多个用户使用同一邮箱: {email}')
            return JsonResponse(error_message)
        
        # ===== 验证密码 =====
        
        # 调用 Django 的 authenticate 函数验证用户凭据
        authenticated_user = authenticate(username=user.username, password=password)
        
        # 检查认证结果
        if authenticated_user is None:
            # 密码错误
            logger.warning(f'登录失败 - 密码错误: {email}')
            return JsonResponse(error_message)
        
        # ===== 创建登录会话 =====
        
        # 调用 auth_login 函数创建会话
        auth_login(request, authenticated_user)
        
        # 设置 session 过期时间为 5 天
        request.session.set_expiry(5 * 24 * 60 * 60)
        
        # 记录成功日志
        logger.info(f'用户登录成功: {user.username}')
        
        # 返回成功响应，包含用户名供前端显示
        return JsonResponse({
            'success': True, 
            'message': '登录成功',
            'username': user.username
        })
    
    except Exception as e:
        # 捕获所有未预期的异常
        logger.error(f'登录时发生错误: {str(e)}')
        return JsonResponse({'success': False, 'message': '登录失败，请稍后重试'})


def user_logout(request):
    """
    处理用户退出登录
    
    工作流程：
    1. 清除用户的登录会话
    2. 返回退出成功消息
    
    Args:
        request: HTTP 请求对象
        
    Returns:
        JsonResponse: JSON 格式的退出结果
            成功: {'success': True, 'message': '退出成功'}
    """
    from django.contrib.auth import logout as auth_logout
    
    # 调用 Django 的 logout 函数清除会话
    auth_logout(request)
    
    # 记录日志
    logger.info('用户退出登录')
    
    # 返回成功响应
    return JsonResponse({'success': True, 'message': '退出成功'})


def forgot_password_page(request):
    """
    显示忘记密码页面
    """
    return render(request, 'forgot_password.html')


def send_reset_code(request):
    """
    发送密码重置验证码（仅已注册邮箱可接收）

    与注册验证码的区别：
    - 必须邮箱已注册才能发送（防止枚举未注册邮箱）
    - 返回时提示"5分钟内有效"
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法错误'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()

        if not email:
            return JsonResponse({'success': False, 'message': '请输入邮箱地址'})
        if not _validate_email(email):
            return JsonResponse({'success': False, 'message': '邮箱格式不正确'})

        # 检查邮箱是否已注册（只有已注册用户才能重置密码）
        if not User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': '该邮箱未注册'})

        # 创建验证码并发送邮件
        verification = VerificationCode.create_code(email)

        subject = '密码重置验证码'
        message = f'您正在重置密码，验证码是：{verification.code}\n\n验证码有效期为5分钟，如非本人操作请忽略此邮件。'

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
            logger.info(f'密码重置验证码发送成功: {email}')
            return JsonResponse({'success': True, 'message': '验证码已发送，5分钟内有效'})
        except Exception as e:
            verification.delete()
            logger.error(f'密码重置邮件发送失败: {email}, 错误: {str(e)}')
            return JsonResponse({'success': False, 'message': '邮件发送失败，请稍后重试'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '无效的请求数据'})
    except Exception as e:
        logger.error(f'发送重置验证码时发生错误: {str(e)}')
        return JsonResponse({'success': False, 'message': '服务器错误，请稍后重试'})


def reset_password(request):
    """
    重置密码：验证验证码后更新密码
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方法错误'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        new_password = data.get('new_password', '')

        if not email or not code:
            return JsonResponse({'success': False, 'message': '请提供邮箱和验证码'})
        if not new_password or len(new_password) < 6:
            return JsonResponse({'success': False, 'message': '新密码至少需要6个字符'})

        # 验证验证码
        verification = _get_latest_verification(email)
        if not verification or not verification.is_valid() or verification.code != code:
            return JsonResponse({'success': False, 'message': '验证码无效或已过期'})

        # 查找用户并更新密码
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': '用户不存在'})

        user.set_password(new_password)
        user.save()

        # 标记验证码为已使用
        verification.is_used = True
        verification.save()

        logger.info(f'密码重置成功: {email}')
        return JsonResponse({'success': True, 'message': '密码重置成功！请使用新密码登录'})

    except Exception as e:
        logger.error(f'重置密码时发生错误: {str(e)}')
        return JsonResponse({'success': False, 'message': '重置失败，请稍后重试'})


def check_login_status(request):
    """
    检查用户登录状态
    
    Args:
        request: HTTP 请求对象
        
    Returns:
        JsonResponse: JSON 格式的登录状态
            已登录: {'is_authenticated': True, 'username': 用户名}
            未登录: {'is_authenticated': False}
    """
    if request.user.is_authenticated:
        return JsonResponse({
            'is_authenticated': True,
            'username': request.user.username
        })
    else:
        return JsonResponse({
            'is_authenticated': False
        })
