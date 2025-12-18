#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工程制图检测 API 路由
提供RESTful API接口供外部调用
"""

import os
import time
import json
import re
from collections import OrderedDict
from flask import Blueprint, request, jsonify, current_app
from modules.auth.oauth_utils import require_oauth
from modules.drawing.utils import allowed_file
from modules.drawing.services import inspect_drawing_api
from modules.drawing.models import DrawingData, DrawingDataset
from modules.drawing.queue_manager import get_queue_manager
from modules.auth import db

# 创建Drawing API蓝图
drawing_api_bp = Blueprint('drawing_api', __name__)


def safe_filename_with_chinese(filename):
    """生成安全的文件名，保留中文字符

    只移除危险字符，保留中文、英文、数字、下划线、横线和点号

    Args:
        filename (str): 原始文件名

    Returns:
        str: 安全的文件名
    """
    if not filename:
        return 'unnamed'

    # 移除路径分隔符和其他危险字符，但保留中文
    # 允许：中文、英文字母、数字、下划线、横线、点号、空格
    filename = re.sub(r'[\\/:*?"<>|]', '_', filename)

    # 移除开头和结尾的空格和点号
    filename = filename.strip(' .')

    # 如果文件名为空或只有扩展名，使用默认名称
    if not filename or filename.startswith('.'):
        return 'unnamed' + filename

    return filename


@drawing_api_bp.route('/upload', methods=['POST'])
@require_oauth(['drawing:upload'])
def api_upload_drawing():
    """API: 上传工程图纸（新版本：上传后自动加入检测队列）

    请求格式:
        POST /api/v1/drawing/upload
        Authorization: Bearer <access_token>
        Content-Type: multipart/form-data

        file: PDF文件
        engineering_drawing_id: 图纸文档编号 (必填)
        checker_name: 检入者姓名 (必填)
        version: 版本号 (必填)
        drawing_type: 图纸类型 (必填)

    响应格式:
        {
            "success": true,
            "record_id": "DRW-2024-001",
            "filename": "drawing.pdf",
            "checker_name": "张三",
            "version": "V1.0",
            "drawing_type": "装配图",
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
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'invalid_file_type',
            'error_description': '只支持PDF格式文件'
        }), 400

    # 4. 获取检入者、版本、图纸文档编号和图纸类型信息
    # engineering_drawing_id 和 drawing_type 如果未提供，使用默认值
    engineering_drawing_id = request.form.get('engineering_drawing_id', '').strip()
    if not engineering_drawing_id:
        # 使用时间戳作为默认图纸编号
        engineering_drawing_id = f"DWG-{int(time.time() * 1000)}"

    checker_name = request.form.get('checker_name', '').strip()
    version = request.form.get('version', '').strip()

    drawing_type = request.form.get('drawing_type', '').strip()
    if not drawing_type:
        # 默认图纸类型
        drawing_type = "未分类"

    # 验证必填字段（只验证checker_name和version）
    if not checker_name:
        return jsonify({
            'error': 'missing_checker_name',
            'error_description': '检入者不能为空'
        }), 400

    if not version:
        return jsonify({
            'error': 'missing_version',
            'error_description': '版本不能为空'
        }), 400

    # 5. 保存文件并创建数据库记录：
    try:
        # 生成唯一文件名（使用毫秒时间戳）
        timestamp = int(time.time() * 1000)
        original_filename = safe_filename_with_chinese(file.filename)
        filename = f"{timestamp}_{original_filename}"

        # 保存到uploads目录
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # 6. 立即创建数据库记录（状态：pending）
        drawing_record = DrawingData(
            engineering_drawing_id=engineering_drawing_id,  # 使用用户提供的图纸文档编号
            account=f"{request.oauth_client.client_name} (API)",  # 标记为API调用
            original_filename=original_filename,
            file_path=filepath,
            checker_name=checker_name,
            version=version,
            engineering_drawing_type=drawing_type,  # 新增：图纸类型
            created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            status='pending',
            conclusion='',
            detailed_report='',
            source='API'  # 数据来源：API调用
        )

        db.session.add(drawing_record)
        db.session.commit()

        # 获取数据库自增ID
        db_record_id = drawing_record.id

        print(f"✅ [API] 数据库记录已创建: ID={db_record_id}, engineering_drawing_id={engineering_drawing_id}")
        print(f"   客户端: {request.oauth_client.client_name}, 文件: {original_filename}")

        # 7. 将检测任务加入队列（使用数据库ID）
        queue_manager = get_queue_manager()
        queue_added = queue_manager.add_task(str(db_record_id), filepath)

        if not queue_added:
            return jsonify({
                'error': 'queue_failed',
                'error_description': '任务加入队列失败，请重试'
            }), 500

        # 8. 返回成功响应
        return jsonify({
            'success': True,
            'record_id': str(db_record_id),  # 返回数据库自增ID
            'engineering_drawing_id': engineering_drawing_id,  # 同时返回图纸编号供参考
            'filename': original_filename,
            'checker_name': checker_name,
            'version': version,
            'drawing_type': drawing_type,  # 返回图纸类型
            'status': 'pending',
            'message': '文件上传成功，检测任务已加入队列'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'upload_failed',
            'error_description': f'文件上传失败: {str(e)}'
        }), 500


