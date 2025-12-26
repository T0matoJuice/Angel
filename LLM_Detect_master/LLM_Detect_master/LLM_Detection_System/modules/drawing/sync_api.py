#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零件数据同步管理API

提供零件数据同步的手动触发和状态查询接口
"""

from flask import Blueprint, jsonify, request
from modules.drawing.scheduler import get_part_scheduler
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
part_sync_api_bp = Blueprint('part_sync_api', __name__, url_prefix='/api/part-sync')


@part_sync_api_bp.route('/status', methods=['GET'])
def get_sync_status():
    """获取零件数据同步状态
    
    Returns:
        JSON: {
            "success": bool,
            "data": {
                "last_sync_time": str,
                "last_sync_status": str,
                "last_sync_stats": dict,
                "scheduler_running": bool,
                "next_run_time": str
            }
        }
    """
    try:
        scheduler = get_part_scheduler()
        status = scheduler.get_sync_status()
        
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@part_sync_api_bp.route('/trigger', methods=['POST'])
def trigger_sync():
    """手动触发零件数据同步
    
    Returns:
        JSON: {
            "success": bool,
            "data": {
                "total": int,
                "inserted": int,
                "updated": int,
                "skipped": int,
                "errors": int
            }
        }
    """
    try:
        scheduler = get_part_scheduler()
        stats = scheduler.trigger_manual_sync()
        
        if stats:
            return jsonify({
                "success": True,
                "message": "同步完成",
                "data": stats
            })
        else:
            return jsonify({
                "success": False,
                "message": "同步失败"
            }), 500
            
    except Exception as e:
        logger.error(f"触发同步失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@part_sync_api_bp.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    """启动调度器
    
    Request Body:
        {
            "hour": int,  # 可选，默认3
            "minute": int  # 可选，默认0
        }
    
    Returns:
        JSON: {"success": bool, "message": str}
    """
    try:
        data = request.get_json() or {}
        hour = data.get('hour', 3)
        minute = data.get('minute', 0)
        
        scheduler = get_part_scheduler()
        scheduler.start_scheduler(hour, minute)
        
        return jsonify({
            "success": True,
            "message": f"调度器已启动，每天 {hour:02d}:{minute:02d} 执行"
        })
    except Exception as e:
        logger.error(f"启动调度器失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@part_sync_api_bp.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """停止调度器
    
    Returns:
        JSON: {"success": bool, "message": str}
    """
    try:
        scheduler = get_part_scheduler()
        scheduler.stop_scheduler()
        
        return jsonify({
            "success": True,
            "message": "调度器已停止"
        })
    except Exception as e:
        logger.error(f"停止调度器失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
