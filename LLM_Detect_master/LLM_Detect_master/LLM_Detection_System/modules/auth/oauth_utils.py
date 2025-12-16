#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OAuth 2.0 工具函数
提供JWT生成、验证、频率限制等功能
"""

import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from modules.auth import db
from modules.auth.oauth_models import OAuthClient, OAuthToken, APICallLog, APIRateLimit


# JWT配置
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 168  # Token有效期：7天（168小时）


def generate_access_token(client_id, scopes=None):
    """生成JWT访问令牌

    Args:
        client_id: 客户端ID
        scopes: 授权范围列表（已禁用权限检查，此参数仅用于记录）

    Returns:
        str: JWT访问令牌

    注意：权限范围检查已禁用，所有Token拥有全部权限
    """
    if scopes is None:
        scopes = ['*']  # 通配符，表示所有权限
    
    # 计算过期时间
    now = datetime.now()
    expires_at = now + timedelta(hours=JWT_EXPIRATION_HOURS)

    # JWT payload (exp和iat必须是Unix时间戳)
    payload = {
        'client_id': client_id,
        'scopes': scopes,
        'exp': int(expires_at.timestamp()),
        'iat': int(now.timestamp()),
        'type': 'access_token'
    }

    # 生成JWT
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return token, expires_at


def verify_access_token(token):
    """验证JWT访问令牌
    
    Args:
        token: JWT访问令牌
    
    Returns:
        dict: 解码后的payload，如果验证失败返回None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token已过期
    except jwt.InvalidTokenError:
        return None  # Token无效


def check_rate_limit(client_id, rate_limit=100):
    """检查API频率限制（滑动窗口算法）
    
    Args:
        client_id: 客户端ID
        rate_limit: 每小时请求限制
    
    Returns:
        tuple: (是否允许, 剩余次数, 重置时间)
    """
    # 当前小时的窗口开始时间
    now = datetime.now()
    window_start = now.replace(minute=0, second=0, microsecond=0)
    
    # 查询或创建频率限制记录
    rate_record = APIRateLimit.query.filter_by(
        client_id=client_id,
        window_start=window_start
    ).first()
    
    if not rate_record:
        # 创建新记录
        rate_record = APIRateLimit(
            client_id=client_id,
            window_start=window_start,
            request_count=1
        )
        db.session.add(rate_record)
        db.session.commit()
        
        remaining = rate_limit - 1
        reset_time = window_start + timedelta(hours=1)
        return True, remaining, reset_time
    
    # 检查是否超过限制
    if rate_record.request_count >= rate_limit:
        reset_time = window_start + timedelta(hours=1)
        return False, 0, reset_time
    
    # 增加计数
    rate_record.request_count += 1
    db.session.commit()
    
    remaining = rate_limit - rate_record.request_count
    reset_time = window_start + timedelta(hours=1)
    return True, remaining, reset_time


def log_api_call(client_id, endpoint, method, status_code, request_ip, 
                 request_params=None, response_time=None, error_message=None):
    """记录API调用日志
    
    Args:
        client_id: 客户端ID
        endpoint: API端点
        method: HTTP方法
        status_code: HTTP状态码
        request_ip: 请求IP
        request_params: 请求参数（JSON字符串）
        response_time: 响应时间（毫秒）
        error_message: 错误信息
    """
    try:
        log = APICallLog(
            client_id=client_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            request_ip=request_ip,
            request_params=request_params,
            response_time=response_time,
            error_message=error_message
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"记录API调用日志失败: {str(e)}")
        db.session.rollback()


def require_oauth(scopes=None):
    """OAuth 2.0认证装饰器

    用于保护API端点，要求请求必须包含有效的访问令牌

    Args:
        scopes: 需要的权限范围列表（已禁用，保留参数仅为向后兼容）

    注意：权限范围检查已禁用，所有有效Token可访问所有API接口

    Usage:
        @require_oauth()  # scopes参数可省略
        def upload_api():
            # 可以通过 request.oauth_client 访问客户端信息
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 记录开始时间
            start_time = datetime.now()
            
            # 1. 获取Authorization头
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({
                    'error': 'missing_authorization',
                    'error_description': '缺少Authorization头'
                }), 401
            
            # 2. 解析Bearer Token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({
                    'error': 'invalid_authorization',
                    'error_description': 'Authorization头格式错误，应为: Bearer <token>'
                }), 401
            
            token = parts[1]
            
            # 3. 验证JWT
            payload = verify_access_token(token)
            if not payload:
                return jsonify({
                    'error': 'invalid_token',
                    'error_description': 'Token无效或已过期'
                }), 401
            
            client_id = payload.get('client_id')
            token_scopes = payload.get('scopes', [])
            
            # 4. 检查Token是否在数据库中且未被撤销
            token_record = OAuthToken.query.filter_by(access_token=token).first()
            if token_record and not token_record.is_valid():
                return jsonify({
                    'error': 'token_revoked',
                    'error_description': 'Token已被撤销或过期'
                }), 401
            
            # 5. 检查客户端是否存在且启用
            client = OAuthClient.query.filter_by(client_id=client_id).first()
            if not client or not client.is_enabled():
                return jsonify({
                    'error': 'client_disabled',
                    'error_description': '客户端不存在或已被禁用'
                }), 403

            # 6. 检查权限范围 - 已禁用
            # 注意：权限范围检查已被移除，所有有效Token可访问所有API
            # if scopes:
            #     for scope in scopes:
            #         if scope not in token_scopes:
            #             return jsonify({
            #                 'error': 'insufficient_scope',
            #                 'error_description': f'缺少必要的权限: {scope}'
            #             }), 403

            # 7. 检查频率限制
            allowed, remaining, reset_time = check_rate_limit(client_id, client.rate_limit)
            if not allowed:
                return jsonify({
                    'error': 'rate_limit_exceeded',
                    'error_description': f'超过频率限制，请在 {reset_time.strftime("%Y-%m-%d %H:%M:%S")} 后重试'
                }), 429
            
            # 8. 更新Token最后使用时间
            if token_record:
                token_record.update_last_used()
                db.session.commit()
            
            # 9. 将客户端信息附加到request对象
            request.oauth_client = client
            request.oauth_scopes = token_scopes
            
            # 10. 执行被装饰的函数
            try:
                response = f(*args, **kwargs)
                
                # 记录成功的API调用
                end_time = datetime.now()
                response_time = int((end_time - start_time).total_seconds() * 1000)
                
                status_code = response[1] if isinstance(response, tuple) else 200
                log_api_call(
                    client_id=client_id,
                    endpoint=request.path,
                    method=request.method,
                    status_code=status_code,
                    request_ip=request.remote_addr,
                    response_time=response_time
                )
                
                return response
                
            except Exception as e:
                # 记录失败的API调用
                end_time = datetime.now()
                response_time = int((end_time - start_time).total_seconds() * 1000)
                
                log_api_call(
                    client_id=client_id,
                    endpoint=request.path,
                    method=request.method,
                    status_code=500,
                    request_ip=request.remote_addr,
                    response_time=response_time,
                    error_message=str(e)
                )
                
                raise
        
        return decorated_function
    return decorator

