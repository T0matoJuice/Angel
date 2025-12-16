#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量工单检测 API 路由
提供RESTful API接口供外部调用
"""

import os
import time
from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.utils import secure_filename
from modules.auth.oauth_utils import require_oauth
from modules.excel.models import WorkorderData, WorkorderUselessdata1, WorkorderUselessdata2
from modules.excel.queue_manager import get_queue_manager
from modules.auth import db
import pandas as pd

# 创建Excel API蓝图
excel_api_bp = Blueprint('excel_api', __name__)


def allowed_excel_file(filename):
    """检查文件类型是否允许"""
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@excel_api_bp.route('/upload', methods=['POST'])
@require_oauth(['excel:upload'])
def api_upload_excel():
    """API: 上传质量工单Excel文件（上传后自动加入检测队列）

    请求格式:
        POST /api/v1/excel/upload
        Authorization: Bearer <access_token>
        Content-Type: multipart/form-data

        file: Excel文件 (必填)
        batch_size: 批量处理大小，默认50 (可选)

    响应格式:
        {
            "success": true,
            "task_id": "20251201_120000_workorder.xlsx",
            "filename": "workorder.xlsx",
            "rows_count": 100,
            "status": "pending",
            "message": "文件上传成功，检测任务已加入队列"
        }
    """
    # 1. 检查文件是否存在
    if 'file' not in request.files:
        return jsonify({
            'error': 'missing_file',
            'error_description': '请求中没有文件'
        }), 400

    file = request.files['file']

    # 2. 检查文件名
    if file.filename == '':
        return jsonify({
            'error': 'empty_filename',
            'error_description': '文件名为空'
        }), 400

    # 3. 检查文件类型
    if not allowed_excel_file(file.filename):
        return jsonify({
            'error': 'invalid_file_type',
            'error_description': '只支持Excel格式文件(.xlsx, .xls)'
        }), 400

    # 4. 获取批量处理参数和用户信息
    batch_size = request.form.get('batch_size', 50, type=int)
    if batch_size < 1 or batch_size > 200:
        return jsonify({
            'error': 'invalid_batch_size',
            'error_description': '批量处理大小必须在1-200之间'
        }), 400
    
    # 获取account和datatime（API调用时必须提供）
    account = request.form.get('account', '').strip()
    datatime_client = request.form.get('datatime', '').strip()
    
    if not account:
        return jsonify({
            'error': 'missing_account',
            'error_description': '缺少account参数'
        }), 400
    
    # datatime 统一使用服务器当前时间，避免客户端传固定值导致写入过期时间
    datatime = time.strftime('%Y-%m-%d %H:%M:%S')
    if datatime_client:
        print(f"ℹ️ [API] 已忽略客户端 datatime={datatime_client}，使用服务器当前时间: {datatime}")
    else:
        print(f"ℹ️ [API] datatime 未提供，使用服务器当前时间: {datatime}")
    
    print(f"📋 [API] 账号: {account}, 时间: {datatime}")

    # 5. 保存文件并解析数据
    try:
        # 生成唯一文件名
        timestamp_str = time.strftime('%Y%m%d_%H%M%S')
        original_filename = os.path.basename(file.filename)
        unique_filename = f"{timestamp_str}_{original_filename}"

        # 保存到uploads目录
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)

        print(f"✅ [API] 文件已保存: {filepath}")

        # 6. 解析Excel文件
        try:
            df = pd.read_excel(filepath, dtype=str)
            
            # 检查是否为空文件
            if df.empty:
                os.remove(filepath)  # 删除无效文件
                return jsonify({
                    'error': 'empty_file',
                    'error_description': 'Excel文件为空'
                }), 400

            rows_count = len(df)
            print(f"📊 [API] Excel文件包含 {rows_count} 行数据")

            # 检查必要字段（83个字段的Excel）
            required_columns = ['工单单号', '工单性质', '判定依据']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                os.remove(filepath)  # 删除无效文件
                return jsonify({
                    'error': 'invalid_format',
                    'error_description': f'Excel文件缺少必要字段: {", ".join(missing_columns)}'
                }), 400

        except Exception as e:
            os.remove(filepath)  # 删除无效文件
            return jsonify({
                'error': 'parse_failed',
                'error_description': f'解析Excel文件失败: {str(e)}'
            }), 400

        # 7. 将数据插入数据库（三个表）
        try:
            from modules.excel.field_mapping import (
                get_workorder_data_mapping,
                get_workorder_uselessdata_1_mapping,
                get_workorder_uselessdata_2_mapping
            )

            # 获取字段映射
            data_fields = get_workorder_data_mapping()
            useless1_fields = get_workorder_uselessdata_1_mapping()
            useless2_fields = get_workorder_uselessdata_2_mapping()

            # 插入WorkorderData表
            for _, row in df.iterrows():
                work_alone = str(row.get('工单单号', '')).strip()
                if not work_alone or work_alone == 'nan':
                    continue

                # 准备WorkorderData数据
                data_record = WorkorderData(
                    filename=unique_filename,
                    workAlone=work_alone,
                    workOrderNature=None,  # 检测前为空
                    judgmentBasis=None,    # 检测前为空
                    account=account,       # API调用者提供的账号
                    datatime=datatime      # API调用时的时间戳
                )

                # 映射其他字段
                for excel_col, db_field in data_fields.items():
                    if excel_col in df.columns and db_field not in ['workAlone', 'workOrderNature', 'judgmentBasis', 'filename', 'account', 'datatime']:
                        value = row.get(excel_col)
                        if pd.notna(value):
                            setattr(data_record, db_field, str(value))

                db.session.add(data_record)

                # 准备WorkorderUselessdata1数据
                useless1_record = WorkorderUselessdata1(
                    filename=unique_filename,
                    workAlone=work_alone
                )
                for excel_col, db_field in useless1_fields.items():
                    if excel_col in df.columns and db_field not in ['workAlone', 'filename']:
                        value = row.get(excel_col)
                        if pd.notna(value):
                            setattr(useless1_record, db_field, str(value))

                db.session.add(useless1_record)

                # 准备WorkorderUselessdata2数据
                useless2_record = WorkorderUselessdata2(
                    filename=unique_filename,
                    workAlone=work_alone
                )
                for excel_col, db_field in useless2_fields.items():
                    if excel_col in df.columns and db_field not in ['workAlone', 'filename']:
                        value = row.get(excel_col)
                        if pd.notna(value):
                            setattr(useless2_record, db_field, str(value))

                db.session.add(useless2_record)

            # 提交数据库事务
            db.session.commit()
            print(f"💾 [API] 数据已插入数据库: {rows_count} 条记录")

        except Exception as e:
            db.session.rollback()
            os.remove(filepath)  # 删除文件
            return jsonify({
                'error': 'database_error',
                'error_description': f'数据入库失败: {str(e)}'
            }), 500

        # 8. 将检测任务加入队列
        queue_manager = get_queue_manager(current_app)
        queue_added = queue_manager.add_task(
            filename=unique_filename,
            filepath=filepath,
            batch_size=batch_size
        )

        if not queue_added:
            return jsonify({
                'error': 'queue_failed',
                'error_description': '任务加入队列失败，请重试'
            }), 500

        print(f"✅ [API] 检测任务已加入队列: {unique_filename}")

        # 9. 返回成功响应
        return jsonify({
            'success': True,
            'task_id': unique_filename,
            'filename': original_filename,
            'rows_count': rows_count,
            'batch_size': batch_size,
            'status': 'pending',
            'message': '文件上传成功，检测任务已加入队列'
        }), 200

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            'error': 'upload_failed',
            'error_description': f'文件上传失败: {str(e)}'
        }), 500


@excel_api_bp.route('/status/<task_id>', methods=['GET'])
@require_oauth(['excel:query'])
def api_get_excel_status(task_id):
    """API: 查询检测任务状态

    请求格式:
        GET /api/v1/excel/status/<task_id>
        Authorization: Bearer <access_token>

    响应格式:
        {
            "success": true,
            "task_id": "20251201_120000_workorder.xlsx",
            "status": "pending|processing|completed|failed",
            "rows_total": 100,
            "rows_processed": 50,
            "progress": 50,
            "result_files": {
                "csv": "quality_result_20251201_120030.csv",
                "excel": "quality_result_20251201_120030.xlsx"
            }
        }
    """
    try:
        # 获取队列管理器
        queue_manager = get_queue_manager(current_app)
        
        # 查询队列状态
        task_status = queue_manager.get_task_status(task_id)
        
        # 查询数据库记录
        records = WorkorderData.query.filter_by(filename=task_id).all()
        
        if not records:
            return jsonify({
                'error': 'task_not_found',
                'error_description': '任务不存在'
            }), 404

        rows_total = len(records)
        rows_processed = sum(1 for r in records if r.workOrderNature)

        # 构建响应数据
        response = {
            'success': True,
            'task_id': task_id,
            'status': task_status or 'unknown',
            'rows_total': rows_total,
            'rows_processed': rows_processed,
            'progress': int((rows_processed / rows_total * 100) if rows_total > 0 else 0)
        }

        # 根据状态添加不同的字段
        if task_status == 'completed':
            # 查询结果文件
            task_result = queue_manager.get_task_result(task_id)
            if task_result:
                response['result_files'] = {
                    'csv': task_result.get('csv_filename'),
                    'excel': task_result.get('excel_filename')
                }
                response['message'] = '检测完成'
        elif task_status == 'processing':
            response['message'] = '正在检测中，请稍候...'
        elif task_status == 'pending':
            queue_info = queue_manager.get_queue_info()
            response['queue_size'] = queue_info['queue_size']
            response['message'] = '任务排队中，请稍候...'
        elif task_status == 'failed':
            response['message'] = '检测失败，请重新上传'

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            'error': 'query_failed',
            'error_description': f'查询状态失败: {str(e)}'
        }), 500


@excel_api_bp.route('/result/<task_id>', methods=['GET'])
@require_oauth(['excel:query'])
def api_get_excel_result(task_id):
    """API: 获取检测结果数据

    请求格式:
        GET /api/v1/excel/result/<task_id>
        Authorization: Bearer <access_token>

    响应格式:
        {
            "success": true,
            "task_id": "20251201_120000_workorder.xlsx",
            "rows_total": 100,
            "results": [
                {
                    "工单单号": "WO001",
                    "工单性质": "质量问题",
                    "判定依据": "根据...",
                    ...
                }
            ]
        }
    """
    try:
        # 查询数据库记录
        records = WorkorderData.query.filter_by(filename=task_id).all()

        if not records:
            return jsonify({
                'error': 'task_not_found',
                'error_description': '任务不存在'
            }), 404

        # 构建19字段结果数据
        expected_columns = ['工单单号','工单性质','判定依据','保内保外','批次入库日期','安装日期','购机日期',
                          '产品名称','开发主体','故障部位名称','故障组','故障类别','服务项目或故障现象',
                          '维修方式','旧件名称','新件名称','来电内容','现场诊断故障现象','处理方案简述或备注']

        results = []
        for record in records:
            u1 = WorkorderUselessdata1.query.filter_by(filename=task_id, workAlone=record.workAlone).first()
            u2 = WorkorderUselessdata2.query.filter_by(filename=task_id, workAlone=record.workAlone).first()

            def norm(v):
                return '' if v is None or v == 'None' or (isinstance(v, float) and pd.isna(v)) else str(v)

            row_data = {
                '工单单号': norm(record.workAlone),
                '工单性质': norm(record.workOrderNature),
                '判定依据': norm(record.judgmentBasis),
                '保内保外': norm(u1.internalExternalInsurance if u1 else ''),
                '批次入库日期': norm(u1.batchWarehousingDate if u1 else ''),
                '安装日期': norm(u1.installDate if u1 else ''),
                '购机日期': norm(u1.purchaseDate if u1 else ''),
                '产品名称': norm(u1.productName if u1 else ''),
                '开发主体': norm(u1.developmentSubject if u1 else ''),
                '故障部位名称': norm(record.replacementPartName),
                '故障组': norm(record.faultGroup),
                '故障类别': norm(record.faultClassification),
                '服务项目或故障现象': norm(record.faultPhenomenon),
                '维修方式': norm(u2.maintenanceMode if u2 else ''),
                '旧件名称': norm(u2.oldPartName if u2 else ''),
                '新件名称': norm(u2.newPartName if u2 else ''),
                '来电内容': norm(record.callContent),
                '现场诊断故障现象': norm(record.onsiteFaultPhenomenon),
                '处理方案简述或备注': norm(record.remarks),
            }
            results.append(row_data)

        return jsonify({
            'success': True,
            'task_id': task_id,
            'rows_total': len(results),
            'columns': expected_columns,
            'results': results
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'query_failed',
            'error_description': f'查询结果失败: {str(e)}'
        }), 500


@excel_api_bp.route('/download/<task_id>', methods=['GET'])
@require_oauth(['excel:query'])
def api_download_excel_result(task_id):
    """API: 下载检测结果文件

    请求格式:
        GET /api/v1/excel/download/<task_id>?format=excel
        Authorization: Bearer <access_token>
        
        参数:
            format: excel 或 csv，默认 excel

    响应:
        返回文件流
    """
    try:
        # 获取队列管理器
        queue_manager = get_queue_manager(current_app)
        
        # 查询结果文件
        task_result = queue_manager.get_task_result(task_id)
        
        if not task_result:
            return jsonify({
                'error': 'result_not_found',
                'error_description': '结果文件不存在，检测可能未完成'
            }), 404

        # 获取文件格式
        file_format = request.args.get('format', 'excel')
        
        if file_format == 'csv':
            filename = task_result.get('csv_filename')
        else:
            filename = task_result.get('excel_filename')

        if not filename:
            return jsonify({
                'error': 'file_not_found',
                'error_description': '结果文件不存在'
            }), 404

        # 构建文件路径
        results_folder = current_app.config['RESULTS_FOLDER']
        filepath = os.path.join(results_folder, filename)

        if not os.path.exists(filepath):
            return jsonify({
                'error': 'file_not_found',
                'error_description': '结果文件不存在'
            }), 404

        # 返回文件
        from flask import send_file
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            'error': 'download_failed',
            'error_description': f'下载失败: {str(e)}'
        }), 500


@excel_api_bp.route('/health', methods=['GET'])
def api_health_check():
    """API: 健康检查（无需认证）

    请求格式:
        GET /api/v1/excel/health

    响应格式:
        {
            "status": "ok",
            "service": "Excel Quality Inspection API",
            "version": "1.0.0"
        }
    """
    return jsonify({
        'status': 'ok',
        'service': 'Excel Quality Inspection API',
        'version': '1.0.0'
    }), 200