@drawing_api_bp.route('/inspect', methods=['POST'])
@require_oauth(['drawing:inspect'])
def api_inspect_drawing():
    """API: 执行工程图纸检测（已废弃）

    注意：此接口已被队列机制取代，上传后会自动检测
    请使用 GET /api/v1/drawing/status/<record_id> 查询检测状态

    响应格式:
        {
            "error": "deprecated",
            "error_description": "此接口已废弃，上传后会自动开始检测，请使用状态查询接口"
        }
    """
    return jsonify({
        'error': 'deprecated',
        'error_description': '此接口已废弃，上传后会自动开始检测，请使用 GET /api/v1/drawing/status/<record_id> 查询检测状态'
    }), 410  # 410 Gone


@drawing_api_bp.route('/status/<record_id>', methods=['GET'])
@require_oauth(['drawing:inspect'])
def api_get_drawing_status(record_id):
    """API: 查询检测任务状态

    请求格式:
        GET /api/v1/drawing/status/<record_id>
        Authorization: Bearer <access_token>

    响应格式:
        {
            "success": true,
            "record_id": "123",
            "engineering_drawing_id": "DWG-001",
            "status": "pending|processing|completed|failed",
            "conclusion": "合格",  // 仅当 status=completed 时有值
            "detailed_report": "...",  // 仅当 status=completed 时有值
            "error_message": "...",  // 仅当 status=failed 时有值
            "queue_size": 3  // 仅当 status=pending 时有值
        }
    """
    try:
        # 从数据库查询记录（使用自增ID）
        record = DrawingData.query.filter_by(id=int(record_id)).first()

        if not record:
            return jsonify({
                'error': 'record_not_found',
                'error_description': '记录不存在'
            }), 404

        # 获取队列管理器
        queue_manager = get_queue_manager()

        # 构建响应数据
        response = {
            'success': True,
            'record_id': str(record.id),  # 返回数据库ID
            'engineering_drawing_id': record.engineering_drawing_id,  # 同时返回图纸编号
            'status': record.status or 'pending',
            'created_at': record.created_at,
            'filename': record.original_filename,
            'checker_name': record.checker_name,
            'version': record.version
        }

        # 根据状态添加不同的字段
        if record.status == 'completed':
            response['conclusion'] = record.conclusion
            response['detailed_report'] = record.detailed_report
            response['completed_at'] = record.completed_at
        elif record.status == 'failed':
            response['error_message'] = record.error_message or '检测失败'
        elif record.status == 'pending':
            queue_info = queue_manager.get_queue_info()
            response['queue_size'] = queue_info['queue_size']
        elif record.status == 'processing':
            response['message'] = '正在检测中，请稍候...'

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            'error': 'query_failed',
            'error_description': f'查询状态失败: {str(e)}'
        }), 500


