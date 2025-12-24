#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器 - 自动同步人工判断数据

功能说明：
1. 每天凌晨自动同步前一天的人工判断数据
2. 支持手动触发同步
3. 记录同步日志和状态
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from flask import current_app
import traceback

from modules.auth import db
from modules.excel.sync_manual_judgment import ManualJudgmentSyncer

# 配置日志
logger = logging.getLogger(__name__)


class ScheduledSyncManager:
    """定时同步管理器"""
    
    def __init__(self, app=None):
        """初始化定时同步管理器
        
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
        sync_enabled = app.config.get('AUTO_SYNC_ENABLED', True)
        sync_hour = app.config.get('AUTO_SYNC_HOUR', 1)  # 默认凌晨1点
        sync_minute = app.config.get('AUTO_SYNC_MINUTE', 0)
        
        if sync_enabled:
            self.start_scheduler(sync_hour, sync_minute)
    
    def start_scheduler(self, hour=1, minute=0):
        """启动定时任务调度器
        
        Args:
            hour (int): 执行小时（0-23），默认1点
            minute (int): 执行分钟（0-59），默认0分
        """
        if self.scheduler is not None:
            logger.warning("调度器已在运行中")
            return
        
        # 创建后台调度器
        self.scheduler = BackgroundScheduler(
            timezone='Asia/Shanghai',
            daemon=True
        )
        
        # 添加定时任务：每天指定时间执行
        self.scheduler.add_job(
            func=self.sync_yesterday_data,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_sync_manual_judgment',
            name='每日同步人工判断数据',
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
        
        logger.info(f"✅ 定时同步任务已启动，每天 {hour:02d}:{minute:02d} 自动同步前一天数据")
        print(f"✅ 定时同步任务已启动，每天 {hour:02d}:{minute:02d} 自动同步前一天数据")
    
    def stop_scheduler(self):
        """停止定时任务调度器"""
        if self.scheduler is not None:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
            logger.info("定时同步任务已停止")
            print("定时同步任务已停止")
    
    def sync_yesterday_data(self):
        """同步昨天的数据（定时任务调用）"""
        # 计算昨天的日期
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
        
        logger.info(f"开始自动同步 {date_str} 的人工判断数据")
        print(f"\n{'='*60}")
        print(f"🕐 定时任务触发: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 同步日期: {date_str}")
        print(f"{'='*60}")
        
        # 执行同步
        self.sync_data(date_str, date_str)
    
    def sync_data(self, start_date, end_date):
        """同步指定日期范围的数据
        
        Args:
            start_date (str): 开始日期，格式：YYYY-MM-DD
            end_date (str): 结束日期，格式：YYYY-MM-DD
            
        Returns:
            dict: 同步结果统计
        """
        try:
            # 记录开始时间
            self.last_sync_time = datetime.now()
            
            # 在应用上下文中执行同步
            with self.app.app_context():
                syncer = ManualJudgmentSyncer()
                
                # 获取Token
                syncer.get_bearer_token()
                
                # 获取数据
                data_list = syncer.fetch_manual_judgment_data(start_date, end_date)
                
                if not data_list:
                    logger.warning(f"未获取到任何数据 ({start_date} ~ {end_date})")
                    self.last_sync_status = "warning"
                    self.last_sync_stats = {
                        "total": 0,
                        "updated": 0,
                        "not_found": 0,
                        "errors": 0
                    }
                    return self.last_sync_stats
                
                # 更新数据库
                stats = syncer.update_database(data_list)
                
                # 记录成功状态
                self.last_sync_status = "success"
                self.last_sync_stats = stats
                
                # 记录日志
                logger.info(
                    f"同步完成: 总数={stats['total']}, "
                    f"成功={stats['updated']}, "
                    f"未找到={stats['not_found']}, "
                    f"失败={stats['errors']}"
                )
                
                print(f"\n✅ 同步完成:")
                print(f"   总记录数: {stats['total']}")
                print(f"   成功更新: {stats['updated']}")
                print(f"   未找到工单: {stats['not_found']}")
                print(f"   更新失败: {stats['errors']}")
                print(f"{'='*60}\n")
                
                return stats
                
        except Exception as e:
            # 记录失败状态
            self.last_sync_status = "error"
            self.last_sync_stats = None
            
            error_msg = f"同步失败: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            print(f"\n✗ {error_msg}\n")
            
            raise
    
    def _job_listener(self, event):
        """任务执行监听器
        
        Args:
            event: 任务事件
        """
        if event.exception:
            logger.error(f"定时任务执行失败: {event.exception}")
        else:
            logger.info(f"定时任务执行成功: {event.job_id}")
    
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
        
        job = self.scheduler.get_job('daily_sync_manual_judgment')
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return None
    
    def trigger_manual_sync(self, start_date=None, end_date=None):
        """手动触发同步
        
        Args:
            start_date (str): 开始日期，默认为昨天
            end_date (str): 结束日期，默认为昨天
            
        Returns:
            dict: 同步结果统计
        """
        if start_date is None or end_date is None:
            yesterday = datetime.now() - timedelta(days=1)
            date_str = yesterday.strftime("%Y-%m-%d")
            start_date = start_date or date_str
            end_date = end_date or date_str
        
        logger.info(f"手动触发同步: {start_date} ~ {end_date}")
        print(f"\n🔧 手动触发同步: {start_date} ~ {end_date}")
        
        return self.sync_data(start_date, end_date)


# 全局调度器实例
_scheduler_manager = None


def get_scheduler_manager(app=None):
    """获取调度器管理器实例（单例模式）
    
    Args:
        app: Flask应用实例
        
    Returns:
        ScheduledSyncManager: 调度器管理器实例
    """
    global _scheduler_manager
    
    if _scheduler_manager is None:
        _scheduler_manager = ScheduledSyncManager(app)
    elif app is not None:
        _scheduler_manager.init_app(app)
    
    return _scheduler_manager


def init_scheduler(app):
    """初始化定时任务调度器（在app.py中调用）
    
    Args:
        app: Flask应用实例
    """
    scheduler_manager = get_scheduler_manager(app)
    
    # 注册应用关闭时的清理函数
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        if exception:
            logger.error(f"应用关闭异常: {exception}")
    
    return scheduler_manager
