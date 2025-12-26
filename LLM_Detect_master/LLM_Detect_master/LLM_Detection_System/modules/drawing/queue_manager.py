#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测任务队列管理模块
实现线程安全的FIFO队列，确保同一时间只有一个检测任务在执行
"""

import threading
import queue
import time
from typing import Dict, Optional
from flask import current_app
from modules.drawing.services import inspect_drawing_api
from modules.drawing.services_try import inspect_drawing_test
from modules.drawing.Identify_drawing_types import identify_drawing_type
from modules.drawing.models import DrawingData
from modules.auth import db
import requests
from requests.auth import HTTPBasicAuth
import os
import pandas as pd
from pathlib import Path
import re
from datetime import datetime


class InspectionQueueManager:
    """检测任务队列管理器

    特性：
    - 线程安全的FIFO队列
    - 同一时间只执行一个检测任务
    - 自动更新数据库状态
    - 支持任务状态查询
    """

    def __init__(self, app=None):
        """初始化队列管理器

        Args:
            app: Flask应用实例（可选）
        """
        self.task_queue = queue.Queue()  # 任务队列
        self.current_task = None  # 当前正在执行的任务
        self.task_status = {}  # 任务状态字典 {record_id: status}
        self.lock = threading.Lock()  # 线程锁
        self.worker_thread = None  # 工作线程
        self.is_running = False  # 运行状态标志
        self.app = app  # Flask应用实例

    def start(self):
        """启动队列处理线程"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
            print("✅ 检测队列管理器已启动")

    def stop(self):
        """停止队列处理线程"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        print("⏹️  检测队列管理器已停止")

    def add_task(self, record_id: str, filepath: str) -> bool:
        """添加检测任务到队列

        Args:
            record_id: 数据库记录ID（drawing_data表的自增ID，转为字符串）
            filepath: 文件路径

        Returns:
            bool: 是否成功添加
        """
        try:
            with self.lock:
                # 检查任务是否已存在且正在处理中
                existing_status = self.task_status.get(record_id)
                if existing_status in ['pending', 'processing']:
                    print(f"⚠️  任务正在处理中: {record_id}, 状态: {existing_status}")
                    return False

                # 如果是已完成或失败的任务，允许重新提交新任务
                if existing_status in ['completed', 'failed', 'error']:
                    print(f"ℹ️  允许重新提交: {record_id}, 旧状态: {existing_status} → 新任务")

                # 添加到队列
                task = {
                    'record_id': record_id,
                    'filepath': filepath,
                    'added_time': time.time()
                }
                self.task_queue.put(task)
                self.task_status[record_id] = 'pending'

                # 更新数据库状态为"排队中"
                self._update_db_status(record_id, 'pending')

                queue_size = self.task_queue.qsize()
                print(f"✅ 任务已加入队列: {record_id}, 队列长度: {queue_size}")
                return True

        except Exception as e:
            print(f"❌ 添加任务失败: {str(e)}")
            return False

    def get_task_status(self, record_id: str) -> Optional[str]:
        """查询任务状态

        Args:
            record_id: 记录ID

        Returns:
            str: 状态 (pending/processing/completed/failed) 或 None
        """
        with self.lock:
            return self.task_status.get(record_id)

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
        print("🔄 队列处理线程已启动")

        while self.is_running:
            try:
                # 从队列获取任务（超时1秒，避免阻塞）
                try:
                    task = self.task_queue.get(timeout=1)
                except queue.Empty:
                    continue

                record_id = task['record_id']
                filepath = task['filepath']

                # 更新当前任务
                with self.lock:
                    self.current_task = record_id
                    self.task_status[record_id] = 'processing'

                print(f"🔍 开始检测任务: {record_id}")

                # 更新数据库状态为"检测中"
                self._update_db_status(record_id, 'processing')

                # 执行检测
                start_time = time.time()
                result = self._execute_inspection(record_id, filepath)
                duration = time.time() - start_time

                # 更新任务状态
                with self.lock:
                    if result['success']:
                        self.task_status[record_id] = 'completed'
                        print(f"✅ 检测完成: {record_id}, 耗时: {duration:.2f}秒")
                    else:
                        self.task_status[record_id] = 'failed'
                        print(f"❌ 检测失败: {record_id}, 原因: {result.get('error', '未知')}")

                    self.current_task = None

                # 标记任务完成
                self.task_queue.task_done()

            except Exception as e:
                print(f"❌ 队列处理异常: {str(e)}")
                with self.lock:
                    if self.current_task:
                        self.task_status[self.current_task] = 'failed'
                        self._update_db_status(self.current_task, 'failed', error=str(e))
                    self.current_task = None

        print("⏹️  队列处理线程已退出")

    def _execute_inspection(self, record_id: str, filepath: str) -> Dict:
        """执行检测并更新数据库

        Args:
            record_id: 记录ID
            filepath: 文件路径

        Returns:
            dict: 检测结果
        """
        try:
            # 获取图纸类型
            drawing_type = None
            if self.app:
                with self.app.app_context():
                    record = DrawingData.query.filter_by(id=int(record_id)).first()
                    if record:
                        drawing_type = record.engineering_drawing_type
                        print(f"📋 图纸类型: {drawing_type}")
                    else:
                        print(f"⚠️  警告: 找不到ID={record_id}的记录")

            # 当 drawing_type 为 "总成图" 时，进行图纸类型识别和Excel对比
            if drawing_type == "CAD文档":
                print(f"🔍 检测到总成图，开始识别图纸类型...")
                
                # 初始化错误消息
                error_message = ""
                
                # 调用图纸类型识别函数
                identified_type = identify_drawing_type(filepath)
                
                # 检查识别结果是否为空
                if not identified_type or identified_type.strip() == "空白" or identified_type.strip() == "[空白]":
                    error_message = "图纸为CAD文件，模型未识别到图纸中的中文名称"
                    print(f"❌ {error_message}")
                    
                    # 输出错误结果到PNG目录下的txt文件
                    png_dir = Path(__file__).resolve().parent / "PNG"
                    png_dir.mkdir(exist_ok=True)
                    
                    result_file = png_dir / f"CAD文件识别结果.txt"
                    
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"记录ID: {record_id}\n")
                        f.write(f"图纸文件: {os.path.basename(filepath)}\n")
                        f.write(f"原始图纸类型: {drawing_type}\n")
                        f.write(f"错误信息: {error_message}\n")
                        f.write(f"{'=' * 80}\n")
                    
                    print(f"✅ 识别结果已保存到: {result_file}")
                    print(f"🛑 实验模式：CAD文件类型识别失败，终止检测流程")
                    
                    # 更新数据库状态和错误信息，便于前端显示
                    engineering_id = None
                    if self.app:
                        with self.app.app_context():
                            record = DrawingData.query.filter_by(id=int(record_id)).first()
                            if record:
                                record.status = 'failed'
                                record.error_message = error_message
                                record.completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                engineering_id = record.engineering_drawing_id
                                db.session.commit()
                                print(f"✅ 数据库状态已更新: status=failed, completed_at={record.completed_at}")
                    
                    # 向远程接口发送失败通知
                    try:
                        remote_url = "http://plmtest.angelgroup.com.cn:8090/Windchill/ptc1/aiInterface/customUpload/sendEpmInfo"
                        username = "plmSysInt"
                        password = "plmSysInt"
                        
                        data = {
                            "id": record_id,
                            "epmDocNumber": engineering_id,
                            "detectionResults": None,
                            "type": "failed",
                            "message": error_message,
                            "detectionTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        print(f"📤 向远程接口发送失败通知: {remote_url}")
                        resp = requests.post(
                            remote_url,
                            auth=HTTPBasicAuth(username, password),
                            data=data,
                            timeout=60
                        )
                        print(f"✅ 远程通知响应: {resp.status_code} - {resp.text}")
                    except requests.RequestException as e:
                        print(f"⚠️  远程通知失败: {e}")
                    except Exception as e:
                        print(f"⚠️  远程通知异常: {e}")
                    
                    # 返回失败
                    return {'success': False, 'error': error_message}
                
                print(f"✅ 原始识别结果: {identified_type}")
                
                # 去除【】符号
                identified_type = re.sub(r'[\[\]【】]', '', identified_type).strip()
                print(f"✅ 处理后识别结果: {identified_type}")
                
                # Excel文件对比逻辑
                excel_dir = Path(__file__).resolve().parent / "EXCEL"
                excel_files = [
                    ("metal.xlsx", "金属件"),
                    ("plastics.xlsx", "塑胶件"),
                    ("electrical.xlsx", "电器件")
                ]
                
                matched_type = "无匹配项"
                matched_in_file = None
                
                # 依次对比三个Excel文件
                for excel_file, type_name in excel_files:
                    excel_path = excel_dir / excel_file
                    
                    if not excel_path.exists():
                        print(f"⚠️  警告: Excel文件不存在 - {excel_path}")
                        continue
                    
                    try:
                        # 读取Excel文件
                        df = pd.read_excel(excel_path)
                        print(f"📄 正在对比 {excel_file}...")
                        
                        # 遍历所有单元格进行对比
                        found = False
                        for col in df.columns:
                            if df[col].astype(str).str.contains(identified_type, na=False).any():
                                matched_type = type_name
                                matched_in_file = excel_file
                                found = True
                                print(f"✅ 在 {excel_file} 中找到匹配: {identified_type} -> {type_name}")
                                break
                        
                        if found:
                            break  # 找到匹配后终止对比
                            
                    except Exception as e:
                        print(f"❌ 读取Excel文件失败 {excel_file}: {str(e)}")
                        continue
                
                # 检查匹配结果
                if matched_type == "无匹配项":
                    error_message = "图纸为CAD文件，在所给物料表格中未找到匹配项"
                    print(f"⚠️  {error_message}")
                    
                    # 输出无匹配结果到PNG目录下的txt文件
                    png_dir = Path(__file__).resolve().parent / "PNG"
                    png_dir.mkdir(exist_ok=True)
                    
                    result_file = png_dir / f"CAD文件识别结果.txt"
                    
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"记录ID: {record_id}\n")
                        f.write(f"图纸文件: {os.path.basename(filepath)}\n")
                        f.write(f"原始图纸类型: {drawing_type}\n")
                        f.write(f"模型识别结果: {identified_type}\n")
                        f.write(f"错误信息: {error_message}\n")
                        f.write(f"{'=' * 80}\n")
                    
                    print(f"✅ 识别结果已保存到: {result_file}")
                    print(f"🛑 实验模式：CAD文件类型识别完成，终止检测流程")
                    
                    # 更新数据库状态和错误信息，便于前端显示
                    engineering_id = None
                    if self.app:
                        with self.app.app_context():
                            record = DrawingData.query.filter_by(id=int(record_id)).first()
                            if record:
                                record.status = 'failed'
                                record.error_message = error_message
                                record.completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                engineering_id = record.engineering_drawing_id
                                db.session.commit()
                                print(f"✅ 数据库状态已更新: status=failed, completed_at={record.completed_at}")
                    
                    # 向远程接口发送失败通知
                    try:
                        remote_url = "http://plmtest.angelgroup.com.cn:8090/Windchill/ptc1/aiInterface/customUpload/sendEpmInfo"
                        username = "plmSysInt"
                        password = "plmSysInt"
                        
                        data = {
                            "id": record_id,
                            "epmDocNumber": engineering_id,
                            "detectionResults": None,
                            "type": "failed",
                            "message": error_message,
                            "detectionTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        print(f"📤 向远程接口发送失败通知: {remote_url}")
                        resp = requests.post(
                            remote_url,
                            auth=HTTPBasicAuth(username, password),
                            data=data,
                            timeout=60
                        )
                        print(f"✅ 远程通知响应: {resp.status_code} - {resp.text}")
                    except requests.RequestException as e:
                        print(f"⚠️  远程通知失败: {e}")
                    except Exception as e:
                        print(f"⚠️  远程通知异常: {e}")
                    
                    # 返回失败
                    return {'success': False, 'error': error_message}
                else:
                    # 匹配成功，更新drawing_type为matched_type
                    drawing_type = matched_type
                    print(f"✅ 图纸类型已更新为: {drawing_type}")
                    
                    # 输出成功结果到PNG目录下的txt文件
                    png_dir = Path(__file__).resolve().parent / "PNG"
                    png_dir.mkdir(exist_ok=True)
                    
                    result_file = png_dir / f"CAD文件识别结果.txt"
                    
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"记录ID: {record_id}\n")
                        f.write(f"图纸文件: {os.path.basename(filepath)}\n")
                        f.write(f"原始图纸类型: CAD文件\n")
                        f.write(f"模型识别结果: {identified_type}\n")
                        f.write(f"匹配文件: {matched_in_file}\n")
                        f.write(f"最终类型: {matched_type}\n")
                        f.write(f"{'=' * 80}\n")
                    
                    print(f"✅ 识别结果已保存到: {result_file}")
                    print(f"✅ 继续进行 {drawing_type} 类型的常规检测...")

            # 调用测试检测函数,传入图纸类型
            result = inspect_drawing_test(filepath, drawing_type)

            if 'error' in result:
                # 检测失败
                self._update_db_status(
                    record_id,
                    'failed',
                    error=result['error']
                )
                
                # 获取engineering_id用于远程通知
                engineering_id = None
                if self.app:
                    with self.app.app_context():
                        record = DrawingData.query.filter_by(id=int(record_id)).first()
                        if record:
                            engineering_id = record.engineering_drawing_id
                
                # 向远程接口发送失败通知
                try:
                    remote_url = "http://plmtest.angelgroup.com.cn:8090/Windchill/ptc1/aiInterface/customUpload/sendEpmInfo"
                    username = "plmSysInt"
                    password = "plmSysInt"
                    
                    data = {
                        "id": record_id,
                        "epmDocNumber": engineering_id,
                        "detectionResults": None,
                        "type": "failed",
                        "message": "检测失败: PDF文件损坏、格式不正确或文件内容为空",
                        "detectionTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    print(f"📤 向远程接口发送失败通知: {remote_url}")
                    resp = requests.post(
                        remote_url,
                        auth=HTTPBasicAuth(username, password),
                        data=data,
                        timeout=60
                    )
                    print(f"✅ 远程通知响应: {resp.status_code} - {resp.text}")
                except requests.RequestException as e:
                    print(f"⚠️  远程通知失败: {e}")
                except Exception as e:
                    print(f"⚠️  远程通知异常: {e}")
                
                return {'success': False, 'error': result['error']}

            timestamp = result.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))

            # 检测成功，更新数据库
            self._update_db_result(
                record_id,
                conclusion=result.get('conclusion', '未知'),
                detailed_report=result.get('detailed_report', ''),
                timestamp=timestamp
            )

            # record_id 现在是数据库自增ID，需要查询获取 engineering_drawing_id
            db_id = record_id
            engineering_id = None
            status_value = None
            if self.app:
                with self.app.app_context():
                    record = DrawingData.query.filter_by(id=int(record_id)).first()
                    if record:
                        engineering_id = record.engineering_drawing_id
                        status_value = record.status
                    else:
                        print(f"⚠️  警告: 找不到ID={record_id}的记录")

            # 检查detailed_report第一行是否包含错误关键词
            detailed_report = result.get('detailed_report', '')
            if detailed_report:
                first_line = detailed_report.split('\n')[0].strip()
                error_keywords = ["无法直接获取图纸", "无法获取图纸", "Base64编码", "Base64"]
                if any(keyword in first_line for keyword in error_keywords):
                    status_value = 'error'

            # 如果检测成功完成，生成PDF报告
            if status_value == 'completed':
                try:
                    # 导入报告生成模块（同一目录下）
                    from modules.drawing.generate_drawing_report import process_drawing_report

                    # 生成PDF报告（在应用上下文中执行）
                    print(f"📄 开始生成PDF报告: {record_id}")
                    if self.app:
                        with self.app.app_context():
                            report_success = process_drawing_report(record_id, filepath)
                            if report_success:
                                print(f"✅ PDF报告生成成功: {record_id}")
                            else:
                                print(f"⚠️  PDF报告生成失败: {record_id}")
                    else:
                        print(f"⚠️  无法生成PDF报告: Flask应用上下文不可用")
                except Exception as e:
                    print(f"❌ PDF报告生成异常: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # 获取检测结论
            conclusion = result.get('conclusion', '未知')
            result = self.upload_result_to_auth(filepath, timestamp, db_id, engineering_id, status_value, conclusion)

            return {'success': True, 'result': result}

        except Exception as e:
            error_msg = f"检测异常: {str(e)}"
            self._update_db_status(record_id, 'failed', error=error_msg)
            return {'success': False, 'error': error_msg}

    @staticmethod
    def upload_result_to_auth(local_file_path: str, detectionTime: str, db_id: str, engineering_id: str,
                              status_value: str, conclusion: str) -> str:

        remote_url = "http://plmtest.angelgroup.com.cn:8090/Windchill/ptc1/aiInterface/customUpload/sendEpmInfo"
        username = "plmSysInt"
        password = "plmSysInt"

        """
        上传 Excel 文件到远程接口（带 Basic 认证）
        :return: 上传结果描述
        """
        # 1. 文件存在性检查
        if not os.path.isfile(local_file_path):
            return f"错误：本地文件不存在 - {local_file_path}"

        file_size = os.path.getsize(local_file_path)
        print("=== 开始文件上传 ===")
        print(f"文件路径: {local_file_path}")
        print(f"文件大小: {file_size} bytes")
        print(f"目标URL: {remote_url}")

        # 2. 构造 multipart/form-data
        with open(local_file_path, "rb") as f:
            files = {"file": (os.path.basename(local_file_path),
                              f,
                              "application/octet-stream")}

            # 根据status_value设置message
            if status_value == 'failed':
                message_text = "系统识别失败，请重新上传"
            else:
                message_text = ""

            data = {
                # id 使用 drawing_data 主键，epmDocNumber 使用 engineering_drawing_id
                "id": db_id,
                "epmDocNumber": engineering_id,
                "detectionResults": conclusion,
                # 根据状态决定 message
                "type": 'success' if status_value == 'completed' else status_value,
                "message": message_text,
                "detectionTime": detectionTime
            }

            # 3. 发送 POST（带 Basic 认证）
            try:
                resp = requests.post(remote_url,
                                     auth=HTTPBasicAuth(username, password),
                                     files=files,
                                     data=data,
                                     timeout=60)
            except requests.RequestException as e:
                return f"文件上传异常: {e}"

        # 4. 处理响应
        print(f"HTTP状态码: {resp.status_code}")
        print(f"服务器响应: {resp.text}")

        if resp.status_code == 200:
            return "文件上传成功！"
        else:
            return f"文件上传失败！状态码: {resp.status_code}"

    def _update_db_status(self, record_id: str, status: str, error: str = None):
        """更新数据库记录状态

        Args:
            record_id: 数据库记录ID（自增ID）
            status: 状态值
            error: 错误信息

        Args:
            record_id: 记录ID
            status: 状态值
            error: 错误信息（可选）
        """
        if not self.app:
            print(f"⚠️  警告: Flask应用未设置，无法更新数据库状态")
            return

        try:
            with self.app.app_context():
                # 使用自增ID查询
                record = DrawingData.query.filter_by(id=int(record_id)).first()

                if record:
                    record.status = status
                    if error:
                        record.error_message = error
                    db.session.commit()
                else:
                    print(f"⚠️  警告: 找不到ID={record_id}的记录")

        except Exception as e:
            try:
                with self.app.app_context():
                    db.session.rollback()
            except:
                pass
            print(f"❌ 更新数据库状态失败: {str(e)}")

    def _update_db_result(self, record_id: str, conclusion: str,
                          detailed_report: str, timestamp: str):
        """更新数据库检测结果

        Args:
            record_id: 记录ID
            conclusion: 检测结论
            detailed_report: 详细报告
            timestamp: 时间戳
        """
        if not self.app:
            print(f"⚠️  警告: Flask应用未设置，无法更新数据库结果")
            return

        try:
            with self.app.app_context():
                # 使用自增ID查询
                record = DrawingData.query.filter_by(id=int(record_id)).first()

                if record:
                    record.conclusion = conclusion
                    record.detailed_report = detailed_report
                    record.status = 'completed'
                    record.completed_at = timestamp
                    db.session.commit()
                else:
                    print(f"⚠️  警告: 找不到ID={record_id}的记录")

        except Exception as e:
            try:
                with self.app.app_context():
                    db.session.rollback()
            except:
                pass
            print(f"❌ 更新检测结果失败: {str(e)}")


# 全局队列管理器实例
_queue_manager = None


def get_queue_manager(app=None) -> InspectionQueueManager:
    """获取全局队列管理器实例（单例模式）

    Args:
        app: Flask应用实例（首次调用时必须提供）

    Returns:
        InspectionQueueManager: 队列管理器实例
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
        _queue_manager = InspectionQueueManager(app)
        _queue_manager.start()
    return _queue_manager


