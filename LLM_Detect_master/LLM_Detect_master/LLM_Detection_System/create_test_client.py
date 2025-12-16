#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速创建测试客户端
"""

from modules.auth import db
from modules.auth.oauth_models import OAuthClient
from app import app

# 创建测试客户端
with app.app_context():
    # 检查是否已存在
    existing = OAuthClient.query.filter_by(client_id='api_test_client_tomato').first()
    if existing:
        print("测试客户端已存在:")
        print(f"Client ID: api_test_client_tomato")
        print(f"Client Secret: api_test_secret_123")
        print(f"客户端名称: {existing.client_name}")
    else:
        # 创建新客户端
        client = OAuthClient(
            client_id='api_test_client_tomato',
            client_name='API测试客户端',
            client_description='用于API测试的客户端',
            contact_person='测试人员',
            contact_email='test@example.com',
            rate_limit=1000,
            allowed_scopes='*',
            created_by='admin',
            is_active='1'
        )
        client.set_client_secret('api_test_secret_123')
        
        db.session.add(client)
        db.session.commit()
        
        print("✅ 测试客户端创建成功!")
        print("=" * 70)
        print("Client ID:     api_test_client_tomato")
        print("Client Secret: api_test_secret_123")
        print("=" * 70)