# 以下接口保留用于向后兼容，但已标记为废弃
@drawing_api_bp.route('/inspect_legacy', methods=['POST'])
@require_oauth(['drawing:inspect'])
def api_inspect_drawing_legacy():
    """API: 执行工程图纸检测（旧版本，仅用于向后兼容）

    请求格式:
        POST /api/v1/drawing/inspect_legacy
        Authorization: Bearer <access_token>
        Content-Type: application/json

        {
            "filename": "1234567890_drawing.pdf"
        }
    """
    # 1. 获取请求参数
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({
            'error': 'missing_filename',
            'error_description': '缺少filename参数'
        }), 400

    filename = data['filename']

    # 2. 检查文件是否存在
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, filename)

    if not os.path.exists(filepath):
        return jsonify({
            'error': 'file_not_found',
            'error_description': '文件不存在，请先上传文件'
        }), 404

    # 3. 执行检测
    try:
        result = inspect_drawing_api(filepath)

        # 4. 检查检测是否成功
        if 'error' in result:
            return jsonify({
                'error': 'inspection_failed',
                'error_description': result['error']
            }), 500

        # 5. 保存检测结果到数据库
        if result.get('success'):
            try:
                # 生成唯一的检测记录ID
                engineering_drawing_id = str(int(time.time() * 1000))

                # 提取原始文件名
                original_filename = filename.split('_', 1)[1] if '_' in filename else filename

                # 获取上传时保存的元数据
                metadata = {}
                if hasattr(current_app, 'upload_metadata') and filename in current_app.upload_metadata:
                    metadata = current_app.upload_metadata[filename]
                    del current_app.upload_metadata[filename]

                # 创建检测记录
                drawing_record = DrawingData(
                    engineering_drawing_id=engineering_drawing_id,
                    account=metadata.get('client_name', request.oauth_client.client_name),
                    original_filename=original_filename,
                    file_path=filepath,
                    conclusion=result.get('conclusion', '未知'),
                    detailed_report=result.get('detailed_report', ''),
                    created_at=result.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S')),
                    checker_name=metadata.get('checker_name', ''),
                    version=metadata.get('version', ''),
                    source='API'  # 数据来源：API调用（旧接口）
                )

                db.session.add(drawing_record)
                db.session.commit()

                # 6. 返回检测结果
                return jsonify({
                    'success': True,
                    'inspection_id': engineering_drawing_id,
                    'filename': original_filename,
                    'conclusion': result.get('conclusion', '未知'),
                    'detailed_report': result.get('detailed_report', ''),
                    'checker_name': metadata.get('checker_name', ''),
                    'version': metadata.get('version', ''),
                    'timestamp': result.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
                }), 200

            except Exception as e:
                db.session.rollback()
                return jsonify({
                    'error': 'database_error',
                    'error_description': f'保存检测结果失败: {str(e)}'
                }), 500
        else:
            return jsonify({
                'error': 'inspection_failed',
                'error_description': '检测失败'
            }), 500

    except Exception as e:
        return jsonify({
            'error': 'inspection_error',
            'error_description': f'检测过程出错: {str(e)}'
        }), 500


@drawing_api_bp.route('/result/<inspection_id>', methods=['GET'])
@require_oauth(['drawing:query'])
def api_get_inspection_result(inspection_id):
    """API: 查询检测结果

    请求格式:
        GET /api/v1/drawing/result/<inspection_id>
        Authorization: Bearer <access_token>

    响应格式:
        {
            "success": true,
            "inspection_id": "1234567890123",
            "filename": "drawing.pdf",
            "conclusion": "合格",
            "detailed_report": "检测详细报告...",
            "checker_name": "张三",
            "version": "V1.0",
            "created_at": "2025-11-19 10:30:00"
        }
    """
    try:
        # 查询检测记录
        record = DrawingData.query.filter_by(
            engineering_drawing_id=inspection_id
        ).first()

        if not record:
            return jsonify({
                'error': 'not_found',
                'error_description': '检测记录不存在'
            }), 404

        # 返回检测结果
        return jsonify({
            'success': True,
            'inspection_id': record.engineering_drawing_id,
            'filename': record.original_filename,
            'conclusion': record.conclusion,
            'detailed_report': record.detailed_report,
            'checker_name': record.checker_name,
            'version': record.version,
            'created_at': record.created_at
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'query_error',
            'error_description': f'查询失败: {str(e)}'
        }), 500


