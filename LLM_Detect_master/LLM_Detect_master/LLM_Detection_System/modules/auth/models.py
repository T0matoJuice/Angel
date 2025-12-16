#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证模型
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from modules.auth import db


class User(UserMixin, db.Model):
    """用户模型 - 映射到 MySQL angel.user 表

    Attributes:
        id: 用户ID（主键，自增）
        username: 用户名
        password: 密码（存储哈希值）
        email: 邮箱
        role: 角色（有关权限）
        creat_time: 创建时间
        is_active: 是否启用
    """
    __tablename__ = 'user'  # 映射到 MySQL 的 user 表

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)  # 注意：字段名是 password，不是 password_hash
    email = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(255), nullable=True, default='user')  # 默认角色为普通用户
    creat_time = db.Column(db.String(255), nullable=True)  # 注意：字段名是 creat_time
    is_active = db.Column(db.String(255), nullable=True, default='1')  # 注意：类型是 varchar，'1'表示启用
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password_text):
        """设置密码（加密存储）

        Args:
            password_text: 明文密码
        """
        # 注意：字段名是 password，不是 password_hash
        self.password = generate_password_hash(password_text)

    def check_password(self, password_text):
        """验证密码

        Args:
            password_text: 明文密码

        Returns:
            bool: 密码是否正确
        """
        # 注意：字段名是 password，不是 password_hash
        return check_password_hash(self.password, password_text)
    
    def get_id(self):
        """获取用户ID（Flask-Login要求）
        
        Returns:
            str: 用户ID字符串
        """
        return str(self.id)
    
    @property
    def is_authenticated(self):
        """用户是否已认证（Flask-Login要求）"""
        return True
    
    @property
    def is_anonymous(self):
        """用户是否匿名（Flask-Login要求）"""
        return False
    
    def get_active(self):
        """用户账户是否激活（Flask-Login要求）

        注意：is_active 字段在 MySQL 中是 varchar 类型
        '1' 表示启用，'0' 表示禁用
        """
        return self.is_active == '1' if self.is_active else True

