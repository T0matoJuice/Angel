#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
制图检测数据模型 - 定义制图检测记录的数据库模型
"""
from modules.auth import db


class DrawingData(db.Model):
    """制图检测数据模型 - 映射到 MySQL angel.drawing_data 表

    Attributes:
        id: 主键，自增
        engineering_drawing_id: 检测记录的唯一标识（对应JSON中的id）
        account: 上传用户的账号（username）
        original_filename: 原始文件名
        file_path: 图纸存储路径
        conclusion: 检测结论
        detailed_report: 详细报告（text类型）
        created_at: 上传/检测时间
        checker_name: 检入者姓名
        version: 版本号
        status: 检测状态 (pending/processing/completed/failed)
        error_message: 错误信息（检测失败时）
        completed_at: 检测完成时间
        source: 数据来源 (Web/API)
    """
    __tablename__ = 'drawing_data'  # 映射到 MySQL 的 drawing_data 表

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.String(255), nullable=True)  # 上传/检测时间
    account = db.Column(db.String(255), nullable=True)  # 上传用户账号
    engineering_drawing_id = db.Column(db.String(255), nullable=True)  # 检测记录唯一标识
    original_filename = db.Column(db.String(255), nullable=True)  # 原始文件名
    file_path = db.Column(db.String(255), nullable=True)  # 图纸存储路径
    conclusion = db.Column(db.String(255), nullable=True)  # 检测结论
    detailed_report = db.Column(db.Text, nullable=True)  # 详细报告（text类型）
    checker_name = db.Column(db.String(255), nullable=True)  # 检入者姓名
    version = db.Column(db.String(255), nullable=True)  # 版本号
    engineering_drawing_type = db.Column(db.String(255), nullable=True)  # 图纸类型
    status = db.Column(db.String(50), nullable=True, default='pending')  # 检测状态
    error_message = db.Column(db.Text, nullable=True)  # 错误信息
    completed_at = db.Column(db.String(255), nullable=True)  # 检测完成时间
    source = db.Column(db.String(50), nullable=True, default='Web')  # 数据来源

    def __repr__(self):
        return f'<DrawingData {self.engineering_drawing_id}>'

    def to_dict(self):
        """将模型转换为字典格式（用于API返回）

        Returns:
            dict: 包含所有字段的字典
        """
        return {
            'id': self.id,  # 前端使用
            'engineering_drawing_id': self.engineering_drawing_id,
            'account': self.account,
            'original_filename': self.original_filename,
            'filename': self.original_filename,  # 兼容旧的字段名
            'file_path': self.file_path,
            'conclusion': self.conclusion,
            'detailed_report': self.detailed_report,
            'created_at': self.created_at,
            'timestamp': self.created_at,  # 兼容旧的字段名
            'checker_name': self.checker_name,  # 检入者姓名
            'version': self.version,  # 版本号
            'engineering_drawing_type': self.engineering_drawing_type,  # 图纸类型
            'status': self.status,  # 检测状态
            'error_message': self.error_message,  # 错误信息
            'completed_at': self.completed_at,  # 检测完成时间
            'source': self.source  # 数据来源
        }


class DrawingDataset(db.Model):
    """图纸数据集模型 - 映射到 MySQL angel.drawing_dataset 表

    用于存储图纸检测的详细项目数据，包含12个检测项目的名称、结果和描述。

    Attributes:
        id: 主键，自增
        engineering_drawing_id: 图纸文档编号
        check_time: 检测时间
        flowpath_id: 流程路径ID
        project_1~12: 12个检测项目名称
        result_1~12: 12个检测结果
        describe_1~12: 12个检测描述
    """
    __tablename__ = 'drawing_dataset'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    engineering_drawing_id = db.Column(db.String(255), nullable=True)
    check_time = db.Column(db.String(255), nullable=True)
    flowpath_id = db.Column(db.String(255), nullable=True)

    # 12个检测项目
    project_1 = db.Column(db.String(255), nullable=True)
    result_1 = db.Column(db.String(255), nullable=True)
    describe_1 = db.Column(db.String(255), nullable=True)

    project_2 = db.Column(db.String(255), nullable=True)
    result_2 = db.Column(db.String(255), nullable=True)
    describe_2 = db.Column(db.String(255), nullable=True)

    project_3 = db.Column(db.String(255), nullable=True)
    result_3 = db.Column(db.String(255), nullable=True)
    describe_3 = db.Column(db.String(255), nullable=True)

    project_4 = db.Column(db.String(255), nullable=True)
    result_4 = db.Column(db.String(255), nullable=True)
    describe_4 = db.Column(db.String(255), nullable=True)

    project_5 = db.Column(db.String(255), nullable=True)
    result_5 = db.Column(db.String(255), nullable=True)
    describe_5 = db.Column(db.String(255), nullable=True)

    project_6 = db.Column(db.String(255), nullable=True)
    result_6 = db.Column(db.String(255), nullable=True)
    describe_6 = db.Column(db.String(255), nullable=True)

    project_7 = db.Column(db.String(255), nullable=True)
    result_7 = db.Column(db.String(255), nullable=True)
    describe_7 = db.Column(db.String(255), nullable=True)

    project_8 = db.Column(db.String(255), nullable=True)
    result_8 = db.Column(db.String(255), nullable=True)
    describe_8 = db.Column(db.String(255), nullable=True)

    project_9 = db.Column(db.String(255), nullable=True)
    result_9 = db.Column(db.String(255), nullable=True)
    describe_9 = db.Column(db.String(255), nullable=True)

    project_10 = db.Column(db.String(255), nullable=True)
    result_10 = db.Column(db.String(255), nullable=True)
    describe_10 = db.Column(db.String(255), nullable=True)

    project_11 = db.Column(db.String(255), nullable=True)
    result_11 = db.Column(db.String(255), nullable=True)
    describe_11 = db.Column(db.String(255), nullable=True)

    project_12 = db.Column(db.String(255), nullable=True)
    result_12 = db.Column(db.String(255), nullable=True)
    describe_12 = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<DrawingDataset {self.id} - {self.engineering_drawing_id}>'

    def to_dict(self):
        """将模型转换为字典格式（用于API返回）

        Returns:
            dict: 包含所有字段的字典
        """
        result = {
            'id': self.id,
            'engineering_drawing_id': self.engineering_drawing_id,
            'check_time': self.check_time,
            'flowpath_id': self.flowpath_id,
        }

        # 添加12个检测项目
        for i in range(1, 13):
            result[f'project_{i}'] = getattr(self, f'project_{i}')
            result[f'result_{i}'] = getattr(self, f'result_{i}')
            result[f'describe_{i}'] = getattr(self, f'describe_{i}')

        return result


