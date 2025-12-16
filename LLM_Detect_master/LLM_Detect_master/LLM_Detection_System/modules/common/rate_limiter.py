#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
限流工具模块 - 防止过载和资源耗尽
"""

import time
import threading
from collections import deque
from typing import Dict, Optional


class RateLimiter:
    """简单的令牌桶限流器
    
    用于限制API请求频率，防止系统过载
    """
    
    def __init__(self, max_requests: int, time_window: int):
        """初始化限流器
        
        Args:
            max_requests: 时间窗口内允许的最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier: str = "default") -> bool:
        """检查是否允许请求
        
        Args:
            identifier: 请求标识符（如IP地址、用户ID等）
            
        Returns:
            bool: 是否允许请求
        """
        with self.lock:
            current_time = time.time()
            
            # 移除时间窗口外的请求记录
            while self.requests and self.requests[0] < current_time - self.time_window:
                self.requests.popleft()
            
            # 检查是否超过限制
            if len(self.requests) >= self.max_requests:
                return False
            
            # 记录本次请求
            self.requests.append(current_time)
            return True
    
    def get_remaining(self) -> int:
        """获取剩余可用请求数"""
        with self.lock:
            current_time = time.time()
            
            # 移除时间窗口外的请求记录
            while self.requests and self.requests[0] < current_time - self.time_window:
                self.requests.popleft()
            
            return max(0, self.max_requests - len(self.requests))
    
    def wait_if_needed(self, identifier: str = "default", max_wait: float = 60.0) -> bool:
        """如果超过限制，等待直到可以继续
        
        Args:
            identifier: 请求标识符
            max_wait: 最大等待时间（秒）
            
        Returns:
            bool: 是否成功（True表示已等待并可继续，False表示等待超时）
        """
        start_time = time.time()
        
        while not self.is_allowed(identifier):
            if time.time() - start_time > max_wait:
                return False
            
            # 等待一小段时间后重试
            time.sleep(0.1)
        
        return True


class QueueProtector:
    """队列保护器
    
    防止队列过载，当队列长度超过阈值时拒绝新任务
    """
    
    def __init__(self, max_queue_size: int = 100, max_processing_time: int = 3600):
        """初始化队列保护器
        
        Args:
            max_queue_size: 最大队列长度
            max_processing_time: 单个任务最大处理时间（秒）
        """
        self.max_queue_size = max_queue_size
        self.max_processing_time = max_processing_time
        self.task_start_times: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def can_add_task(self, current_queue_size: int) -> tuple[bool, Optional[str]]:
        """检查是否可以添加新任务
        
        Args:
            current_queue_size: 当前队列长度
            
        Returns:
            tuple: (是否可以添加, 拒绝原因)
        """
        with self.lock:
            if current_queue_size >= self.max_queue_size:
                return False, f"队列已满（{current_queue_size}/{self.max_queue_size}），请稍后重试"
            
            return True, None
    
    def mark_task_start(self, task_id: str):
        """标记任务开始"""
        with self.lock:
            self.task_start_times[task_id] = time.time()
    
    def mark_task_end(self, task_id: str):
        """标记任务结束"""
        with self.lock:
            self.task_start_times.pop(task_id, None)
    
    def check_timeout_tasks(self) -> list[str]:
        """检查超时的任务
        
        Returns:
            list: 超时任务的ID列表
        """
        with self.lock:
            current_time = time.time()
            timeout_tasks = []
            
            for task_id, start_time in list(self.task_start_times.items()):
                if current_time - start_time > self.max_processing_time:
                    timeout_tasks.append(task_id)
            
            return timeout_tasks


# 全局限流器实例（每分钟最多100个请求）
global_rate_limiter = RateLimiter(max_requests=100, time_window=60)

# 全局队列保护器实例
global_queue_protector = QueueProtector(max_queue_size=100, max_processing_time=3600)
