#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型智能检测系统 - 集成制图检测和质量工单检测功能
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ⚠️ 重要：在导入任何模块之前先加载环境变量
# 这样可以确保所有模块在导入时都能访问到环境变量
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# 打印环境变量加载状态（便于调试）
print("=" * 60)
print("环境变量加载状态")
print("=" * 60)
print(f"📁 .env 文件路径: {env_path}")
print(f"📁 .env 文件存在: {env_path.exists()}")
print(f"🔑 MOONSHOT_API_KEY: {'已配置 ✅' if os.getenv('MOONSHOT_API_KEY') else '未配置 ❌'}")
print(f"🔑 SILICONFLOW_API_KEY_EXCEL: {'已配置 ✅' if os.getenv('SILICONFLOW_API_KEY_EXCEL') else '未配置 ❌'}")
print("=" * 60)

from flask import Flask
from flask_cors import CORS
from modules.common.config import init_app_config
from modules.auth import init_auth
from modules.auth.routes import auth_bp
from modules.auth.oauth_routes import oauth_bp
from modules.drawing.routes import drawing_bp
from modules.excel.routes import excel_bp
from modules.common.routes import common_bp
from modules.common.dashboard_api import dashboard_api_bp
from modules.api.drawing_api import drawing_api_bp
from modules.api.excel_api import excel_api_bp

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 导入配置
init_app_config(app)

# 初始化认证模块（数据库和登录管理器）
init_auth(app)

# 初始化检测队列管理器（必须在应用上下文中初始化）
from modules.drawing.queue_manager import get_queue_manager
from modules.excel.queue_manager import get_queue_manager as get_excel_queue_manager
with app.app_context():
    drawing_queue_manager = get_queue_manager(app)
    excel_queue_manager = get_excel_queue_manager(app)
    print("✅ Drawing检测队列管理器已初始化")
    print("✅ Excel检测队列管理器已初始化")

# 初始化定时任务调度器（自动同步人工判断数据）
from modules.excel.scheduler import init_scheduler
scheduler_manager = init_scheduler(app)
print("✅ 定时同步任务调度器已初始化")

# 初始化零件数据定时同步调度器
from modules.drawing.scheduler import init_part_scheduler
part_scheduler = init_part_scheduler(app)
print("✅ 零件数据定时同步调度器已初始化")

# 注册蓝图 - Web界面
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(common_bp)
app.register_blueprint(drawing_bp, url_prefix='/drawing')
app.register_blueprint(excel_bp, url_prefix='/excel')

# 注册蓝图 - API接口
app.register_blueprint(oauth_bp, url_prefix='/api/oauth')
app.register_blueprint(dashboard_api_bp)  # 仪表盘API（无前缀，直接/api/dashboard）
app.register_blueprint(drawing_api_bp, url_prefix='/api/v1/drawing')
app.register_blueprint(excel_api_bp, url_prefix='/api/v1/excel')

# 注册同步管理API
from modules.excel.sync_api import sync_management_bp
app.register_blueprint(sync_management_bp)

# 注册零件数据同步管理API
from modules.drawing.sync_api import part_sync_api_bp
app.register_blueprint(part_sync_api_bp)

if __name__ == '__main__':
    print("==== 大模型智能检测系统 ====")
    print("访问地址: http://localhost:5000")
    print("提示：首次运行会自动创建数据库")
    print("=" * 60)

    app.run(debug=False, host='0.0.0.0', port=5000)
