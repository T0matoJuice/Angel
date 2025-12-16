#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OAuth 2.0 路由模块
提供Token端点和客户端管理接口
"""

from flask import Blueprint, request, jsonify
from modules.auth import db
from modules.auth.oauth_models import OAuthClient, OAuthToken
from modules.auth.oauth_utils import generate_access_token
from datetime import datetime

# 创建OAuth蓝图
oauth_bp = Blueprint('oauth', __name__)


@oauth_bp.route('/token', methods=['POST'])
def oauth_token():
    """OAuth 2.0 Token端点

    实现Client Credentials Grant流程

    注意：权限范围检查已禁用，所有Token拥有全部API访问权限

    请求格式:
        POST /api/oauth/token
        Content-Type: application/x-www-form-urlencoded

        grant_type=client_credentials
        client_id=<client_id>
        client_secret=<client_secret>
        scope=* (可选，默认为通配符 * 表示所有权限)

    响应格式:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "Bearer",
            "expires_in": 604800,
            "scopes": ["*"]
        }
    """
    # 1. 获取请求参数
    grant_type = request.form.get('grant_type')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    scope = request.form.get('scope', '')
    
    # 2. 验证grant_type
    if grant_type != 'client_credentials':
        return jsonify({
            'error': 'unsupported_grant_type',
            'error_description': '不支持的授权类型，仅支持 client_credentials'
        }), 400
    
    # 3. 验证必填参数
    if not client_id or not client_secret:
        return jsonify({
            'error': 'invalid_request',
            'error_description': '缺少必填参数: client_id 或 client_secret'
        }), 400
    
    # 4. 查询客户端
    client = OAuthClient.query.filter_by(client_id=client_id).first()
    if not client:
        return jsonify({
            'error': 'invalid_client',
            'error_description': '客户端不存在'
        }), 401
    
    # 5. 验证客户端密钥
    if not client.check_client_secret(client_secret):
        return jsonify({
            'error': 'invalid_client',
            'error_description': '客户端密钥错误'
        }), 401
    
    # 6. 检查客户端是否启用
    if not client.is_enabled():
        return jsonify({
            'error': 'client_disabled',
            'error_description': '客户端已被禁用'
        }), 403
    
    # 7. 解析权限范围（已禁用权限检查）
    # 注意：权限范围检查已禁用，所有Token拥有全部权限
    if scope:
        requested_scopes = [s.strip() for s in scope.split(',')]
    else:
        # 默认授予所有权限
        requested_scopes = ['*']  # 通配符表示所有权限

    # 8. 验证权限范围 - 已禁用
    # 注意：不再验证权限范围，所有请求的scopes都会被授予
    # allowed_scopes = client.allowed_scopes.split(',') if client.allowed_scopes else []
    # for s in requested_scopes:
    #     if s not in allowed_scopes:
    #         return jsonify({
    #             'error': 'invalid_scope',
    #             'error_description': f'客户端没有权限: {s}'
    #         }), 400

    # 9. 生成访问令牌
    try:
        access_token, expires_at = generate_access_token(client_id, requested_scopes)
        
        # 10. 保存Token到数据库
        token_record = OAuthToken(
            access_token=access_token,
            client_id=client_id,
            token_type='Bearer',
            expires_at=expires_at,
            scopes=','.join(requested_scopes),
            is_revoked='0'
        )
        db.session.add(token_record)
        db.session.commit()
        
        # 11. 返回Token响应
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 604800,  # 7天 = 604800秒 (168小时 × 3600秒)
            'scopes': requested_scopes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'error_description': f'生成Token失败: {str(e)}'
        }), 500


@oauth_bp.route('/revoke', methods=['POST'])
def oauth_revoke():
    """撤销访问令牌
    
    请求格式:
        POST /api/oauth/revoke
        Content-Type: application/x-www-form-urlencoded
        
        token=<access_token>
        client_id=<client_id>
        client_secret=<client_secret>
    
    响应格式:
        {
            "success": true,
            "message": "Token已撤销"
        }
    """
    # 1. 获取请求参数
    token = request.form.get('token')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    
    # 2. 验证必填参数
    if not token or not client_id or not client_secret:
        return jsonify({
            'error': 'invalid_request',
            'error_description': '缺少必填参数'
        }), 400
    
    # 3. 验证客户端
    client = OAuthClient.query.filter_by(client_id=client_id).first()
    if not client or not client.check_client_secret(client_secret):
        return jsonify({
            'error': 'invalid_client',
            'error_description': '客户端认证失败'
        }), 401
    
    # 4. 查询Token
    token_record = OAuthToken.query.filter_by(
        access_token=token,
        client_id=client_id
    ).first()
    
    if not token_record:
        # RFC 7009: 即使Token不存在，也应该返回成功
        return jsonify({
            'success': True,
            'message': 'Token已撤销'
        }), 200
    
    # 5. 撤销Token
    try:
        token_record.revoke()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Token已撤销'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'error_description': f'撤销Token失败: {str(e)}'
        }), 500

