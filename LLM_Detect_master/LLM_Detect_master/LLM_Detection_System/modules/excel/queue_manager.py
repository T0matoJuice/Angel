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
                # 检查任务状态
                current_status = self.task_status.get(filename)
                
                # 如果任务正在处理中或排队中，拒绝重复添加
                if current_status in ['pending', 'processing']:
                    print(f"⚠️  任务正在处理中: {filename}, 状态: {current_status}")
                    return False
                
                # 如果任务已完成或失败，允许重新添加（清理旧状态）
                if current_status in ['completed', 'failed']:
                    print(f"🔄 清理旧任务状态: {filename}, 旧状态: {current_status}")
                    # 清理旧的结果缓存
                    self.task_results.pop(filename, None)
                
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
                batch_size = task.get('batch_size', 5)
                max_workers = task.get('max_workers', 10)
                batch_size = 1

                # 更新当前任务
                with self.lock:
                    self.current_task = filename
                    self.task_status[filename] = 'processing'
                
                print(f"🔍 开始检测Excel任务: {filename}")
                print(f"📊 批量处理大小: {batch_size} 条/批")
                print(f"📊 最大线程数: {max_workers} ")

                # 执行检测
                start_time = time.time()
                result = self._execute_inspection(filename, filepath, batch_size, max_workers)
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
    
    def _execute_inspection(self, filename: str, filepath: str, batch_size: int, max_workers: int) -> Dict:
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
                        batch_size=batch_size,
                        max_workers=max_workers
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
                # 检查CSV是否有正确的表头
                lines = quality_result.strip().split('\n')
                if not lines:
                    error_msg = "CSV结果为空"
                    print(f"❌ {error_msg}")
                    return {'success': False, 'error': error_msg}
                
                # 检查第一行是否是表头
                first_line = lines[0]
                expected_header = '工单单号,工单性质,判定依据'
                
                if not first_line.startswith('工单单号'):
                    print(f"⚠️  警告: CSV缺少表头，自动添加")
                    # 添加标准表头
                    standard_header = '工单单号,工单性质,判定依据,保内保外,批次入库日期,安装日期,购机日期,产品名称,开发主体,故障部位名称,故障组,故障类别,服务项目或故障现象,维修方式,旧件名称,新件名称,来电内容,现场诊断故障现象,处理方案简述或备注'
                    quality_result = standard_header + '\n' + quality_result
                
                
                df_result = pd.read_csv(StringIO(quality_result), dtype=str, encoding='utf-8')
                print(f"📝 CSV结果包含 {len(df_result)} 行数据")
                
                # 调试：打印CSV的列名
                print(f"🔍 CSV列名: {df_result.columns.tolist()}")
                
                # 调试：打印第一行数据
                if len(df_result) > 0:
                    first_row = df_result.iloc[0]
                    print(f"🔍 第一行数据示例:")
                    print(f"   工单单号: '{first_row.get('工单单号', 'N/A')}'")
                    print(f"   工单性质: '{first_row.get('工单性质', 'N/A')}'")
                
                # 验证数据行数
                if len(df_result) != processed_count:
                    print(f"⚠️  警告: CSV行数({len(df_result)})与处理记录数({processed_count})不一致")
                    print(f"   可能原因: AI输出不完整或包含额外的空行")
                
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

                        if not work_alone or work_alone == 'nan':
                            continue
                        
                        # 调试：打印查询条件（只打印前3条）
                        if index < 3:
                            print(f"🔍 查询条件[{index}]: workAlone='{work_alone}', filename='{filename}'")
                        
                        # 查询数据库记录 - 使用 .all() 获取所有匹配的记录
                        records = WorkorderData.query.filter_by(
                            workAlone=work_alone,
                            filename=filename
                        ).all()

                        if records:
                            records_payload.append({
                                "workAlone": work_alone,
                                "workOrderNature": work_order_nature,
                                "judgmentBasis": judgment_basis
                            })
                            # 更新所有匹配的记录
                            for record in records:
                                record.workOrderNature = work_order_nature if work_order_nature and work_order_nature != 'nan' else None
                                record.judgmentBasis = judgment_basis if judgment_basis and judgment_basis != 'nan' else None
                                updated_count += 1
                            
                            if index < 3:
                                print(f"   ✅ 找到 {len(records)} 条记录，已全部更新")
                        else:
                            not_found_count += 1
                            if index < 3:
                                print(f"   ❌ 未找到记录")
                    
                    # 提交更新
                    db.session.commit()
                    print(f"💾 数据库更新完成: 成功更新 {updated_count} 条记录")
                    
                    if not_found_count > 0:
                        print(f"⚠️  未找到 {not_found_count} 条记录")
            
            # 将判定结果上报到外部接口
            try:
                token = self._fetch_token()
                # submit_resp = self._submit_judgment(token, records_payload)
                # print(f"🚀 已提交判定结果 {len(records_payload)}条 到外部接口")
                print("判定结果未提交到外部接口（此处代码被注释掉以防止实际调用）")
                # print(json.dumps(submit_resp, ensure_ascii=False, indent=2) if isinstance(submit_resp, dict) else submit_resp)
            except Exception as e:
                print(f"⚠️  提交判定结果 {len(records_payload)}条 到外部接口失败: {e}")

            # ========================================
            # 新增：生成Excel结果文件
            # ========================================
            print("🔨 正在生成Excel结果文件...")

            try:
                if self.app:
                    with self.app.app_context():
                        from modules.excel.models import WorkorderUselessdata1, WorkorderUselessdata2

                        # 1. 一次性查询所有主表记录
                        records = WorkorderData.query.filter_by(filename=filename).all()

                        if not records:
                            print(f"⚠️  没有找到文件 {filename} 的记录")
                            return {
                                'success': True,
                                'processed_count': processed_count,
                                'updated_count': updated_count,
                                'not_found_count': not_found_count,
                                'excel_generated': False,
                                'total_rows': 0
                            }

                        # 2. 提取所有工单号用于批量查询
                        work_alone_list = [record.workAlone for record in records if record.workAlone]
                        print(f"📊 开始处理 {len(work_alone_list)} 条工单记录")

                        # 3. 批量查询 WorkorderUselessdata1 表
                        u1_records = WorkorderUselessdata1.query.filter(
                            WorkorderUselessdata1.filename == filename,
                            WorkorderUselessdata1.workAlone.in_(work_alone_list)
                        ).all()

                        # 构建 u1 的映射字典 {workAlone: u1_record}
                        u1_dict = {u.workAlone: u for u in u1_records}

                        # 4. 批量查询 WorkorderUselessdata2 表
                        u2_records = WorkorderUselessdata2.query.filter(
                            WorkorderUselessdata2.filename == filename,
                            WorkorderUselessdata2.workAlone.in_(work_alone_list)
                        ).all()

                        # 构建 u2 的映射字典 {workAlone: u2_record}
                        u2_dict = {u.workAlone: u for u in u2_records}

                        print(f"✅ 批量查询完成: u1记录={len(u1_records)}, u2记录={len(u2_records)}")

                        # 5. 定义19个字段
                        expected_columns = [
                            '工单单号', '工单性质', '判定依据', '保内保外', '批次入库日期', '安装日期',
                            '购机日期', '产品名称', '开发主体', '故障部位名称', '故障组', '故障类别',
                            '服务项目或故障现象', '维修方式', '旧件名称', '新件名称', '来电内容',
                            '现场诊断故障现象', '处理方案简述或备注'
                        ]

                        # 6. 优化后的规范化函数（预先编译正则，减少函数调用开销）
                        def norm_fast(v):
                            """快速规范化函数"""
                            if v is None:
                                return ''
                            if isinstance(v, str) and v == 'None':
                                return ''
                            if isinstance(v, float) and pd.isna(v):
                                return ''
                            return str(v)

                        # 7. 使用列表推导式快速构建数据
                        import time
                        start_time = time.time()

                        # 预定义字段获取函数，减少循环中的属性查找
                        temp_data = []
                        for record in records:
                            work_alone = record.workAlone

                            # 从字典中获取关联记录（O(1)时间复杂度）
                            u1 = u1_dict.get(work_alone)
                            u2 = u2_dict.get(work_alone)

                            # 构建行数据 - 直接赋值，减少中间变量
                            row_data = [
                                # 工单单号
                                norm_fast(work_alone),
                                # 工单性质
                                norm_fast(record.workOrderNature),
                                # 判定依据
                                norm_fast(record.judgmentBasis),
                                # 保内保外
                                norm_fast(u1.internalExternalInsurance if u1 else ''),
                                # 批次入库日期
                                norm_fast(u1.batchWarehousingDate if u1 else ''),
                                # 安装日期
                                norm_fast(u1.installDate if u1 else ''),
                                # 购机日期
                                norm_fast(u1.purchaseDate if u1 else ''),
                                # 产品名称
                                norm_fast(u1.productName if u1 else ''),
                                # 开发主体
                                norm_fast(u1.developmentSubject if u1 else ''),
                                # 故障部位名称
                                norm_fast(record.replacementPartName),
                                # 故障组
                                norm_fast(record.faultGroup),
                                # 故障类别
                                norm_fast(record.faultClassification),
                                # 服务项目或故障现象
                                norm_fast(record.faultPhenomenon),
                                # 维修方式
                                norm_fast(u2.maintenanceMode if u2 else ''),
                                # 旧件名称
                                norm_fast(u2.oldPartName if u2 else ''),
                                # 新件名称
                                norm_fast(u2.newPartName if u2 else ''),
                                # 来电内容
                                norm_fast(record.callContent),
                                # 现场诊断故障现象
                                norm_fast(record.onsiteFaultPhenomenon),
                                # 处理方案简述或备注
                                norm_fast(record.remarks)
                            ]

                            temp_data.append(row_data)

                        build_time = time.time() - start_time
                        print(f"⚡ 数据构建完成: {build_time:.3f}秒, {len(temp_data)}行")

                        # 8. 使用优化的方式创建DataFrame
                        start_time = time.time()
                        df_result = pd.DataFrame(temp_data, columns=expected_columns)
                        df_time = time.time() - start_time
                        print(f"📄 DataFrame创建: {df_time:.3f}秒")

                        # 9. 生成结果文件名
                        import os
                        if filename.lower().endswith('.xlsx'):
                            base_filename = filename[:-5]
                            excel_filename = f"quality_result_{filename}"
                            csv_filename = f"quality_result_{base_filename}.csv"
                        else:
                            excel_filename = f"quality_result_{filename}.xlsx"
                            csv_filename = f"quality_result_{filename}.csv"

                        # 10. 保存文件
                        results_folder = self.app.config.get('RESULTS_FOLDER', 'results')
                        os.makedirs(results_folder, exist_ok=True)

                        # 保存Excel文件（使用更快的引擎）
                        excel_start = time.time()
                        excel_filepath = os.path.join(results_folder, excel_filename)
                        df_result.to_excel(
                            excel_filepath,
                            index=False,
                            engine='openpyxl'  # 明确指定引擎
                        )
                        excel_time = time.time() - excel_start
                        print(f"💾 Excel保存: {excel_time:.3f}秒")
                        print(f"✅ Excel结果文件: {excel_filename}")

                        # 保存CSV文件
                        csv_start = time.time()
                        csv_filepath = os.path.join(results_folder, csv_filename)
                        df_result.to_csv(csv_filepath, index=False, encoding='utf-8')
                        csv_time = time.time() - csv_start
                        print(f"💾 CSV保存: {csv_time:.3f}秒")
                        print(f"✅ CSV结果文件: {csv_filename}")

                        # 11. 保存结果信息
                        with self.lock:
                            self.task_results[filename] = {
                                'excel_filename': excel_filename,
                                'csv_filename': csv_filename,
                                'excel_filepath': excel_filepath,
                                'csv_filepath': csv_filepath,
                                'rows_processed': len(df_result),
                                'completed_count': updated_count,
                                'total_count': processed_count
                            }

                        print(
                            f"🎯 处理完成: 总计{len(df_result)}行, 耗时{build_time + df_time + excel_time + csv_time:.3f}秒")

            except Exception as e:
                print(f"⚠️  生成Excel结果文件失败: {str(e)}")
                import traceback
                traceback.print_exc()

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