@drawing_api_bp.route('/history', methods=['GET'])
@require_oauth(['drawing:query'])
def api_get_inspection_history():
    """API: 查询检测历史记录

    请求格式:
        GET /api/v1/drawing/history?page=1&per_page=10
        Authorization: Bearer <access_token>

    响应格式:
        {
            "success": true,
            "total": 100,
            "page": 1,
            "per_page": 10,
            "records": [
                {
                    "inspection_id": "1234567890123",
                    "filename": "drawing.pdf",
                    "conclusion": "合格",
                    "checker_name": "张三",
                    "version": "V1.0",
                    "created_at": "2025-11-19 10:30:00"
                },
                ...
            ]
        }
    """
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # 限制每页最大数量
        if per_page > 100:
            per_page = 100

        # 查询当前客户端的检测记录
        client_name = request.oauth_client.client_name

        # 分页查询
        pagination = DrawingData.query.filter_by(
            account=client_name
        ).order_by(
            DrawingData.id.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # 构建响应数据
        records = []
        for record in pagination.items:
            records.append({
                'inspection_id': record.engineering_drawing_id,
                'filename': record.original_filename,
                'conclusion': record.conclusion,
                'checker_name': record.checker_name,
                'version': record.version,
                'created_at': record.created_at
            })

        return jsonify({
            'success': True,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'records': records
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'query_error',
            'error_description': f'查询历史记录失败: {str(e)}'
        }), 500


@drawing_api_bp.route('/health', methods=['GET'])
def api_health_check():
    """API: 健康检查（无需认证）

    请求格式:
        GET /api/v1/drawing/health

    响应格式:
        {
            "status": "ok",
            "service": "Drawing Inspection API",
            "version": "1.0.0"
        }
    """
    return jsonify({
        'status': 'ok',
        'service': 'Drawing Inspection API',
        'version': '1.0.0'
    }), 200


@drawing_api_bp.route('/dataset', methods=['POST'])
@require_oauth(['drawing:dataset'])
def api_save_dataset():
    """API: 保存图纸检测数据集

    将图纸检测的详细项目数据保存到 drawing_dataset 表中。
    支持保存12个检测项目的名称、结果和描述。

    请求格式:
        POST /api/v1/drawing/dataset
        Authorization: Bearer <access_token>
        Content-Type: application/x-www-form-urlencoded 或 multipart/form-data

        Form Data 参数:
            engineering_drawing_id: "DRW-2024-001"  // 必填
            check_time: "2024-12-16 10:30:00"       // 可选
            flowpath_id: "FLOW-001"                  // 可选
            project_1: "图框格式"                    // 可选
            result_1: "符合"                         // 可选
            describe_1: "图框格式正确"               // 可选
            project_2: "标题栏内容"
            result_2: "符合"
            describe_2: "标题栏内容完整"
            ...
            project_12: "其他规范"
            result_12: "符合"
            describe_12: "符合其他规范要求"

    响应格式:
        {
            "success": true,
            "message": "数据集保存成功",
            "dataset_id": 123,
            "engineering_drawing_id": "DRW-2024-001"
        }
    """
    try:
        # 从 Form Data 获取数据
        engineering_drawing_id = request.form.get('engineering_drawing_id', '').strip()

        # 验证必填字段
        if not engineering_drawing_id:
            return jsonify({
                'error': 'missing_engineering_drawing_id',
                'error_description': '图纸文档编号不能为空'
            }), 400

        # 创建数据集记录
        dataset = DrawingDataset(
            engineering_drawing_id=engineering_drawing_id,
            check_time=request.form.get('check_time', time.strftime('%Y-%m-%d %H:%M:%S')),
            flowpath_id=request.form.get('flowpath_id', '')
        )

        # 设置12个检测项目的数据
        for i in range(1, 13):
            setattr(dataset, f'project_{i}', request.form.get(f'project_{i}', ''))
            setattr(dataset, f'result_{i}', request.form.get(f'result_{i}', ''))
            setattr(dataset, f'describe_{i}', request.form.get(f'describe_{i}', ''))

        # 保存到数据库
        db.session.add(dataset)
        db.session.commit()

        print(f"✅ [API] 数据集已保存: ID={dataset.id}, 图纸编号={engineering_drawing_id}")

        return jsonify({
            'success': True,
            'message': '数据集保存成功',
            'dataset_id': dataset.id,
            'engineering_drawing_id': engineering_drawing_id
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ [API] 保存数据集失败: {str(e)}")
        return jsonify({
            'error': 'save_failed',
            'error_description': f'保存数据集失败: {str(e)}'
        }), 500


@drawing_api_bp.route('/dataset/<int:dataset_id>', methods=['GET'])
@require_oauth(['drawing:dataset'])
def api_get_dataset(dataset_id):
    """API: 获取图纸检测数据集

    根据数据集ID获取详细的检测项目数据。

    请求格式:
        GET /api/v1/drawing/dataset/<dataset_id>
        Authorization: Bearer <access_token>

    响应格式:
        {
            "success": true,
            "dataset": {
                "id": 123,
                "engineering_drawing_id": "DRW-2024-001",
                "check_time": "2024-12-16 10:30:00",
                "flowpath_id": "FLOW-001",
                "project_1": "图框格式",
                "result_1": "符合",
                "describe_1": "图框格式正确",
                ...
            }
        }
    """
    try:
        dataset = DrawingDataset.query.get(dataset_id)

        if not dataset:
            return jsonify({
                'error': 'not_found',
                'error_description': f'未找到ID为{dataset_id}的数据集'
            }), 404

        return jsonify({
            'success': True,
            'dataset': dataset.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'query_error',
            'error_description': f'查询数据集失败: {str(e)}'
        }), 500


@drawing_api_bp.route('/dataset/by-drawing/<engineering_drawing_id>', methods=['GET'])
@require_oauth(['drawing:dataset'])
def api_get_dataset_by_drawing_id(engineering_drawing_id):
    """API: 根据图纸编号获取数据集列表

    根据图纸文档编号获取所有相关的数据集记录。

    请求格式:
        GET /api/v1/drawing/dataset/by-drawing/<engineering_drawing_id>
        Authorization: Bearer <access_token>

    响应格式:
        {
            "success": true,
            "total": 2,
            "datasets": [
                {
                    "id": 123,
                    "engineering_drawing_id": "DRW-2024-001",
                    "check_time": "2024-12-16 10:30:00",
                    ...
                },
                ...
            ]
        }
    """
    try:
        datasets = DrawingDataset.query.filter_by(
            engineering_drawing_id=engineering_drawing_id
        ).order_by(DrawingDataset.id.desc()).all()

        return jsonify({
            'success': True,
            'total': len(datasets),
            'datasets': [ds.to_dict() for ds in datasets]
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'query_error',
            'error_description': f'查询数据集失败: {str(e)}'
        }), 500


@drawing_api_bp.route('/get-drawing-detection', methods=['POST'])
@require_oauth(['drawing:query'])
def api_query_by_drawing_and_version():
    """API: 根据图纸编号和版本号查询记录

    根据图纸文档编号和版本号查询对应的检测记录，如果有多条记录则返回最新的一条。
    同时返回该记录在drawing_detection表中的12个检测点的详细数据。

    请求格式:
        POST /api/v1/drawing/get-drawing-detection
        Authorization: Bearer <access_token>
        Content-Type: multipart/form-data

    Form Data 参数:
        engineering_drawing_id: 图纸文档编号 (必填)
        version: 版本号 (必填)

    响应格式:
        {
            "success": true,
            "id": 123,
            "engineering_drawing_id": "DRW-001",
            "version": "V1.0",
            "detection_points": [
                {
                    "point": 1,
                    "content": "发现内容1",
                    "result": "符合",
                    "position": "位置描述1",
                    "reason": "符合原因1",
                    "suggest": "修改建议1"
                },
                ...
            ]
        }

    错误响应:
        {
            "error": "not_found",
            "error_description": "未找到匹配的记录"
        }
    """
    try:
        # 从 Form Data 获取参数
        engineering_drawing_id = request.form.get('engineering_drawing_id', '').strip()
        version = request.form.get('version', '').strip()

        # 验证必填参数
        if not engineering_drawing_id:
            return jsonify({
                'error': 'missing_parameter',
                'error_description': '图纸文档编号不能为空'
            }), 400

        if not version:
            return jsonify({
                'error': 'missing_parameter',
                'error_description': '版本号不能为空'
            }), 400

        # 查询记录（按ID降序，获取最新的一条）
        record = DrawingData.query.filter_by(
            engineering_drawing_id=engineering_drawing_id,
            version=version
        ).order_by(DrawingData.id.desc()).first()

        if not record:
            return jsonify({
                'error': 'not_found',
                'error_description': f'未找到图纸编号为 {engineering_drawing_id}、版本号为 {version} 的记录'
            }), 404

        # 查询 drawing_detection 表中的数据
        query = """
            SELECT 
                content_1, result_1, position_1, reason_1, suggest_1,
                content_2, result_2, position_2, reason_2, suggest_2,
                content_3, result_3, position_3, reason_3, suggest_3,
                content_4, result_4, position_4, reason_4, suggest_4,
                content_5, result_5, position_5, reason_5, suggest_5,
                content_6, result_6, position_6, reason_6, suggest_6,
                content_7, result_7, position_7, reason_7, suggest_7,
                content_8, result_8, position_8, reason_8, suggest_8,
                content_9, result_9, position_9, reason_9, suggest_9,
                content_10, result_10, position_10, reason_10, suggest_10,
                content_11, result_11, position_11, reason_11, suggest_11,
                content_12, result_12, position_12, reason_12, suggest_12
            FROM drawing_detection
            WHERE id = :id
        """

        result = db.session.execute(db.text(query), {"id": record.id})
        detection_row = result.fetchone()

        # 构建检测点数据
        detection_points = []
        if detection_row:
            columns = result.keys()
            detection_dict = dict(zip(columns, detection_row))

            # 12个检测点的名称（按固定顺序）
            point_names = [
                '未注公差表检查',
                '公差精确度检测',
                '关键尺寸识别',
                '技术要求检测',
                '人员参数检查',
                '未注公差表检查',
                '安吉尔LOGO检查',
                '图号检查',
                '中文名称检查',
                '材料信息检查',
                '版本号检查',
                '图号检查'
            ]

            # 将12个检测点的数据整理成数组（使用OrderedDict保持字段顺序）
            for i in range(1, 13):
                point_data = OrderedDict([
                    ('检测项目名称', point_names[i - 1]),
                    ('发现内容', detection_dict.get(f'content_{i}', '') or ''),
                    ('检测结果', detection_dict.get(f'result_{i}', '') or ''),
                    ('位置描述', detection_dict.get(f'position_{i}', '') or ''),
                    ('符合/不符合原因', detection_dict.get(f'reason_{i}', '') or ''),
                    ('修改建议', detection_dict.get(f'suggest_{i}', '') or '')
                ])
                detection_points.append(point_data)

        # 返回结果
        return jsonify({
            'success': True,
            'id': record.id,
            'engineering_drawing_id': record.engineering_drawing_id,
            'version': record.version,
            'detection_points': detection_points
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'query_error',
            'error_description': f'查询失败: {str(e)}'
        }), 500
