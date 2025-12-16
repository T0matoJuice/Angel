#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史记录管理模块
"""

import os
import json
import time
from flask import current_app

def save_detection_history(filename, conclusion, detailed_report, timestamp):
    """保存检测历史记录"""
    try:
        history_file = os.path.join(current_app.config['HISTORY_FOLDER'], 'detection_history.json')

        # 创建新的历史记录
        new_record = {
            'id': str(int(time.time() * 1000)),  # 使用毫秒时间戳作为ID
            'filename': filename,
            'original_filename': filename.split('_', 1)[1] if '_' in filename else filename,
            'conclusion': conclusion,
            'detailed_report': detailed_report,
            'timestamp': timestamp,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # 读取现有历史记录
        history_records = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_records = json.load(f)
            except:
                history_records = []

        # 添加新记录到列表开头
        history_records.insert(0, new_record)

        # 限制历史记录数量
        max_records = current_app.config['MAX_HISTORY_RECORDS']
        if len(history_records) > max_records:
            history_records = history_records[:max_records]

        # 保存更新后的历史记录
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_records, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"保存历史记录失败: {e}")
        return False

def get_detection_history():
    """获取制图检测历史记录"""
    try:
        history_file = os.path.join(current_app.config['HISTORY_FOLDER'], 'detection_history.json')

        if not os.path.exists(history_file):
            return []

        with open(history_file, 'r', encoding='utf-8') as f:
            history_records = json.load(f)

        return history_records

    except Exception as e:
        print(f"读取制图检测历史记录失败: {e}")
        return []

def save_excel_history(filename, original_filename, rows_processed, timestamp):
    """保存Excel处理历史记录"""
    try:
        history_file = os.path.join(current_app.config['HISTORY_FOLDER'], 'excel_history.json')

        # 创建新的历史记录
        new_record = {
            'id': str(int(time.time() * 1000)),  # 使用毫秒时间戳作为ID
            'filename': filename,
            'original_filename': original_filename,
            'rows_processed': rows_processed,
            'timestamp': timestamp,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # 读取现有历史记录
        history_records = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_records = json.load(f)
            except:
                history_records = []

        # 添加新记录到列表开头
        history_records.insert(0, new_record)

        # 限制历史记录数量
        max_records = current_app.config['MAX_HISTORY_RECORDS']
        if len(history_records) > max_records:
            history_records = history_records[:max_records]

        # 保存更新后的历史记录
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_records, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"保存Excel处理历史记录失败: {e}")
        return False

def get_excel_history():
    """获取Excel处理历史记录"""
    try:
        history_file = os.path.join(current_app.config['HISTORY_FOLDER'], 'excel_history.json')

        if not os.path.exists(history_file):
            return []

        with open(history_file, 'r', encoding='utf-8') as f:
            history_records = json.load(f)

        return history_records

    except Exception as e:
        print(f"读取Excel处理历史记录失败: {e}")
        return []
