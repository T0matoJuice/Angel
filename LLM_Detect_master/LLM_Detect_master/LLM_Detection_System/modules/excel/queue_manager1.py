#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel质量工单检测队列管理模块
实现线程安全的FIFO队列，支持批量工单的异步AI检测处理
"""

import threading
import queue
import time
import sys
import json
from typing import Dict, Optional, List, Any
from flask import current_app
from modules.excel.processor import Processor
from modules.excel.models import WorkorderData
from modules.auth import db
import traceback
import requests


class ExcelQueueManager:
    """Excel质量工单检测队列管理器

    特性：
    - 线程安全的FIFO队列
    - 支持批量工单检测
    - 自动更新数据库状态
    - 支持任务状态查询
    - 错误恢复机制
    """

    def __init__(self, app=None):
        """初始化队列管理器

        Args:
            app: Flask应用实例（可选）
        """
        self.task_queue = queue.Queue()  # 任务队列
        self.current_task = None  # 当前正在执行的任务
        self.task_status = {}  # 任务状态字典 {filename: status}
        self.task_results = {}  # 任务结果字典 {filename: {csv_filename, excel_filename}}
        self.lock = threading.Lock()  # 线程锁
        self.worker_thread = None  # 工作线程
        self.is_running = False  # 运行状态标志
        self.app = app  # Flask应用实例
        self.processor = None  # Excel处理器实例

    @staticmethod
    def _fetch_token() -> str:
        """调用外部登录接口获取 access_token。"""
        url = "http://qmstest.angelgroup.com.cn:8080/ssoServer/oauth/login"
        headers = {
            "Authorization": "Basic cXVhbGl0eURhdGE6JDJhJDEwJGZDOU40WUxOWUlCLzgyM3ZQcjd2b2U3dWtndUtHSkRNYzdya210UmkxeHVCQ0lZZUcwMkJX",
            "Content-Type": "application/json",
        }
        payload = {
            "username": "ai",
            "password": "Ai@2025."
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()

        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError("登录接口返回非JSON")

        token = (
            data.get("access_token")
            or data.get("token")
            or (data.get("data", {}) if isinstance(data, dict) else {}).get("access_token")
        )

        if not token:
            raise RuntimeError("登录接口未返回 access_token")

        return token

    @staticmethod
    def _submit_judgment(access_token: str, payload: Any) -> Dict:
        """提交工单判定数据到外部接口。"""
        url = "http://qmstest.angelgroup.com.cn:8080/qualityDataAnalysis/baseData/crmMaintenanceData/aiSubmitJudgment"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()

        try:
            return resp.json()
        except ValueError:
            return {"raw": resp.text}
        
    def start(self):
        """启动队列处理线程"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
            print("✅ Excel检测队列管理器已启动")
    
    def stop(self):
        """停止队列处理线程"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        print("⏹️  Excel检测队列管理器已停止")
    
    def add_task(self, filename: str, filepath: str, batch_size: int = 50) -> bool:
        """添加检测任务到队列
        
        Args:
            filename: 数据库中的唯一文件名（带时间戳）
            filepath: 实际上传的Excel文件路径
            batch_size: 每批处理的工单数量
            
        Returns:
            bool: 是否成功添加
        """
        try:
            with self.lock:
                # 检查任务是否已存在
                if filename in self.task_status:
                    print(f"⚠️  任务已存在: {filename}")
                    return False
                
                # 添加到队列
                task = {
                    'filename': filename,
                    'filepath': filepath,
                    'batch_size': batch_size,
                    'added_time': time.time()
                }
                self.task_queue.put(task)
                self.task_status[filename] = 'pending'
                
                queue_size = self.task_queue.qsize()
                print(f"✅ Excel检测任务已加入队列: {filename}, 队列长度: {queue_size}")
                return True
                
        except Exception as e:
            print(f"❌ 添加任务失败: {str(e)}")
            return False
    
    def get_task_status(self, filename: str) -> Optional[str]:
        """查询任务状态
        
        Args:
            filename: 文件名
            
        Returns:
            str: 状态 (pending/processing/completed/failed) 或 None
        """
        with self.lock:
            return self.task_status.get(filename)
    
    def get_task_result(self, filename: str) -> Optional[Dict]:
        """查询任务结果（包含生成的文件名）
        
        Args:
            filename: 文件名
            
        Returns:
            dict: 结果信息 {csv_filename, excel_filename} 或 None
        """
        with self.lock:
            return self.task_results.get(filename)
    
    def get_queue_info(self) -> Dict:
        """获取队列信息
        
        Returns:
            dict: 队列统计信息
        """
        with self.lock:
            return {
                'queue_size': self.task_queue.qsize(),
                'current_task': self.current_task,
                'total_tasks': len(self.task_status),
                'is_running': self.is_running
            }
    
    def _process_queue(self):
        """队列处理主循环（在独立线程中运行）"""
        print("🔄 Excel检测队列处理线程已启动")
        
        while self.is_running:
            try:
                # 从队列获取任务（超时1秒，避免阻塞）
                try:
                    task = self.task_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                filename = task['filename']
                filepath = task['filepath']
                batch_size = task.get('batch_size', 50)
                
                # 更新当前任务
                with self.lock:
                    self.current_task = filename
                    self.task_status[filename] = 'processing'
                
                print(f"🔍 开始检测Excel任务: {filename}")
                print(f"📊 批量处理大小: {batch_size} 条/批")
                
                # 执行检测
                start_time = time.time()
                result = self._execute_inspection(filename, filepath, batch_size)
                duration = time.time() - start_time
                
                # 更新任务状态
                with self.lock:
                    if result['success']:
                        self.task_status[filename] = 'completed'
                        print(f"✅ Excel检测完成: {filename}, 耗时: {duration:.2f}秒, 处理: {result.get('processed_count', 0)}条")
                    else:
                        self.task_status[filename] = 'failed'
                        print(f"❌ Excel检测失败: {filename}, 原因: {result.get('error', '未知')}")
                    
                    self.current_task = None
                
                # 标记任务完成
                self.task_queue.task_done()
                
            except Exception as e:
                print(f"❌ 队列处理异常: {str(e)}")
                print(traceback.format_exc())
                with self.lock:
                    if self.current_task:
                        self.task_status[self.current_task] = 'failed'
                    self.current_task = None
        
        print("⏹️  Excel检测队列处理线程已退出")
    
    def _execute_inspection(self, filename: str, filepath: str, batch_size: int) -> Dict:
        """执行Excel检测并更新数据库
        
        Args:
            filename: 数据库中的文件名
            filepath: Excel文件路径
            batch_size: 批量处理大小
            
        Returns:
            dict: 检测结果
        """
        try:
            # 初始化处理器
            if not self.processor:
                self.processor = Processor()
            
            # 固定的训练工单路径
            if self.app:
                with self.app.app_context():
                    training_file = f"{self.app.root_path}/data/训练数据新100条.xlsx"
            else:
                training_file = "data/训练数据新100条.xlsx"
            
            print(f"📚 使用训练文件: {training_file}")
            
            # 调用分批处理方法（必须在应用上下文中）
            print(f"🚀 开始分批AI质量判断...")
            
            if self.app:
                with self.app.app_context():
                    quality_result, usage_stats, processed_count = self.processor.batch_process_quality_from_db(
                        filename=filename,
                        training_excel=training_file,
                        batch_size=batch_size
                    )
            else:
                error_msg = "Flask应用上下文未初始化"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
            
            if not quality_result:
                error_msg = "分批处理未返回结果"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
            
            print(f"✅ AI判断完成，共处理: {processed_count}条记录")
            
            # 解析CSV结果并回写数据库
            import pandas as pd
            from io import StringIO
            
            try:
                df_result = pd.read_csv(StringIO(quality_result), dtype=str, encoding='utf-8')
                print(f"📝 CSV结果包含 {len(df_result)} 行数据")
            except Exception as e:
                error_msg = f"CSV解析失败: {str(e)}"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
            
            # 回写工单性质和判定依据到数据库
            updated_count = 0
            not_found_count = 0
            records_payload = []
            
            if self.app:
                with self.app.app_context():
                    for index, row in df_result.iterrows():
                        work_alone = str(row.get('工单单号', '')).strip()
                        work_order_nature = str(row.get('工单性质', '')).strip()
                        judgment_basis = str(row.get('判定依据', '')).strip()
                        records_payload.append({
                            "workAlone": work_alone,
                            "workOrderNature": work_order_nature,
                            "judgmentBasis": judgment_basis
                        })
                        
                        if not work_alone or work_alone == 'nan':
                            continue
                        
                        # 查询数据库记录
                        record = WorkorderData.query.filter_by(
                            workAlone=work_alone,
                            filename=filename
                        ).first()
                        
                        if record:
                            # 更新工单性质和判定依据
                            record.workOrderNature = work_order_nature if work_order_nature and work_order_nature != 'nan' else None
                            record.judgmentBasis = judgment_basis if judgment_basis and judgment_basis != 'nan' else None
                            updated_count += 1
                        else:
                            not_found_count += 1
                    
                    # 提交更新
                    db.session.commit()
                    print(f"💾 数据库更新完成: 成功更新 {updated_count} 条记录")
                    
                    if not_found_count > 0:
                        print(f"⚠️  未找到 {not_found_count} 条记录")
            
            # 将判定结果上报到外部接口
            try:
                token = self._fetch_token()
                submit_resp = self._submit_judgment(token, records_payload)
                print("🚀 已提交判定结果到外部接口")
                print(json.dumps(submit_resp, ensure_ascii=False, indent=2) if isinstance(submit_resp, dict) else submit_resp)
            except Exception as e:
                print(f"⚠️  提交判定结果到外部接口失败: {e}")

            return {
                'success': True,
                'processed_count': processed_count,
                'updated_count': updated_count,
                'not_found_count': not_found_count
            }
            
        except Exception as e:
            error_msg = f"检测异常: {str(e)}"
            print(f"❌ {error_msg}")
            print(traceback.format_exc())
            return {'success': False, 'error': error_msg}


# 全局队列管理器实例
_queue_manager = None


def get_queue_manager(app=None) -> ExcelQueueManager:
    """获取全局队列管理器实例（单例模式）

    Args:
        app: Flask应用实例（首次调用时必须提供）

    Returns:
        ExcelQueueManager: 队列管理器实例
    """
    global _queue_manager
    if _queue_manager is None:
        if app is None:
            # 尝试从Flask上下文获取应用实例
            try:
                app = current_app._get_current_object()
            except RuntimeError:
                raise RuntimeError(
                    "首次调用 get_queue_manager() 时必须提供 Flask 应用实例，"
                    "或在 Flask 应用上下文中调用"
                )
        _queue_manager = ExcelQueueManager(app)
        _queue_manager.start()
    return _queue_manager
