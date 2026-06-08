# ===== 导入模块 =====
# 从 Django 数据库模块导入 models，用于定义数据模型（数据库表结构）
from django.db import models

# 导入 Python 内置的随机数模块，用于生成随机验证码
import random

# 导入 Python 内置的字符串常量模块
# string.digits 包含 '0123456789'，用于生成数字验证码
import string

# 从 datetime 模块导入 timedelta 类，用于时间计算（如计算 5 分钟后的时间）
from datetime import timedelta

# 从 Django 工具模块导入 timezone，用于获取当前时间（支持时区）
from django.utils import timezone


# ===== 定义验证码模型 =====
class VerificationCode(models.Model):
    """
    邮箱验证码模型
    
    继承自 models.Model，Django 会自动将这个类映射为数据库表
    表名格式：<应用名>_<类名小写>，即 lauth_verificationcode
    
    这个表用于存储用户注册时发送的验证码信息
    """
    
    # ===== 定义字段（数据库列）=====
    
    # 邮箱字段
    # EmailField: Django 提供的专门用于存储邮箱的字段类型
    #   - 会自动验证邮箱格式是否正确
    #   - 底层是 VARCHAR 类型
    # '邮箱': 字段的中文标签，在 Django Admin 后台显示
    # max_length=254: 最大长度为 254 个字符
    #   - 这是 RFC 5321 标准规定的邮箱地址最大长度
    email = models.EmailField('邮箱', max_length=254)
    
    # 验证码字段
    # CharField: 用于存储字符串的字段类型
    # '验证码': 字段的中文标签
    # max_length=6: 最大长度为 6 个字符（因为验证码是 6 位数字）
    code = models.CharField('验证码', max_length=6)
    
    # 创建时间字段
    # DateTimeField: 用于存储日期和时间的字段类型
    # '创建时间': 字段的中文标签
    # auto_now_add=True: 自动设置时间为记录创建时的当前时间
    #   - 只在第一次创建记录时自动填充
    #   - 后续修改记录时不会更新这个字段
    #   - 不需要手动赋值，Django 会自动处理
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    # 使用状态字段
    # BooleanField: 布尔值字段，存储 True 或 False
    # '是否已使用': 字段的中文标签
    # default=False: 默认值为 False（未使用）
    #   - 新创建的验证码记录默认为未使用状态
    #   - 验证成功后会将其改为 True
    is_used = models.BooleanField('是否已使用', default=False)
    
    # ===== Meta 类：模型的元数据配置 =====
    class Meta:
        """
        Meta 类用于定义模型的额外属性
        这些属性不影响数据库结构，但影响 Django 的行为
        """
        
        # verbose_name: 单个对象的显示名称
        # 在 Django Admin 后台和其他地方显示时使用
        verbose_name = '验证码'
        
        # verbose_name_plural: 复数形式的显示名称
        # 英文中需要区分单复数，但中文没有复数形式，所以设置为相同
        verbose_name_plural = verbose_name
        
        # ordering: 默认的排序规则
        # 当查询这个模型的记录时，默认按这个规则排序
        # '-created_at': 按创建时间降序排列（最新的在前）
        #   - 负号 '-' 表示降序（从大到小）
        #   - 去掉负号则是升序（从小到大）
        #   - 这样查询时最新生成的验证码会排在前面
        ordering = ['-created_at']
    
    # ===== 定义方法 =====
    
    def __str__(self):
        """
        返回对象的字符串表示
        
        这个方法在以下情况会被调用：
        1. 使用 print() 打印对象时
        2. 在 Django Admin 后台显示对象列表时
        3. 将对象转换为字符串时
        
        Returns:
            str: 格式化的字符串，显示邮箱和验证码
                例如: 'user@example.com - 123456'
        """
        # 使用 f-string 格式化字符串
        # self.email: 当前对象的邮箱字段值
        # self.code: 当前对象的验证码字段值
        return f'{self.email} - {self.code}'
    
    @staticmethod
    def generate_code():
        """
        生成 6 位数字验证码（静态方法）
        
        静态方法的特点：
        - 使用 @staticmethod 装饰器标记
        - 不需要 self 或 cls 参数
        - 不能访问实例属性或类属性
        - 可以像普通函数一样使用，也可以通过类名调用
        
        生成原理：
        1. string.digits 是字符串 '0123456789'
        2. random.choices() 从 digits 中随机选择字符
        3. k=6 表示选择 6 个字符（允许重复）
        4. ''.join() 将字符列表拼接成一个字符串
        
        Returns:
            str: 6 位数字字符串
                例如: '123456', '987654', '000000' 等
                
        Examples:
            >>> VerificationCode.generate_code()
            '583921'
            >>> VerificationCode.generate_code()
            '123456'
        """
        # random.choices(population, k): 从 population 中随机选择 k 个元素
        #   - population: string.digits ('0123456789')
        #   - k: 选择的数量 (6)
        #   - 返回一个列表，例如: ['1', '2', '3', '4', '5', '6']
        
        # ''.join(list): 将列表中的字符用空字符串连接起来
        #   - ['1', '2', '3', '4', '5', '6'] -> '123456'
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_code(cls, email):
        """
        为指定邮箱创建新的验证码记录（类方法）
        
        类方法的特点：
        - 使用 @classmethod 装饰器标记
        - 第一个参数是 cls（类本身），而不是 self（实例）
        - 可以访问类属性和其他类方法
        - 通常用于创建对象的工厂方法
        
        工作流程：
        1. 调用 generate_code() 生成随机验证码
        2. 使用 objects.create() 在数据库中创建新记录
        3. 返回创建的验证码对象
        
        Args:
            cls: 类本身（VerificationCode），由 Python 自动传入
            email (str): 接收验证码的邮箱地址
            
        Returns:
            VerificationCode: 创建的验证码对象
                包含所有字段：email, code, created_at, is_used
                
        Examples:
            >>> verification = VerificationCode.create_code('user@example.com')
            >>> print(verification.code)       # '123456' (随机生成)
            >>> print(verification.email)      # 'user@example.com'
            >>> print(verification.is_used)    # False
            >>> print(verification.created_at) # 2024-01-01 12:00:00
        """
        # 调用静态方法生成 6 位随机验证码
        # cls.generate_code() 等同于 VerificationCode.generate_code()
        # 使用 cls 而不是类名的好处是：如果被子类继承，会使用子类的 generate_code()
        code = cls.generate_code()
        
        # 在数据库中创建新的验证码记录
        # cls.objects.create(): Django ORM 提供的方法
        #   - 创建一个新的对象实例
        #   - 立即保存到数据库（执行 INSERT SQL 语句）
        #   - 返回创建的对象
        # 
        # 参数说明：
        #   email=email: 设置邮箱字段
        #   code=code: 设置验证码字段
        #   created_at: 自动设置为当前时间（因为 auto_now_add=True）
        #   is_used: 自动设置为 False（因为 default=False）
        verification = cls.objects.create(email=email, code=code)
        
        # 返回创建的对象，调用者可以使用这个对象获取验证码等信息
        return verification
    
    def is_valid(self):
        """
        检查验证码是否有效（实例方法）
        
        验证码有效的两个条件：
        1. 未被使用过（is_used == False）
        2. 未过期（创建时间在 5 分钟以内）
        
        这个方法通常在用户提交注册表单时调用，用于验证用户输入的验证码
        
        Returns:
            bool: 验证码是否有效
                - True: 验证码有效（未使用且未过期）
                - False: 验证码无效（已使用或已过期）
                
        Examples:
            >>> verification = VerificationCode.objects.get(email='user@example.com')
            >>> if verification.is_valid():
            ...     print('验证码有效，可以注册')
            ... else:
            ...     print('验证码已过期或已使用，请重新获取')
        """
        # 条件 1：检查验证码是否已被使用
        # self.is_used: 访问当前对象的 is_used 字段
        # 如果已使用（True），直接返回 False，不再检查时间
        if self.is_used:
            return False
        
        # 条件 2：检查验证码是否过期
        
        # 计算过期时间
        # self.created_at: 验证码的创建时间（DateTime 对象）
        # timedelta(minutes=5): 创建一个 5 分钟的时间差对象
        # 两者相加得到过期时间（创建时间 + 5 分钟）
        # 例如: created_at = 10:00:00, expiry_time = 10:05:00
        expiry_time = self.created_at + timedelta(minutes=5)
        
        # 比较当前时间和过期时间
        # timezone.now(): 获取当前时间（带时区信息的 DateTime 对象）
        #   - 比 datetime.now() 更好，因为它考虑了时区
        #   - 返回的是 UTC 时间
        # 
        # <: 如果当前时间小于过期时间，说明还在有效期内
        #   - 例如: 当前时间 10:03:00 < 过期时间 10:05:00 -> True (有效)
        #   - 例如: 当前时间 10:06:00 < 过期时间 10:05:00 -> False (已过期)
        return timezone.now() < expiry_time
