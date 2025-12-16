#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证模块初始化
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# 初始化数据库和登录管理器
db = SQLAlchemy()
login_manager = LoginManager()

def init_auth(app):
    """初始化认证模块
    
    Args:
        app: Flask应用实例
    """
    # 初始化数据库
    db.init_app(app)
    
    # 初始化登录管理器
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # 未登录时跳转的视图
    login_manager.login_message = '请先登录后再访问该页面'
    login_manager.login_message_category = 'warning'
    
    # 导入User模型（避免循环导入）
    from modules.auth.models import User

    @login_manager.user_loader
    def load_user(user_id):
        """加载用户回调函数"""
        return User.query.get(int(user_id))

    # 注意：使用现有的 MySQL 数据库表，不需要自动创建表
    # 如果需要创建新表，取消下面的注释
    # with app.app_context():
    #     db.create_all()
    #     print("✅ 数据库表创建成功")

    print("✅ 认证模块初始化成功（使用 MySQL angel.user 表）")

