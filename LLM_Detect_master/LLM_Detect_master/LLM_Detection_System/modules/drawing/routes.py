#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
制图检测路由模块 - 提供机械制图规范检测功能的Web路由和API接口
"""

import os
import time
import glob
import tempfile
from flask import Blueprint, request, jsonify, render_template, send_file, current_app
from flask_login import login_required, current_user
from modules.drawing.utils import allowed_file, convert_pdf_to_image, create_placeholder_image
from modules.drawing.services import inspect_drawing_api
from modules.drawing.models import DrawingData
from modules.drawing.queue_manager import get_queue_manager
from modules.auth import db

# 创建制图检测蓝图
drawing_bp = Blueprint('drawing', __name__)


@drawing_bp.route('/')
@login_required
def drawing_index():
    """制图检测系统主页 - 显示制图检测功能介绍和操作入口"""
    return render_template('drawing_index.html')


@drawing_bp.route('/detection')
@login_required
def drawing_detection():
    """制图检测页面 - 提供PDF文件上传和智能制图规范检测功能"""
    return render_template('drawing_detection.html')


@drawing_bp.route('/textbook')
@login_required
def drawing_textbook():
    # 1. 基础路径配置
    base_dir = os.path.join(current_app.root_path, "data")
    search_pattern = os.path.join(base_dir, "*机械制图教材*.pdf")
    found_files = glob.glob(search_pattern)

    print(f"搜索模式: {search_pattern}")
    print(f"找到的文件: {found_files}")

    if found_files:
        # --- 成功分支 ---
        target_file = found_files[0]
        # 【关键修正】：return 必须在 if 里面，也就是要有缩进
        return send_file(target_file, as_attachment=False)
    else:
        # --- 失败分支 ---
        # 只有上面的 if 执行完没进入，才会来到这里
        if os.path.exists(base_dir):
            print(f"目录 {base_dir} 下的所有文件: {os.listdir(base_dir)}")

        return jsonify({'error': '未找到包含[机械制图教材]的PDF文件'}), 404


@drawing_bp.route('/history')
@login_required
def drawing_history():
    """制图检测历史记录页面 - 显示用户的制图检测历史记录和详细结果"""
    return render_template('drawing_history.html')


@drawing_bp.route('/api/history')
@login_required
def drawing_get_history():
    """获取制图检测历史记录API - 从 MySQL 数据库读取

    显示所有检测记录（包括Web界面和API接口创建的记录）
    """
    try:
        # 从数据库查询所有检测记录，按创建时间倒序排列
        # 移除了 filter_by(account=current_user.username) 过滤条件，显示所有记录
        records = DrawingData.query.order_by(DrawingData.id.desc()).all()

        # 转换为字典列表，并添加来源标识
        history_records = []
        for record in records:
            record_dict = record.to_dict()

            # 添加来源标识字段
            # 判断逻辑：如果account字段包含"api"、"client"等关键词，或者以特定前缀开头，则认为是API来源
            account = record.account or ''
            if 'api' in account.lower() or 'client' in account.lower() or account.startswith('api_'):
                record_dict['source'] = 'API接口'
                record_dict['source_type'] = 'api'
            else:
                record_dict['source'] = 'Web界面'
                record_dict['source_type'] = 'web'

            history_records.append(record_dict)

        return jsonify({
            'success': True,
            'records': history_records,
            'total': len(history_records)
        })
    except Exception as e:
        return jsonify({'error': f'获取历史记录失败: {str(e)}'}), 500


@drawing_bp.route('/api/history/<record_id>')
@login_required
def drawing_get_history_detail(record_id):
    """获取制图检测历史记录详情 - 从 MySQL 数据库读取

    Args:
        record_id (str): 历史记录的唯一标识符（engineering_drawing_id）

    Returns:
        JSON: 包含历史记录详细信息的响应数据
    """
    try:
        # 从数据库查询指定 ID 的记录（使用自增ID）
        # 移除了 account 过滤条件，允许查看所有记录的详情
        record = DrawingData.query.filter_by(id=int(record_id)).first()

        if not record:
            return jsonify({'error': '历史记录不存在'}), 404

        # 转换为字典并添加来源标识
        record_dict = record.to_dict()

        # 添加来源标识字段
        account = record.account or ''
        if 'api' in account.lower() or 'client' in account.lower() or account.startswith('api_'):
            record_dict['source'] = 'API接口'
            record_dict['source_type'] = 'api'
        else:
            record_dict['source'] = 'Web界面'
            record_dict['source_type'] = 'web'

        return jsonify({
            'success': True,
            'record': record_dict
        })

    except Exception as e:
        return jsonify({'error': f'获取历史记录详情失败: {str(e)}'}), 500


@drawing_bp.route('/upload', methods=['POST'])
@login_required
def drawing_upload_file():
    """制图检测 - PDF文件上传接口 - 上传后立即创建数据库记录并加入检测队列

    新流程：
    1. 验证文件和参数
    2. 保存文件到uploads目录
    3. 立即创建数据库记录（状态：pending）
    4. 将检测任务加入队列
    5. 返回record_id供前端轮询状态
    """
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '只支持PDF文件格式'}), 400

    # 获取图纸文档编号、检入者、版本和图纸类型信息
    engineering_drawing_id = request.form.get('engineering_drawing_id', '').strip()
    checker_name = request.form.get('checker_name', '').strip()
    version = request.form.get('version', '').strip()
    drawing_type = request.form.get('drawing_type', '').strip()

    # 验证必填字段
    if not engineering_drawing_id:
        return jsonify({'error': '图纸文档编号不能为空'}), 400
    if not checker_name:
        return jsonify({'error': '检入者不能为空'}), 400
    if not version:
        return jsonify({'error': '版本不能为空'}), 400
    if not drawing_type:
        return jsonify({'error': '图纸类型不能为空'}), 400

    try:
        # 1. 保存文件到uploads目录
        timestamp = int(time.time() * 1000)  # 使用毫秒时间戳
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 2. 使用用户输入的图纸文档编号作为检测记录ID（已从表单获取）
        # engineering_drawing_id 已在上面定义

        # 3. 立即创建数据库记录（状态：pending）
        drawing_record = DrawingData(
            engineering_drawing_id=engineering_drawing_id,
            account=current_user.username,
            original_filename=file.filename,
            file_path=filepath,
            checker_name=checker_name,
            version=version,
            engineering_drawing_type=drawing_type,
            created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            status='pending',  # 初始状态：排队中
            conclusion='',  # 检测结论暂时为空
            detailed_report='',  # 详细报告暂时为空
            source='Web'  # 数据来源：Web界面
        )

        db.session.add(drawing_record)
        db.session.commit()

        # 获取数据库自增ID
        db_record_id = drawing_record.id

        print(f"✅ 数据库记录已创建: ID={db_record_id}, engineering_drawing_id={engineering_drawing_id}")
        print(f"   文件: {file.filename}, 检入者: {checker_name}, 版本: {version}")

        # 4. 将检测任务加入队列（使用数据库ID）
        queue_manager = get_queue_manager()
        queue_added = queue_manager.add_task(str(db_record_id), filepath)

        if not queue_added:
            return jsonify({
                'error': '任务加入队列失败，请重试'
            }), 500

        # 5. 返回成功响应
        return jsonify({
            'success': True,
            'record_id': str(db_record_id),  # 返回数据库ID供前端轮询
            'engineering_drawing_id': engineering_drawing_id,  # 同时返回图纸编号
            'filename': file.filename,
            'message': 'PDF文件上传成功，检测任务已加入队列',
            'preview_url': f'/drawing/preview/{filename}',
            'checker_name': checker_name,
            'version': version,
            'status': 'pending'  # 当前状态
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ 上传失败: {str(e)}")
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


@drawing_bp.route('/inspect', methods=['POST'])
@login_required
def drawing_inspect():
    """制图检测 - AI智能检测接口（已废弃，由队列自动处理）

    注意：此接口已被队列机制取代，上传后会自动检测
    保留此接口仅为兼容性，实际不再使用
    """
    return jsonify({
        'error': 'deprecated',
        'message': '此接口已废弃，上传后会自动开始检测，请使用 /api/status/<record_id> 查询检测状态'
    }), 410  # 410 Gone - 资源已不再可用


@drawing_bp.route('/api/status/<record_id>', methods=['GET'])
@login_required
def drawing_get_status(record_id):
    """查询检测任务状态

    Args:
        record_id: 检测记录ID（数据库自增ID）

    Returns:
        JSON: {
            "success": true,
            "record_id": "123",
            "engineering_drawing_id": "DWG-001",
            "status": "pending|processing|completed|failed",
            "conclusion": "符合",  // 仅当 status=completed 时有值
            "detailed_report": "...",  // 仅当 status=completed 时有值
            "error_message": "...",  // 仅当 status=failed 时有值
            "queue_position": 3  // 仅当 status=pending 时有值
        }
    """
    try:
        # 从数据库查询记录（使用自增ID）
        record = DrawingData.query.filter_by(id=int(record_id)).first()

        if not record:
            return jsonify({'error': '记录不存在'}), 404

        # 获取队列管理器
        queue_manager = get_queue_manager()

        # 构建响应数据
        response = {
            'success': True,
            'record_id': str(record.id),  # 返回数据库ID
            'engineering_drawing_id': record.engineering_drawing_id,  # 同时返回图纸编号
            'status': record.status or 'pending',
            'created_at': record.created_at
        }

        # 根据状态添加不同的字段
        if record.status == 'completed':
            response['conclusion'] = record.conclusion
            response['detailed_report'] = record.detailed_report
            response['completed_at'] = record.completed_at
        elif record.status == 'failed':
            response['error_message'] = record.error_message or '检测失败'
        elif record.status == 'pending':
            # 获取队列信息
            queue_info = queue_manager.get_queue_info()
            response['queue_size'] = queue_info['queue_size']
        elif record.status == 'processing':
            response['message'] = '正在检测中，请稍候...'

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': f'查询状态失败: {str(e)}'}), 500


@drawing_bp.route('/api/queue/info', methods=['GET'])
@login_required
def drawing_get_queue_info():
    """获取检测队列信息

    Returns:
        JSON: {
            "success": true,
            "queue_size": 3,
            "current_task": "1234567890",
            "total_tasks": 10,
            "is_running": true
        }
    """
    try:
        queue_manager = get_queue_manager()
        queue_info = queue_manager.get_queue_info()

        return jsonify({
            'success': True,
            **queue_info
        })
    except Exception as e:
        return jsonify({'error': f'获取队列信息失败: {str(e)}'}), 500


@drawing_bp.route('/preview/<filename>')
@login_required
def drawing_preview_pdf(filename):
    """PDF预览接口 - 简化版本 - """
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404

    # 尝试转换PDF为图片
    image_data = convert_pdf_to_image(filepath)

    if image_data:
        return jsonify({
            'success': True,
            'image_data': image_data,
            'message': 'PDF预览生成成功',
            'real_preview': True
        })
    else:
        # 使用占位符
        placeholder_data = create_placeholder_image(filename)
        return jsonify({
            'success': True,
            'image_data': placeholder_data,
            'message': 'PDF预览使用占位符',
            'real_preview': False
        })


@drawing_bp.route('/download-report/<record_id>', methods=['GET'])
@login_required
def drawing_download_report(record_id):
    """根据记录ID下载制图检测报告PDF

    从数据库查询指定的检测记录，返回生成的PDF报告文件

    Args:
        record_id (str): 检测记录的唯一标识符（数据库自增ID）

    Returns:
        Response: 包含PDF报告文件的下载响应，或错误信息
    """
    try:
        print(f"📥 下载报告请求: record_id={record_id}")

        # 从数据库查询记录（使用自增ID）
        record = DrawingData.query.filter_by(id=int(record_id)).first()

        if not record:
            print(f"❌ 记录不存在: id={record_id}")
            return jsonify({'error': '检测记录不存在'}), 404

        print(f"✅ 找到记录: {record.original_filename}")
        print(f"   file_path: {record.file_path}")

        # 检查PDF文件是否存在
        pdf_path = record.file_path

        if not pdf_path:
            print(f"❌ file_path为空")
            return jsonify({'error': 'PDF文件路径为空'}), 404

        # 如果数据库中的路径不存在，尝试从当前UPLOAD_FOLDER中查找
        if not os.path.exists(pdf_path):
            print(f"⚠️  数据库路径无效: {pdf_path}")
            print(f"   尝试从当前UPLOAD_FOLDER中查找文件...")
            
            # 从路径中提取文件名
            filename = os.path.basename(pdf_path)
            # 构建新的路径
            new_pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            print(f"   新路径: {new_pdf_path}")
            
            if os.path.exists(new_pdf_path):
                print(f"✅ 在新路径找到文件")
                pdf_path = new_pdf_path
            else:
                print(f"❌ 文件不存在: {new_pdf_path}")
                return jsonify({'error': f'PDF文件不存在，请重新上传'}), 404

        print(f"✅ PDF文件存在: {pdf_path}")

        # 生成下载文件名
        safe_filename = record.original_filename or 'drawing_report'
        # 确保文件名以.pdf结尾
        if not safe_filename.lower().endswith('.pdf'):
            safe_filename = safe_filename.rsplit('.', 1)[0] + '.pdf' if '.' in safe_filename else safe_filename + '.pdf'

        download_filename = f"检测报告_{safe_filename}"
        print(f"📄 下载文件名: {download_filename}")

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"❌ 下载报告失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'下载报告失败: {str(e)}'}), 500


@drawing_bp.route('/charts')
@login_required
def drawing_charts():
    """制图检测统计报表页面 - 显示AI检测问题汇总统计"""
    return render_template('drawing_chats.html')


@drawing_bp.route('/api/charts/statistics', methods=['GET'])
@login_required
def drawing_get_chart_statistics():
    """获取制图检测统计数据API
    
    支持日期范围、创建人、物料类型筛选
    返回统计信息和问题明细列表
    
    Query Parameters:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        creator: 创建人筛选
        material_type: 物料类型筛选
    
    Returns:
        JSON: {
            'success': True,
            'statistics': {
                'date_range': '2025-06 至 2025-10',
                'total_drawings': 1000,
                'total_issues': 400,
                'issue_types': {
                    '尺寸错误': 50,
                    '版本错误': 50,
                    ...
                },
                'monthly_data': {
                    '2025-06': {'尺寸错误': 8, '版本错误': 7, ...},
                    ...
                }
            },
            'details': [
                {
                    'check_date': '2025-10-30',
                    'issue_type': '尺寸错误',
                    'engineer': '张三',
                    'material_name': '显示面板',
                    'material_type': '塑胶件',
                    'drawing_id': 'J3506-ROC90-01'
                },
                ...
            ]
        }
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        # 获取筛选参数 - 默认查询最近6个月的数据
        today = datetime.now()
        six_months_ago = today - timedelta(days=180)
        
        # 如果用户没有指定日期,使用最近6个月
        start_date = request.args.get('start_date', six_months_ago.strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', today.strftime('%Y-%m-%d'))
        creator = request.args.get('creator', '')
        material_type = request.args.get('material_type', '')
        
        print(f"📊 查询统计数据: start_date={start_date}, end_date={end_date}")
        
        # 查询drawing_data表获取基础数据
        query = DrawingData.query.filter(DrawingData.status == 'completed')
        
        # 应用日期筛选
        if start_date:
            query = query.filter(DrawingData.created_at >= start_date)
        if end_date:
            query = query.filter(DrawingData.created_at <= end_date + ' 23:59:59')
        
        # 应用创建人筛选
        if creator:
            query = query.filter(DrawingData.checker_name == creator)
        
        # 应用物料类型筛选（通过图纸类型字段）
        if material_type:
            query = query.filter(DrawingData.engineering_drawing_type == material_type)
        
        records = query.all()
        
        print(f"✅ 查询到 {len(records)} 条记录")
        
        # 统计数据
        total_drawings = len(records)
        
        # 统计符合/不符合 - 从drawing_data.conclusion字段
        # conclusion字段的值: "符合" 或 "不符合"
        non_compliant_count = sum(1 for r in records if r.conclusion and '不符合' in r.conclusion)
        compliant_count = total_drawings - non_compliant_count
        
        # 问题类型统计 - 从drawing_detection表的对应字段
        # 映射关系（共12个检测项目）:
        # result_1  -> 关键尺寸识别（尺寸错误）
        # result_2  -> 人员参数检查
        # result_3  -> 未注公差表检查（缺少重点尺寸）
        # result_4  -> 安吉尔LOGO检查
        # result_5  -> 中文名称检查
        # result_6  -> 材料信息检查（缺少未注公差）
        # result_7  -> 重量信息检查（图标错误）
        # result_8  -> 尺寸公差检测
        # result_9  -> 公差精确度检测
        # result_10 -> 技术要求检测
        # result_11 -> 图号检查（版本错误）
        # result_12 -> 重量信息检查（缺少单一材质重量）
        
        issue_types_count = {
            '尺寸错误': 0,           # result_1
            '人员参数检查': 0,       # result_2
            '缺少重点尺寸': 0,       # result_3
            'LOGO检查': 0,          # result_4
            '名称检查': 0,          # result_5
            '缺少未注公差': 0,       # result_6
            '图标错误': 0,          # result_7
            '尺寸公差检测': 0,       # result_8
            '公差精确度检测': 0,     # result_9
            '技术要求检测': 0,       # result_10
            '版本错误': 0,          # result_11
            '缺少单一材质重量': 0    # result_12
        }
        
        # 月度数据统计
        monthly_data = {}
        
        # 问题明细列表
        details = []
        
        # 遍历记录，从drawing_detection表获取详细检测项目
        for record in records:
            # 使用SQL直接查询drawing_detection表（获取全部12个result字段）
            sql = text("""
                SELECT result_1, result_2, result_3, result_4, result_5, result_6,
                       result_7, result_8, result_9, result_10, result_11, result_12
                FROM drawing_detection
                WHERE engineering_drawing_id = :drawing_id
            """)
            detection_records = db.session.execute(sql, {'drawing_id': record.engineering_drawing_id}).fetchall()
            
            # 提取月份
            if record.created_at:
                try:
                    month = record.created_at[:7]  # YYYY-MM
                    if month not in monthly_data:
                        monthly_data[month] = {k: 0 for k in issue_types_count.keys()}
                except:
                    month = None
            else:
                month = None
            
            # 分析检测结果，统计问题类型
            for detection in detection_records:
                (result_1, result_2, result_3, result_4, result_5, result_6,
                 result_7, result_8, result_9, result_10, result_11, result_12) = detection
                
                # result_1 - 尺寸错误（关键尺寸识别）
                if result_1 and '不符合' in result_1:
                    issue_types_count['尺寸错误'] += 1
                    if month:
                        monthly_data[month]['尺寸错误'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '尺寸错误',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_2 - 人员参数检查
                if result_2 and '不符合' in result_2:
                    issue_types_count['人员参数检查'] += 1
                    if month:
                        monthly_data[month]['人员参数检查'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '人员参数检查',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_3 - 缺少重点尺寸（未注公差表检查）
                if result_3 and '不符合' in result_3:
                    issue_types_count['缺少重点尺寸'] += 1
                    if month:
                        monthly_data[month]['缺少重点尺寸'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '缺少重点尺寸',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_4 - LOGO检查（安吉尔LOGO检查）
                if result_4 and '不符合' in result_4:
                    issue_types_count['LOGO检查'] += 1
                    if month:
                        monthly_data[month]['LOGO检查'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': 'LOGO检查',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_5 - 名称检查（中文名称检查）
                if result_5 and '不符合' in result_5:
                    issue_types_count['名称检查'] += 1
                    if month:
                        monthly_data[month]['名称检查'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '名称检查',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_6 - 缺少未注公差（材料信息检查）
                if result_6 and '不符合' in result_6:
                    issue_types_count['缺少未注公差'] += 1
                    if month:
                        monthly_data[month]['缺少未注公差'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '缺少未注公差',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_7 - 图标错误（重量信息检查）
                if result_7 and '不符合' in result_7:
                    issue_types_count['图标错误'] += 1
                    if month:
                        monthly_data[month]['图标错误'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '图标错误',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_8 - 尺寸公差检测
                if result_8 and '不符合' in result_8:
                    issue_types_count['尺寸公差检测'] += 1
                    if month:
                        monthly_data[month]['尺寸公差检测'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '尺寸公差检测',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_9 - 公差精确度检测
                if result_9 and '不符合' in result_9:
                    issue_types_count['公差精确度检测'] += 1
                    if month:
                        monthly_data[month]['公差精确度检测'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '公差精确度检测',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_10 - 技术要求检测
                if result_10 and '不符合' in result_10:
                    issue_types_count['技术要求检测'] += 1
                    if month:
                        monthly_data[month]['技术要求检测'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '技术要求检测',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_11 - 版本错误（图号检查）
                if result_11 and '不符合' in result_11:
                    issue_types_count['版本错误'] += 1
                    if month:
                        monthly_data[month]['版本错误'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '版本错误',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
                
                # result_12 - 缺少单一材质重量（重量信息检查）
                if result_12 and '不符合' in result_12:
                    issue_types_count['缺少单一材质重量'] += 1
                    if month:
                        monthly_data[month]['缺少单一材质重量'] += 1
                    details.append({
                        'check_date': record.created_at[:10] if record.created_at else '',
                        'issue_type': '缺少单一材质重量',
                        'engineer': record.checker_name or '',
                        'material_name': record.original_filename or '',
                        'material_type': record.engineering_drawing_type or '',
                        'drawing_id': record.engineering_drawing_id or ''
                    })
        
        # 计算总问题数
        total_issues = sum(issue_types_count.values())
        
        # 计算异常数：比较drawing_dataset和drawing_detection表中对应字段的差异
        anomaly_count = 0
        for record in records:
            # 查询 drawing_dataset 表中的记录
            dataset_sql = text("""
                SELECT result_1, result_2, result_3, result_4, result_5, result_6,
                       result_7, result_8, result_9, result_10, result_11, result_12
                FROM drawing_dataset
                WHERE engineering_drawing_id = :drawing_id
            """)
            dataset_records = db.session.execute(dataset_sql, {'drawing_id': record.engineering_drawing_id}).fetchall()
            
            # 查询 drawing_detection 表中的记录
            detection_sql = text("""
                SELECT result_1, result_2, result_3, result_4, result_5, result_6,
                       result_7, result_8, result_9, result_10, result_11, result_12
                FROM drawing_detection
                WHERE engineering_drawing_id = :drawing_id
            """)
            detection_records = db.session.execute(detection_sql, {'drawing_id': record.engineering_drawing_id}).fetchall()
            
            # 比较两个表中的结果，如果有对应记录则进行对比
            if dataset_records and detection_records:
                for dataset_row in dataset_records:
                    for detection_row in detection_records:
                        # 比较12个result字段
                        for i in range(12):
                            dataset_val = dataset_row[i] if dataset_row[i] else ''
                            detection_val = detection_row[i] if detection_row[i] else ''
                            # 如果两个值不相同，则计为异常
                            if dataset_val != detection_val:
                                anomaly_count += 1
        
        # 格式化日期范围
        date_range = f"{start_date[:7]} 至 {end_date[:7]}"
        
        print(f"📈 统计结果: 总图纸={total_drawings}, 符合={compliant_count}, 不符合={non_compliant_count}, 总问题={total_issues}, 异常数={anomaly_count}")
        print(f"   问题分布: {issue_types_count}")
        
        return jsonify({
            'success': True,
            'statistics': {
                'date_range': date_range,
                'total_drawings': total_drawings,
                'compliant_count': compliant_count,
                'non_compliant_count': non_compliant_count,
                'total_issues': total_issues,
                'anomaly_count': anomaly_count,
                'issue_types': issue_types_count,
                'monthly_data': monthly_data
            },
            'details': details
        })
        
    except Exception as e:
        import traceback
        print(f"❌ 获取统计数据失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'获取统计数据失败: {str(e)}'}), 500



