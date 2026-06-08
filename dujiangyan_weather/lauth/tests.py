from django.test import TestCase
from django.contrib.auth.models import User
from .models import VerificationCode
from datetime import timedelta
from django.utils import timezone


class VerificationCodeModelTest(TestCase):
    """
    验证码模型的单元测试
    
    测试 VerificationCode 模型的创建、生成、验证等功能
    """
    
    def test_generate_code(self):
        """测试生成 6 位数字验证码"""
        code = VerificationCode.generate_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
    
    def test_create_code(self):
        """测试创建验证码记录"""
        verification = VerificationCode.create_code('test@example.com')
        self.assertEqual(verification.email, 'test@example.com')
        self.assertEqual(len(verification.code), 6)
        self.assertFalse(verification.is_used)
        self.assertIsNotNone(verification.created_at)
    
    def test_is_valid_unused_and_not_expired(self):
        """测试有效验证码（未使用且未过期）"""
        verification = VerificationCode.create_code('test@example.com')
        self.assertTrue(verification.is_valid())
    
    def test_is_valid_used(self):
        """测试已使用的验证码"""
        verification = VerificationCode.create_code('test@example.com')
        verification.is_used = True
        verification.save()
        self.assertFalse(verification.is_valid())
    
    def test_is_valid_expired(self):
        """测试已过期的验证码"""
        verification = VerificationCode.create_code('test@example.com')
        # 手动设置创建时间为 6 分钟前（超过 5 分钟有效期）
        verification.created_at = timezone.now() - timedelta(minutes=6)
        verification.save()
        self.assertFalse(verification.is_valid())
    
    def test_default_ordering(self):
        """测试默认排序（按创建时间降序）"""
        v1 = VerificationCode.create_code('test1@example.com')
        v2 = VerificationCode.create_code('test2@example.com')
        codes = VerificationCode.objects.all()
        self.assertEqual(list(codes), [v2, v1])


class EmailValidationTest(TestCase):
    """
    邮箱格式验证的单元测试
    
    测试 _validate_email 辅助函数的验证逻辑
    """
    
    def test_valid_emails(self):
        """测试有效的邮箱格式"""
        from .views import _validate_email
        
        valid_emails = [
            'user@example.com',
            'test.user@domain.org',
            'user+tag@gmail.com',
            'user_name@test.co.uk',
        ]
        
        for email in valid_emails:
            self.assertTrue(_validate_email(email), f'{email} 应该是有效的')
    
    def test_invalid_emails(self):
        """测试无效的邮箱格式"""
        from .views import _validate_email
        
        invalid_emails = [
            '',
            'not-an-email',
            '@example.com',
            'user@',
            'user@.com',
            'user @example.com',
        ]
        
        for email in invalid_emails:
            self.assertFalse(_validate_email(email), f'{email} 应该是无效的')


class SendVerificationCodeViewTest(TestCase):
    """
    发送验证码视图的单元测试
    
    测试发送验证码接口的功能和验证逻辑
    """
    
    def test_send_code_requires_post(self):
        """测试必须使用 POST 方法"""
        response = self.client.get('/lauth/send-code/')
        self.assertEqual(response.status_code, 405)
    
    def test_send_code_invalid_email(self):
        """测试无效邮箱格式"""
        response = self.client.post(
            '/lauth/send-code/',
            data={'email': 'invalid-email'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_send_code_already_registered(self):
        """测试已注册的邮箱"""
        User.objects.create_user(username='testuser', email='test@example.com', password='pass123')
        
        response = self.client.post(
            '/lauth/send-code/',
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('已被注册', data['message'])


class RegisterUserViewTest(TestCase):
    """
    用户注册视图的单元测试
    
    测试用户注册流程和验证逻辑
    """
    
    def setUp(self):
        """测试前准备：创建有效的验证码"""
        self.verification = VerificationCode.create_code('newuser@example.com')
        self.valid_code = self.verification.code
    
    def test_register_success(self):
        """测试成功注册"""
        import json
        response = self.client.post(
            '/lauth/register-user/',
            data=json.dumps({
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'password123',
                'verification_code': self.valid_code
            }),
            content_type='application/json'
        )
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(User.objects.count(), 1)
        
        user = User.objects.first()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
    
    def test_register_username_too_short(self):
        """测试用户名过短"""
        import json
        response = self.client.post(
            '/lauth/register-user/',
            data=json.dumps({
                'username': 'ab',
                'email': 'newuser@example.com',
                'password': 'password123',
                'verification_code': self.valid_code
            }),
            content_type='application/json'
        )
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('至少需要3个字符', data['message'])
    
    def test_register_password_too_short(self):
        """测试密码过短"""
        import json
        response = self.client.post(
            '/lauth/register-user/',
            data=json.dumps({
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': '12345',
                'verification_code': self.valid_code
            }),
            content_type='application/json'
        )
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('至少需要6个字符', data['message'])
    
    def test_register_invalid_verification_code(self):
        """测试无效的验证码"""
        import json
        response = self.client.post(
            '/lauth/register-user/',
            data=json.dumps({
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'password123',
                'verification_code': '999999'
            }),
            content_type='application/json'
        )
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('验证码无效', data['message'])
    
    def test_register_duplicate_username(self):
        """测试重复的用户名"""
        User.objects.create_user(username='existinguser', email='other@example.com', password='pass123')
        
        import json
        response = self.client.post(
            '/lauth/register-user/',
            data=json.dumps({
                'username': 'existinguser',
                'email': 'newuser@example.com',
                'password': 'password123',
                'verification_code': self.valid_code
            }),
            content_type='application/json'
        )
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('用户名已被使用', data['message'])


class UserLoginViewTest(TestCase):
    """
    用户登录视图的单元测试
    
    测试用户登录流程和会话创建
    """
    
    def setUp(self):
        """测试前准备：创建测试用户"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    def test_login_success(self):
        """测试成功登录"""
        import json
        response = self.client.post(
            '/lauth/user-login/',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['username'], 'testuser')
    
    def test_login_wrong_password(self):
        """测试密码错误"""
        import json
        response = self.client.post(
            '/lauth/user-login/',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('邮箱或密码错误', data['message'])
    
    def test_login_nonexistent_email(self):
        """测试不存在的邮箱"""
        import json
        response = self.client.post(
            '/lauth/user-login/',
            data=json.dumps({
                'email': 'nonexistent@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('邮箱或密码错误', data['message'])


class LoginDecoratorTest(TestCase):
    """
    登录验证装饰器的单元测试
    
    测试 @login_required 装饰器的功能
    """
    
    def test_check_login_authenticated(self):
        """测试已登录用户的状态检查"""
        # 创建并登录用户
        user = User.objects.create_user(username='testuser', password='pass123')
        self.client.login(username='testuser', password='pass123')
        
        response = self.client.get('/lauth/check-login/')
        data = response.json()
        self.assertTrue(data['is_authenticated'])
        self.assertEqual(data['username'], 'testuser')
    
    def test_check_login_not_authenticated(self):
        """测试未登录用户的状态检查"""
        response = self.client.get('/lauth/check-login/')
        data = response.json()
        self.assertFalse(data['is_authenticated'])
