#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零件数据定时同步调度器

功能说明：
1. 每天凌晨3:00自动从PLM系统查询零件数据并导入数据库
2. 支持手动触发同步
3. 记录同步日志和状态
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from flask import current_app
import traceback

from modules.drawing.query_part import QueryPartManager

# 配置日志
logger = logging.getLogger(__name__)


class PartDataScheduler:
    """零件数据定时同步调度器"""
    
    def __init__(self, app=None):
        """初始化调度器
        
        Args:
            app: Flask应用实例
        """
        self.scheduler = None
        self.app = app
        self.last_sync_time = None
        self.last_sync_status = None
        self.last_sync_stats = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用
        
        Args:
            app: Flask应用实例
        """
        self.app = app
        
        # 从配置中读取定时任务设置
        sync_enabled = app.config.get('PART_SYNC_ENABLED', True)
        sync_hour = app.config.get('PART_SYNC_HOUR', 3)  # 默认凌晨3点
        sync_minute = app.config.get('PART_SYNC_MINUTE', 0)
        
        if sync_enabled:
            self.start_scheduler(sync_hour, sync_minute)
    
    def start_scheduler(self, hour=3, minute=0):
        """启动定时任务调度器
        
        Args:
            hour (int): 执行小时（0-23），默认3点
            minute (int): 执行分钟（0-59），默认0分
        """
        if self.scheduler is not None:
            logger.warning("零件数据同步调度器已在运行中")
            return
        
        # 创建后台调度器
        self.scheduler = BackgroundScheduler(
            timezone='Asia/Shanghai',
            daemon=True
        )
        
        # 添加定时任务：每天指定时间执行
        self.scheduler.add_job(
            func=self.sync_part_data,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_sync_part_data',
            name='每日同步零件数据',
            replace_existing=True,
            max_instances=1  # 确保同一时间只运行一个实例
        )
        
        # 添加事件监听器
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        # 启动调度器
        self.scheduler.start()
        
        logger.info(f"✅ 零件数据定时同步任务已启动，每天 {hour:02d}:{minute:02d} 自动同步")
        print(f"✅ 零件数据定时同步任务已启动，每天 {hour:02d}:{minute:02d} 自动同步")
    
    def stop_scheduler(self):
        """停止定时任务调度器"""
        if self.scheduler is not None:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
            logger.info("零件数据定时同步任务已停止")
            print("零件数据定时同步任务已停止")
    
    def sync_part_data(self):
        """同步零件数据（定时任务调用）"""
        logger.info("开始自动同步零件数据")
        print(f"\n{'='*80}")
        print(f"🕐 定时任务触发: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 任务内容: 从PLM系统查询零件数据并导入数据库")
        print(f"{'='*80}")
        
        # 执行同步
        self.execute_sync()
    
    def execute_sync(self):
        """执行同步任务
        
        Returns:
            dict: 同步结果统计
        """
        try:
            # 记录开始时间
            self.last_sync_time = datetime.now()
            
            # 在应用上下文中执行同步
            with self.app.app_context():
                manager = QueryPartManager()
                
                # 第一步：查询数据
                success, json_data, output_file = manager.query_parts_from_plm()
                
                if not success:
                    logger.error("❌ 零件数据查询失败！")
                    self.last_sync_status = "error"
                    self.last_sync_stats = None
                    return None
                
                logger.info("✅ 零件数据查询成功！")
                
                # 第二步：导入到数据库
                stats = manager.import_parts_to_database(json_data)
                
                if stats:
                    # 记录成功状态
                    self.last_sync_status = "success" if stats['errors'] == 0 else "warning"
                    self.last_sync_stats = stats
                    
                    # 记录日志
                    logger.info(
                        f"同步完成: 总数={stats['total']}, "
                        f"新插入={stats['inserted']}, "
                        f"更新={stats['updated']}, "
                        f"跳过={stats['skipped']}, "
                        f"失败={stats['errors']}"
                    )
                    
                    print(f"\n✅ 同步完成:")
                    print(f"   总记录数: {stats['total']}")
                    print(f"   新插入: {stats['inserted']}")
                    print(f"   更新记录: {stats['updated']}")
                    print(f"   跳过记录: {stats['skipped']}")
                    print(f"   更新失败: {stats['errors']}")
                    print(f"{'='*80}\n")
                    
                    return stats
                else:
                    logger.error("❌ 数据导入失败！")
                    self.last_sync_status = "error"
                    self.last_sync_stats = None
                    return None
                
        except Exception as e:
            # 记录失败状态
            self.last_sync_status = "error"
            self.last_sync_stats = None
            
            error_msg = f"同步失败: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            print(f"\n❌ {error_msg}\n")
            
            raise
    
    def _job_listener(self, event):
        """任务执行监听器
        
        Args:
            event: 任务事件
        """
        if event.exception:
            logger.error(f"零件数据同步任务执行失败: {event.exception}")
        else:
            logger.info(f"零件数据同步任务执行成功: {event.job_id}")
    
    def get_sync_status(self):
        """获取同步状态
        
        Returns:
            dict: 同步状态信息
        """
        return {
            "last_sync_time": self.last_sync_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_sync_time else None,
            "last_sync_status": self.last_sync_status,
            "last_sync_stats": self.last_sync_stats,
            "scheduler_running": self.scheduler is not None and self.scheduler.running,
            "next_run_time": self._get_next_run_time()
        }
    
    def _get_next_run_time(self):
        """获取下次执行时间
        
        Returns:
            str: 下次执行时间字符串
        """
        if self.scheduler is None or not self.scheduler.running:
            return None
        
        job = self.scheduler.get_job('daily_sync_part_data')
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return None
    
    def trigger_manual_sync(self):
        """手动触发同步
        
        Returns:
            dict: 同步结果统计
        """
        logger.info("手动触发零件数据同步")
        print(f"\n🔧 手动触发零件数据同步")
        
        return self.execute_sync()


# 全局调度器实例
_part_scheduler = None


def get_part_scheduler(app=None):
    """获取零件数据调度器实例（单例模式）
    
    Args:
        app: Flask应用实例
        
    Returns:
        PartDataScheduler: 调度器实例
    """
    global _part_scheduler
    
    if _part_scheduler is None:
        _part_scheduler = PartDataScheduler(app)
    elif app is not None:
        _part_scheduler.init_app(app)
    
    return _part_scheduler


def init_part_scheduler(app):
    """初始化零件数据定时任务调度器（在app.py中调用）
    
    Args:
        app: Flask应用实例
    """
    part_scheduler = get_part_scheduler(app)
    
    # 注册应用关闭时的清理函数
    @app.teardown_appcontext
    def shutdown_part_scheduler(exception=None):
        if exception:
            logger.error(f"应用关闭异常: {exception}")
    
    return part_scheduler
