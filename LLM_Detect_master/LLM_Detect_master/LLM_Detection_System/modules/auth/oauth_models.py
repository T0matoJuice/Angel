#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OAuth 2.0 数据模型
用于工程制图检测模块的外部API访问控制
"""

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from modules.auth import db
import secrets
import uuid


class OAuthClient(db.Model):
    """OAuth客户端模型 - 存储外部客户端的认证信息
    
    Attributes:
        id: 客户端ID（主键，自增）
        client_id: 客户端标识符（UUID）
        client_secret: 客户端密钥（加密存储）
        client_name: 客户端名称
        client_description: 客户端描述
        contact_email: 联系邮箱
        contact_person: 联系人
        is_active: 是否启用
        created_at: 创建时间
        updated_at: 更新时间
        created_by: 创建者
        rate_limit: 每小时请求限制
        allowed_scopes: 允许的权限范围
    """
    __tablename__ = 'oauth_clients'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    client_secret = db.Column(db.String(255), nullable=False)  # 存储加密后的密钥
    client_name = db.Column(db.String(255), nullable=False)
    client_description = db.Column(db.Text, nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_person = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.String(10), default='1')  # '1'=启用，'0'=禁用
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.String(255), nullable=True)
    rate_limit = db.Column(db.Integer, default=100)  # 每小时请求限制
    allowed_scopes = db.Column(db.String(500), default='drawing:upload,drawing:inspect,drawing:query')
    
    # 关联关系
    tokens = db.relationship('OAuthToken', backref='client', lazy='dynamic', cascade='all, delete-orphan')
    api_logs = db.relationship('APICallLog', backref='client', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<OAuthClient {self.client_name}>'
    
    @staticmethod
    def generate_client_id():
        """生成唯一的客户端ID"""
        return f"client_{uuid.uuid4().hex}"
    
    @staticmethod
    def generate_client_secret():
        """生成随机的客户端密钥（明文，用于返回给用户）"""
        return f"secret_{secrets.token_urlsafe(32)}"
    
    def set_client_secret(self, secret_text):
        """设置客户端密钥（加密存储）"""
        self.client_secret = generate_password_hash(secret_text)
    
    def check_client_secret(self, secret_text):
        """验证客户端密钥"""
        return check_password_hash(self.client_secret, secret_text)
    
    def is_enabled(self):
        """检查客户端是否启用"""
        return self.is_active == '1'
    
    def to_dict(self, include_secret=False):
        """转换为字典（用于API响应）"""
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client_name,
            'client_description': self.client_description,
            'contact_email': self.contact_email,
            'contact_person': self.contact_person,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'rate_limit': self.rate_limit,
            'allowed_scopes': self.allowed_scopes.split(',') if self.allowed_scopes else []
        }
        # 注意：client_secret 不应该在API响应中返回
        return data


class OAuthToken(db.Model):
    """OAuth访问令牌模型 - 存储已颁发的访问令牌
    
    Attributes:
        id: 令牌ID（主键，自增）
        access_token: 访问令牌（JWT）
        client_id: 客户端标识符
        token_type: 令牌类型
        expires_at: 过期时间
        scopes: 授权范围
        is_revoked: 是否已撤销
        created_at: 创建时间
        last_used_at: 最后使用时间
    """
    __tablename__ = 'oauth_tokens'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    access_token = db.Column(db.String(500), nullable=False, unique=True, index=True)
    client_id = db.Column(db.String(255), db.ForeignKey('oauth_clients.client_id'), nullable=False, index=True)
    token_type = db.Column(db.String(50), default='Bearer')
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    scopes = db.Column(db.String(500), nullable=True)
    is_revoked = db.Column(db.String(10), default='0', index=True)  # '1'=已撤销，'0'=有效
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<OAuthToken {self.access_token[:20]}...>'
    
    def is_valid(self):
        """检查令牌是否有效（未过期且未撤销）"""
        return (
            self.is_revoked == '0' and
            self.expires_at > datetime.now()
        )
    
    def revoke(self):
        """撤销令牌"""
        self.is_revoked = '1'
    
    def update_last_used(self):
        """更新最后使用时间"""
        self.last_used_at = datetime.now()
    
    def to_dict(self):
        """转换为字典（用于API响应）"""
        return {
            'access_token': self.access_token,
            'token_type': self.token_type,
            'expires_in': int((self.expires_at - datetime.now()).total_seconds()),
            'scopes': self.scopes.split(',') if self.scopes else []
        }


class APICallLog(db.Model):
    """API调用日志模型 - 记录所有API调用
    
    Attributes:
        id: 日志ID（主键，自增）
        client_id: 客户端标识符
        endpoint: API端点
        method: HTTP方法
        status_code: HTTP状态码
        request_ip: 请求IP地址
        request_params: 请求参数
        response_time: 响应时间（毫秒）
        error_message: 错误信息
        created_at: 调用时间
    """
    __tablename__ = 'api_call_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.String(255), db.ForeignKey('oauth_clients.client_id'), nullable=False, index=True)
    endpoint = db.Column(db.String(255), nullable=False, index=True)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=True)
    request_ip = db.Column(db.String(50), nullable=True)
    request_params = db.Column(db.Text, nullable=True)
    response_time = db.Column(db.Integer, nullable=True)  # 毫秒
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f'<APICallLog {self.endpoint} - {self.status_code}>'


class APIRateLimit(db.Model):
    """API频率限制模型 - 用于实现滑动窗口频率限制
    
    Attributes:
        id: ID（主键，自增）
        client_id: 客户端标识符
        window_start: 时间窗口开始时间
        request_count: 请求次数
        created_at: 创建时间
        updated_at: 更新时间
    """
    __tablename__ = 'api_rate_limits'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.String(255), db.ForeignKey('oauth_clients.client_id'), nullable=False, index=True)
    window_start = db.Column(db.DateTime, nullable=False, index=True)
    request_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('client_id', 'window_start', name='unique_client_window'),
    )
    
    def __repr__(self):
        return f'<APIRateLimit {self.client_id} - {self.request_count}>'

