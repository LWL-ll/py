from django.contrib import admin
from .models import VerificationCode


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    """
    验证码的后台管理配置
    
    提供验证码记录的列表展示、搜索和过滤功能，
    方便管理员查看和管理用户注册时发送的验证码。
    
    Features:
        - 显示邮箱、验证码、创建时间和使用状态
        - 可按使用状态和创建时间过滤
        - 支持按邮箱和验证码内容搜索
        - 创建时间为只读字段，不可编辑
    """
    # 列表展示的字段：邮箱、验证码、创建时间、使用状态
    list_display = ['email', 'code', 'created_at', 'is_used']
    
    # 右侧过滤器：按使用状态和创建时间筛选
    # 可以快速查看所有未使用或已过期的验证码
    list_filter = ['is_used', 'created_at']
    
    # 搜索字段：可以按邮箱地址和验证码内容搜索
    search_fields = ['email', 'code']
    
    # 只读字段：创建时间不可编辑
    # 因为这是自动记录的时间戳，不应手动修改
    readonly_fields = ['created_at']
