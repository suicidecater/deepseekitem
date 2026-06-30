"""
认证服务 - 仅邮箱注册，三种用户分开注册/登录
"""
import json
import random
import smtplib
import string
from email.mime.text import MIMEText
from datetime import datetime, timedelta

import bcrypt
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db, redis_store
from app.models.user import Student, Coach, PlatformAdmin
from app.models.exam import Evaluation
from app.utils.validators import validate_email, validate_password


class AuthService:
    """认证服务类"""

    # ========== 用户查询 ==========

    @staticmethod
    def get_user_by_email(email):
        """根据邮箱查找用户（遍历三张表）"""
        user = Student.query.filter_by(email=email).first()
        if user:
            return user, 'student'
        user = Coach.query.filter_by(email=email).first()
        if user:
            return user, 'coach'
        user = PlatformAdmin.query.filter_by(email=email).first()
        if user:
            return user, 'admin'
        return None, None

    @staticmethod
    def get_student_by_email(email):
        """仅查学员表"""
        return Student.query.filter_by(email=email).first()

    @staticmethod
    def get_coach_by_email(email):
        """仅查教练表"""
        return Coach.query.filter_by(email=email).first()

    @staticmethod
    def get_admin_by_email(email):
        """仅查管理员表"""
        return PlatformAdmin.query.filter_by(email=email).first()

    @staticmethod
    def _format_user_response(user, user_type):
        """
        格式化用户信息为前端期望的结构：
        { userId, name, avatar, email, role }
        """
        data = user.to_dict()
        admin_type = data.get('admin_type') if user_type == 'admin' else None
        result = {
            'userId': data['id'],
            'name': data.get('name', '') or '',
            'avatar': data.get('avatar', '') or '',
            'email': data.get('email', ''),
            'role': user_type,
        }
        if admin_type is not None:
            result['adminType'] = admin_type
        if user_type == 'student':
            result['studySubject'] = data.get('study_subject', 1)
            # 各方向的测评状态
            status_map = {}
            for d_subj in [1, 4, 5]:
                ev = Evaluation.query.filter_by(
                    student_id=data['id'], study_subject=d_subj
                ).first()
                status_map[str(d_subj)] = 1 if ev else 0
            result['evaluationStatusMap'] = status_map
            result['evaluationStatus'] = status_map.get(str(data.get('study_subject', 1)), 0)
        return result

    # ========== 验证码 ==========

    @staticmethod
    def generate_verify_code():
        """生成6位数字验证码"""
        return ''.join(random.choices(string.digits, k=6))

    @staticmethod
    def send_verify_code(email, code_type='register'):
        """
        发送验证码（QQ邮箱SMTP真实发送）
        返回: (success: bool, message: str)
        """
        if not email:
            return False, '邮箱不能为空'

        if not validate_email(email):
            return False, '邮箱格式不正确'

        # 60秒限频检查
        rate_key = f'verify_code_ratelimit:{email}'
        if redis_store.exists(rate_key):
            ttl = redis_store.ttl(rate_key)
            return False, f'操作过于频繁，请{ttl}秒后再试'

        # 生成验证码
        code = AuthService.generate_verify_code()

        # 存储到Redis，有效期5分钟
        expire_seconds = current_app.config.get('VERIFY_CODE_EXPIRE', 300)
        code_key = f'verify_code:{email}'
        redis_store.setex(code_key, expire_seconds, code)

        # 设置限频Key，60秒过期
        rate_seconds = current_app.config.get('VERIFY_CODE_RATE_LIMIT', 60)
        redis_store.setex(rate_key, rate_seconds, '1')

        # 发送邮件（QQ邮箱SMTP）
        try:
            sent = AuthService._send_email(email, code)
            if sent:
                current_app.logger.info(f'验证码已发送到 {email}: {code}')
                return True, '验证码已发送'
            else:
                current_app.logger.warning(f'邮件发送跳过 {email}（发件人未配置），验证码: {code}')
                return False, '邮件服务未配置，请联系管理员'
        except Exception as e:
            current_app.logger.error(f'邮件发送失败 {email}: {e}')
            current_app.logger.info(f'[Fallback] 验证码: {code}')
            return False, f'邮件发送失败，请稍后再试'

    @staticmethod
    def _send_email(to_email, code):
        """通过QQ邮箱SMTP发送验证码邮件（端口587 TLS加密）
        返回: True=已发送, False=跳过（缺配置）"""
        smtp_host = current_app.config.get('SMTP_HOST', 'smtp.qq.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_password = current_app.config.get('SMTP_PASSWORD', '')

        if not smtp_password:
            current_app.logger.warning('SMTP_PASSWORD 未配置，跳过邮件发送（验证码仅存Redis）')
            return False

        from_email = AuthService._get_config_value('qq_email_address')
        if not from_email:
            from_email = current_app.config.get('SMTP_USER', '')
        if not from_email:
            current_app.logger.warning('SMTP_USER 或 qq_email_address 未配置，跳过邮件发送')
            return False

        msg = MIMEText(
            f'【交通知识培训平台】您的验证码是：{code}，5分钟内有效。请勿将验证码泄露给他人。',
            'plain', 'utf-8'
        )
        msg['Subject'] = '交通知识培训平台 - 验证码'
        msg['From'] = from_email
        msg['To'] = to_email

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(from_email, smtp_password)
            smtp.sendmail(from_email, to_email, msg.as_string())
        return True

    @staticmethod
    def _get_config_value(key):
        """从 system_config 表读取配置值"""
        try:
            from app.models.system_config import SystemConfig
            config = SystemConfig.query.filter_by(config_key=key).first()
            if config:
                return config.config_value
        except Exception:
            pass
        return None

    @staticmethod
    def verify_code(email, code):
        """校验验证码（从Redis读取比对，成功后删除）"""
        code_key = f'verify_code:{email}'
        stored_code = redis_store.get(code_key)

        if stored_code is None:
            return False, '验证码不存在或已过期'

        if stored_code != str(code):
            return False, '验证码不正确'

        redis_store.delete(code_key)
        return True, '验证码校验成功'

    # ========== 通用校验 ==========

    @staticmethod
    def _check_email_exists(email):
        """检查邮箱是否已在任何表中注册"""
        if Student.query.filter_by(email=email).first():
            return True
        if Coach.query.filter_by(email=email).first():
            return True
        if PlatformAdmin.query.filter_by(email=email).first():
            return True
        return False

    @staticmethod
    def _hash_password(password):
        """bcrypt加密密码"""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    @staticmethod
    def _generate_jwt(user_type, user_id):
        """生成JWT access_token和refresh_token"""
        identity = json.dumps({'user_type': user_type, 'user_id': user_id})
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
        return access_token, refresh_token

    @staticmethod
    def _login_common(user, user_type, password=None, code=None):
        """
        通用登录逻辑
        - 检查状态
        - 密码登录或验证码登录
        - 生成JWT
        """
        # 检查状态
        if hasattr(user, 'status') and user.status != 1:
            status_msgs = {
                2: {'student': '该学员已结业', 'coach': '该教练已离职', 'admin': '该管理员已被禁用'},
                3: {'student': '该学员已弃学', 'coach': '该教练已被禁用', 'admin': '该管理员已被禁用'},
                4: {'student': '该学员已被禁用'},
            }
            # 通用禁用提示
            if user.status in status_msgs:
                msgs = status_msgs[user.status]
                msg = msgs.get(user_type, '账号已被禁用或停用')
            else:
                msg = '账号已被禁用或停用'
            return False, msg, None

        # 验证码登录
        if code and not password:
            success, msg = AuthService.verify_code(user.email, code)
            if not success:
                return False, msg, None
        elif password:
            if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                return False, '密码错误', None
        else:
            return False, '请输入密码或验证码', None

        # 生成JWT
        access_token, refresh_token = AuthService._generate_jwt(user_type, user.id)

        return True, '登录成功', {
            'token': access_token,
            'refresh_token': refresh_token,
            'user': AuthService._format_user_response(user, user_type),
        }

    # ========== 学员注册/登录 ==========

    @staticmethod
    def register_student(email, password, name, train_type, car_type=None, code=None):
        """学员注册"""
        if not email or not password:
            return False, '邮箱和密码不能为空', None

        if not validate_password(password):
            return False, '密码至少6位，需包含字母和数字', None

        if not validate_email(email):
            return False, '邮箱格式不正确', None

        if not code:
            return False, '请输入验证码', None

        ok, msg = AuthService.verify_code(email, code)
        if not ok:
            return False, msg, None

        if not name or not name.strip():
            return False, '姓名不能为空', None

        if train_type not in (1, 2, 3, 4):
            return False, '培训类型无效', None

        # 检查邮箱是否已注册
        if AuthService._check_email_exists(email):
            return False, '该邮箱已被注册', None

        # 创建学员
        student = Student(
            email=email,
            password=AuthService._hash_password(password),
            name=name.strip(),
            train_type=train_type,
            car_type=car_type or None,
            status=1,
        )
        student.save()

        access_token, refresh_token = AuthService._generate_jwt('student', student.id)

        return True, '注册成功', {
            'token': access_token,
            'refresh_token': refresh_token,
            'user': AuthService._format_user_response(student, 'student'),
        }

    @staticmethod
    def login_student(email, password=None, code=None):
        """学员登录"""
        if not email:
            return False, '请输入邮箱', None

        user = AuthService.get_student_by_email(email)
        if user is None:
            return False, '学员不存在', None

        return AuthService._login_common(user, 'student', password, code)

    # ========== 教练注册/登录 ==========

    @staticmethod
    def register_coach(email, password, school_name, train_type,
                       school_address=None, school_phone=None, code=None):
        """教练注册"""
        if not email or not password:
            return False, '邮箱和密码不能为空', None

        if not validate_password(password):
            return False, '密码至少6位，需包含字母和数字', None

        if not validate_email(email):
            return False, '邮箱格式不正确', None

        if not code:
            return False, '请输入验证码', None

        ok, msg = AuthService.verify_code(email, code)
        if not ok:
            return False, msg, None

        if not school_name or not school_name.strip():
            return False, '驾校名称不能为空', None

        if train_type not in (1, 2, 3, 4):
            return False, '培训类型无效', None

        if AuthService._check_email_exists(email):
            return False, '该邮箱已被注册', None

        coach = Coach(
            email=email,
            password=AuthService._hash_password(password),
            school_name=school_name.strip(),
            school_address=(school_address or '').strip() or None,
            school_phone=(school_phone or '').strip() or None,
            train_type=train_type,
            status=1,
        )
        coach.save()

        access_token, refresh_token = AuthService._generate_jwt('coach', coach.id)

        return True, '注册成功', {
            'token': access_token,
            'refresh_token': refresh_token,
            'user': AuthService._format_user_response(coach, 'coach'),
        }

    @staticmethod
    def login_coach(email, password=None, code=None):
        """教练登录"""
        if not email:
            return False, '请输入邮箱', None

        user = AuthService.get_coach_by_email(email)
        if user is None:
            return False, '教练不存在', None

        return AuthService._login_common(user, 'coach', password, code)

    # ========== 管理员注册/登录 ==========

    @staticmethod
    def register_admin(email, password, admin_type, code=None):
        """平台管理员注册"""
        if not email or not password:
            return False, '邮箱和密码不能为空', None

        if not validate_password(password):
            return False, '密码至少6位，需包含字母和数字', None

        if not validate_email(email):
            return False, '邮箱格式不正确', None

        if not code:
            return False, '请输入验证码', None

        ok, msg = AuthService.verify_code(email, code)
        if not ok:
            return False, msg, None

        if admin_type not in (1, 2, 3):
            return False, '管理员类型无效', None

        if AuthService._check_email_exists(email):
            return False, '该邮箱已被注册', None

        admin = PlatformAdmin(
            email=email,
            password=AuthService._hash_password(password),
            admin_type=admin_type,
            status=1,
        )
        admin.save()

        access_token, refresh_token = AuthService._generate_jwt('admin', admin.id)

        return True, '注册成功', {
            'token': access_token,
            'refresh_token': refresh_token,
            'user': AuthService._format_user_response(admin, 'admin'),
        }

    @staticmethod
    def login_admin(email, password=None, code=None):
        """平台管理员登录"""
        if not email:
            return False, '请输入邮箱', None

        user = AuthService.get_admin_by_email(email)
        if user is None:
            return False, '管理员不存在', None

        return AuthService._login_common(user, 'admin', password, code)

    # ========== 向下兼容：统一登录 ==========

    @staticmethod
    def login(email, password=None, code=None):
        """
        统一登录（向下兼容，遍历三张表）
        """
        if not email:
            return False, '请输入邮箱', None

        user, user_type = AuthService.get_user_by_email(email)
        if user is None:
            return False, '用户不存在', None

        return AuthService._login_common(user, user_type, password, code)

    @staticmethod
    def register(email, password, name=None, code=None):
        """
        学员注册（向下兼容）
        """
        return AuthService.register_student(
            email=email,
            password=password,
            name=name or '',
            train_type=1,
            car_type='C1',
            code=code,
        )

    # ========== Token刷新 ==========

    @staticmethod
    def refresh_token():
        """刷新Access Token"""
        return True, 'Token刷新成功', {
            'message': 'Token已刷新'
        }

    # ========== 退出 ==========

    @staticmethod
    def logout(jti):
        """退出登录：将JWT jti加入Redis黑名单"""
        from flask_jwt_extended import get_jwt
        expires = get_jwt().get('exp', 0)
        now = datetime.utcnow().timestamp()
        ttl = max(int(expires - now), 1)

        redis_store.setex(f'jwt_blacklist:{jti}', ttl, '1')

    # ========== 当前用户信息 ==========

    @staticmethod
    def get_current_user_info(user, user_type):
        """获取当前用户详细信息（前端格式）"""
        return AuthService._format_user_response(user, user_type)
