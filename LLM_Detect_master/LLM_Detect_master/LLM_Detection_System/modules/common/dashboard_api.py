#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主页仪表盘API - 提供统计数据和最近记录（优化版）
"""

from flask import Blueprint, jsonify
from sqlalchemy import func
from datetime import datetime

# 创建仪表盘API蓝图
dashboard_api_bp = Blueprint('dashboard_api', __name__)


@dashboard_api_bp.route('/api/dashboard/statistics', methods=['GET'])
def get_statistics():
    """获取系统统计数据
    
    Returns:
        JSON: 包含本月检测次数、历史总次数、图纸符合率、工单问题比例
    """
    # 默认值
    default_data = {
        'monthlyCount': 0,
        'totalCount': 0,
        'drawingRate': 0.0,
        'issueRate': 0.0
    }
    
    try:
        from modules.auth import db
        from modules.drawing.models import DrawingData
        from modules.excel.models import WorkorderData
        
        # 获取当前年月
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        print(f"[DEBUG] 开始查询统计数据: {current_year}-{current_month:02d}")
        
        # 1. 本月检测次数（制图 + 工单）
        drawing_monthly = 0
        workorder_monthly = 0
        
        try:
            drawing_monthly = db.session.query(func.count(DrawingData.id)).filter(
                DrawingData.created_at.like(f'{current_year}-{current_month:02d}%')
            ).scalar() or 0
            print(f"[DEBUG] 制图月度数据: {drawing_monthly}")
        except Exception as e:
            print(f"[ERROR] 查询制图月度数据错误: {e}")
        
        try:
            workorder_monthly = db.session.query(func.count(func.distinct(WorkorderData.filename))).filter(
                WorkorderData.datatime.like(f'{current_year}-{current_month:02d}%')
            ).scalar() or 0
            print(f"[DEBUG] 工单月度数据: {workorder_monthly}")
        except Exception as e:
            print(f"[ERROR] 查询工单月度数据错误: {e}")
        
        monthly_count = drawing_monthly + workorder_monthly
        
        # 2. 历史总检测次数
        drawing_total = 0
        workorder_total = 0
        
        try:
            drawing_total = db.session.query(func.count(DrawingData.id)).scalar() or 0
            print(f"[DEBUG] 制图总数: {drawing_total}")
        except Exception as e:
            print(f"[ERROR] 查询制图总数错误: {e}")
            
        try:
            workorder_total = db.session.query(func.count(func.distinct(WorkorderData.filename))).scalar() or 0
            print(f"[DEBUG] 工单总数: {workorder_total}")
        except Exception as e:
            print(f"[ERROR] 查询工单总数错误: {e}")
            
        total_count = drawing_total + workorder_total
        
        # 3. 图纸符合率（conclusion='符合'的比例）
        drawing_rate = 0.0
        try:
            completed_drawings = db.session.query(func.count(DrawingData.id)).filter(
                DrawingData.status == 'completed'
            ).scalar() or 0
            
            if completed_drawings > 0:
                # 统计conclusion='符合'的图纸数量
                compliant_drawings = db.session.query(func.count(DrawingData.id)).filter(
                    DrawingData.status == 'completed',
                    DrawingData.conclusion == '符合'
                ).scalar() or 0
                drawing_rate = round((compliant_drawings / completed_drawings) * 100, 1)
            print(f"[DEBUG] 图纸符合率: {drawing_rate}% (符合: {compliant_drawings if completed_drawings > 0 else 0}/{completed_drawings})")
        except Exception as e:
            print(f"[ERROR] 查询图纸符合率错误: {e}")
        
        # 4. 工单问题比例（非质量工单占总工单的比例）
        issue_rate = 0.0
        try:
            total_workorders = db.session.query(func.count(WorkorderData.id)).scalar() or 0
            
            if total_workorders > 0:
                # 统计非质量工单数量（workOrderNature != '质量问题'）
                non_quality_issues = db.session.query(func.count(WorkorderData.id)).filter(
                    WorkorderData.workOrderNature != '质量问题'
                ).scalar() or 0
                issue_rate = round((non_quality_issues / total_workorders) * 100, 1)
            print(f"[DEBUG] 工单问题比例: {issue_rate}% (非质量工单: {non_quality_issues if total_workorders > 0 else 0}/{total_workorders})")
        except Exception as e:
            print(f"[ERROR] 查询工单问题比例错误: {e}")
        
        result_data = {
            'monthlyCount': monthly_count,
            'totalCount': total_count,
            'drawingRate': drawing_rate,
            'issueRate': issue_rate
        }
        
        print(f"[DEBUG] 统计数据查询成功: {result_data}")
        
        return jsonify({
            'success': True,
            'data': result_data
        })
        
    except Exception as e:
        print(f"[ERROR] 获取统计数据失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 返回默认数据
        return jsonify({
            'success': True,
            'data': default_data,
            'warning': '数据库查询失败，显示默认值'
        })


@dashboard_api_bp.route('/api/dashboard/recent-records', methods=['GET'])
def get_recent_records():
    """获取最近的检测记录
    
    Returns:
        JSON: 最近5条检测记录列表
    """
    try:
        from modules.auth import db
        from modules.drawing.models import DrawingData
        from modules.excel.models import WorkorderData
        
        print("[DEBUG] 开始查询最近记录")
        records = []
        
        # 获取最近3条制图检测记录
        try:
            recent_drawings = DrawingData.query.order_by(
                DrawingData.created_at.desc()
            ).limit(3).all()
            
            for drawing in recent_drawings:
                records.append({
                    'time': drawing.created_at or '',
                    'type': '工程制图检测',
                    'detail': drawing.original_filename or '未知文件',
                    'status': drawing.status or 'unknown'
                })
            print(f"[DEBUG] 查询到 {len(recent_drawings)} 条制图记录")
        except Exception as e:
            print(f"[ERROR] 查询制图记录失败: {e}")
        
        # 获取最近2批工单检测记录
        try:
            # 使用MAX聚合函数获取每个filename的最新时间，符合ONLY_FULL_GROUP_BY要求
            recent_workorders = db.session.query(
                func.max(WorkorderData.datatime).label('datatime'),
                WorkorderData.filename,
                func.count(WorkorderData.id).label('count')
            ).group_by(
                WorkorderData.filename
            ).order_by(
                func.max(WorkorderData.datatime).desc()
            ).limit(2).all()
            
            for workorder in recent_workorders:
                records.append({
                    'time': workorder.datatime or '',
                    'type': '质量工单判定',
                    'detail': f'{workorder.filename} ({workorder.count}条)',
                    'status': 'completed'
                })
            print(f"[DEBUG] 查询到 {len(recent_workorders)} 批工单记录")
        except Exception as e:
            print(f"[ERROR] 查询工单记录失败: {e}")
        
        # 按时间排序
        if records:
            records.sort(key=lambda x: x['time'], reverse=True)
            records = records[:5]
        
        print(f"[DEBUG] 最近记录查询完成，共 {len(records)} 条")
        
        return jsonify({
            'success': True,
            'data': records
        })
        
    except Exception as e:
        print(f"[ERROR] 获取最近记录失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 返回空列表
        return jsonify({
            'success': True,
            'data': [],
            'warning': '数据库查询失败，暂无记录'
        })


@dashboard_api_bp.route('/api/dashboard/user-info', methods=['GET'])
def get_user_info():
    """获取当前用户信息
    
    Returns:
        JSON: 用户名等信息
    """
    try:
        from flask_login import current_user
        
        if current_user.is_authenticated:
            return jsonify({
                'success': True,
                'data': {
                    'username': current_user.username,
                    'isAuthenticated': True
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'username': '访客',
                    'isAuthenticated': False
                }
            })
            
    except Exception as e:
        print(f"[ERROR] 获取用户信息失败: {e}")
        return jsonify({
            'success': True,
            'data': {
                'username': '访客',
                'isAuthenticated': False
            }
        })
