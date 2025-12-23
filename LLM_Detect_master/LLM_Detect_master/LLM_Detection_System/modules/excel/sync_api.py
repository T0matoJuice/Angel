#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人工判断数据同步管理API

提供定时同步的状态查询和手动触发功能
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import logging

from modules.excel.scheduler import get_scheduler_manager

logger = logging.getLogger(__name__)

# 创建蓝图
sync_management_bp = Blueprint('sync_management', __name__)


@sync_management_bp.route('/api/sync/status', methods=['GET'])
def get_sync_status():
    """获取同步状态
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "last_sync_time": "2025-01-23 01:00:00",
                "last_sync_status": "success",
                "last_sync_stats": {...},
                "scheduler_running": true,
                "next_run_time": "2025-01-24 01:00:00"
            }
        }
    """
    try:
        scheduler_manager = get_scheduler_manager()
        status = scheduler_manager.get_sync_status()
        
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        logger.error(f"获取同步状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取同步状态失败: {str(e)}"
        }), 500


@sync_management_bp.route('/api/sync/trigger', methods=['POST'])
def trigger_manual_sync():
    """手动触发同步
    
    Request Body (可选):
        {
            "start_date": "2025-01-22",  // 可选，默认为昨天
            "end_date": "2025-01-22"      // 可选，默认为昨天
        }
    
    Returns:
        JSON: {
            "success": true,
            "message": "同步完成",
            "data": {
                "total": 150,
                "updated": 145,
                "not_found": 5,
                "errors": 0
            }
        }
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 如果未指定日期，默认为昨天
        if not start_date or not end_date:
            yesterday = datetime.now() - timedelta(days=1)
            date_str = yesterday.strftime("%Y-%m-%d")
            start_date = start_date or date_str
            end_date = end_date or date_str
        
        # 验证日期格式
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "success": False,
                "message": "日期格式错误，应为 YYYY-MM-DD"
            }), 400
        
        # 执行同步
        scheduler_manager = get_scheduler_manager()
        stats = scheduler_manager.trigger_manual_sync(start_date, end_date)
        
        return jsonify({
            "success": True,
            "message": f"同步完成 ({start_date} ~ {end_date})",
            "data": stats
        })
        
    except Exception as e:
        logger.error(f"手动同步失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"同步失败: {str(e)}"
        }), 500


@sync_management_bp.route('/api/sync/config', methods=['GET'])
def get_sync_config():
    """获取同步配置
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "enabled": true,
                "schedule_hour": 1,
                "schedule_minute": 0
            }
        }
    """
    try:
        from flask import current_app
        
        config = {
            "enabled": current_app.config.get('AUTO_SYNC_ENABLED', True),
            "schedule_hour": current_app.config.get('AUTO_SYNC_HOUR', 1),
            "schedule_minute": current_app.config.get('AUTO_SYNC_MINUTE', 0)
        }
        
        return jsonify({
            "success": True,
            "data": config
        })
    except Exception as e:
        logger.error(f"获取同步配置失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取同步配置失败: {str(e)}"
        }), 500
