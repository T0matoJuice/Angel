#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重试工具模块 - 提供数据库操作的自动重试机制
"""

import time
import functools
from typing import Callable, Any, Tuple, Type
from sqlalchemy.exc import OperationalError, IntegrityError, DatabaseError


def retry_on_db_error(
    max_retries: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (OperationalError, DatabaseError)
):
    """数据库操作重试装饰器
    
    当数据库操作失败时，自动重试指定次数
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的倍增因子
        exceptions: 需要重试的异常类型
        
    Example:
        @retry_on_db_error(max_retries=3, delay=0.5)
        def save_to_db():
            db.session.commit()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        print(f"⚠️  数据库操作失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                        print(f"   等待 {current_delay:.2f} 秒后重试...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        print(f"❌ 数据库操作失败，已达最大重试次数 ({max_retries + 1})")
                        raise last_exception
                except IntegrityError as e:
                    # 完整性约束错误（如主键冲突）不重试
                    print(f"❌ 数据完整性错误，不重试: {str(e)}")
                    raise
            
            # 理论上不会到这里，但为了类型检查
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_with_exponential_backoff(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """通用的指数退避重试装饰器
    
    适用于任何可能失败的操作（如网络请求、外部API调用等）
    
    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        print(f"⚠️  操作失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                        print(f"   等待 {delay:.2f} 秒后重试...")
                        time.sleep(delay)
                        delay = min(delay * 2, max_delay)  # 指数退避，但不超过最大延迟
                    else:
                        print(f"❌ 操作失败，已达最大重试次数 ({max_retries + 1})")
                        raise last_exception
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator
