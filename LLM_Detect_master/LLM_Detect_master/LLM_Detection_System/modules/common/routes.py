#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共路由模块
"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required

# 创建公共路由蓝图
common_bp = Blueprint('common', __name__)

@common_bp.route('/')
@login_required
def index():
    """集成系统主页 - 新版仪表盘（带统计数据）"""
    return render_template('mainPage.html')

@common_bp.route('/old')
@login_required
def old_index():
    """旧版主页 - 简单入口页面（备份）"""
    return render_template('index.html')

@common_bp.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': '大模型智能检测系统运行正常'})
