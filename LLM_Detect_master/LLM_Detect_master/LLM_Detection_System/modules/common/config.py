#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共配置模块
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def init_app_config(app):
    """初始化Flask应用配置"""

    # 加载环境变量（API密钥等）
    # 使用绝对路径确保无论从哪个目录启动都能找到 .env 文件
    # base_dir 指向项目根目录（LLM_Detect_master），而不是 LLM_Detection_System
    # 因为 uploads/results/history 等目录都在项目根目录下
    base_dir = Path(__file__).resolve().parent.parent.parent.parent  # 多加一层 parent
    env_path = base_dir / 'LLM_Detection_System' / '.env'  # .env 文件在 LLM_Detection_System 下

    # 再次加载环境变量（确保配置已加载）
    load_dotenv(env_path)

    # 验证关键环境变量是否已加载
    if not os.getenv('MOONSHOT_API_KEY'):
        print("⚠️  警告: MOONSHOT_API_KEY 未配置，工程制图检测功能将无法使用")

    if not os.getenv('SILICONFLOW_API_KEY_EXCEL'):
        print("⚠️  警告: SILICONFLOW_API_KEY_EXCEL 未配置，Excel工单处理功能将无法使用")

    # 配置文件上传（使用绝对路径，确保无论从哪个目录启动都能正确访问）
    UPLOAD_FOLDER = os.path.join(base_dir, 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # 配置历史记录存储
    HISTORY_FOLDER = os.path.join(base_dir, 'history')
    if not os.path.exists(HISTORY_FOLDER):
        os.makedirs(HISTORY_FOLDER)

    # 配置结果文件存储
    RESULTS_FOLDER = os.path.join(base_dir, 'results')
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['HISTORY_FOLDER'] = HISTORY_FOLDER
    app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 限制文件大小50MB
    app.config['MAX_HISTORY_RECORDS'] = 10  # 最大历史记录数
    app.config['JSON_AS_ASCII'] = False

    # 数据库配置 - MySQL
    # 格式：mysql+pymysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Angel#20251204@10.2.32.162:3306/angel?charset=utf8mb4'
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # app.config['SQLALCHEMY_ECHO'] = False  # 设置为True可以看到SQL语句（调试用）

    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'default_password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'test_db')
    # 调试打印：检查到底读到了什么 (启动后看 docker logs aje1)
    print(f"DEBUG: Connecting to {DB_USER}@{DB_HOST}/{DB_NAME}")
    # 格式：mysql+pymysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False  # 设置为True可以看到SQL语句（调试用）
    
    # 数据库连接池配置（提高并发处理能力）
    app.config['SQLALCHEMY_POOL_SIZE'] = 20  # 连接池大小
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = 30  # 超出连接池大小的最大连接数
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30  # 获取连接的超时时间（秒）
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600  # 连接回收时间（秒），避免MySQL连接超时
    app.config['SQLALCHEMY_POOL_PRE_PING'] = True  # 连接前先ping，确保连接有效

    # 会话配置（用于Flask-Login）
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 会话有效期：24小时
