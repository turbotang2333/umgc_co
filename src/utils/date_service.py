from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
import argparse

class DateRangeService:
    """日期范围处理服务"""
    
    @staticmethod
    def get_yesterday_range() -> Tuple[datetime, datetime]:
        """获取昨天的日期范围
        
        Returns:
            Tuple[datetime, datetime]: (昨天00:00:00, 昨天23:59:59)
        """
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_date, end_date
    
    @staticmethod
    def get_single_day_range(date_str: str) -> Tuple[datetime, datetime]:
        """获取指定日期的完整范围
        
        Args:
            date_str: str 日期字符串，格式为YYYY-MM-DD
        
        Returns:
            Tuple[datetime, datetime]: (指定日00:00:00, 指定日23:59:59)
        """
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        # 将naive datetime转换为UTC时区
        target_date = target_date.replace(tzinfo=timezone.utc)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_date, end_date
    
    @staticmethod
    def get_date_range(start_str: str, end_str: str) -> Tuple[datetime, datetime]:
        """获取日期范围
        
        Args:
            start_str: str 开始日期字符串，格式为YYYY-MM-DD
            end_str: str 结束日期字符串，格式为YYYY-MM-DD
        
        Returns:
            Tuple[datetime, datetime]: (开始日00:00:00, 结束日23:59:59)
        """
        start_date = datetime.strptime(start_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_str, '%Y-%m-%d')
        
        # 将naive datetime转换为UTC时区
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
        
        return start_date, end_date
    
    @staticmethod
    def get_past_days_range(days: int) -> Tuple[datetime, datetime]:
        """获取过去N天的日期范围
        
        Args:
            days: int 天数
        
        Returns:
            Tuple[datetime, datetime]: (N天前00:00:00, 昨天23:59:59)
        """
        end_date = datetime.now(timezone.utc) - timedelta(days=1)
        start_date = end_date - timedelta(days=days-1)
        
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return start_date, end_date
    
    @staticmethod
    def parse_args_to_date_range(args: argparse.Namespace) -> Tuple[datetime, datetime]:
        """根据命令行参数解析日期范围
        
        Args:
            args: argparse.Namespace 命令行参数
        
        Returns:
            Tuple[datetime, datetime]: 解析后的日期范围
        """
        if hasattr(args, 'date_range') and args.date_range:
            start_str, end_str = args.date_range
            return DateRangeService.get_date_range(start_str, end_str)
        elif hasattr(args, 'date') and args.date:
            return DateRangeService.get_single_day_range(args.date)
        elif hasattr(args, 'days') and args.days:
            return DateRangeService.get_past_days_range(args.days)
        else:
            # 默认返回昨天的日期范围
            return DateRangeService.get_yesterday_range()
    
    @staticmethod
    def is_in_range(target_datetime: datetime, start_date: datetime, end_date: datetime) -> bool:
        """检查指定时间是否在日期范围内
        
        Args:
            target_datetime: datetime 目标时间
            start_date: datetime 开始时间
            end_date: datetime 结束时间
        
        Returns:
            bool: 是否在范围内
        """
        # 确保所有datetime都有时区信息
        if target_datetime.tzinfo is None:
            target_datetime = target_datetime.replace(tzinfo=timezone.utc)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
            
        return start_date <= target_datetime <= end_date 
    
    @staticmethod
    def format_datetime_short(dt: datetime) -> str:
        """格式化为简短时间显示 (MM-DD HH:MM)
        
        Args:
            dt: datetime 要格式化的时间
        
        Returns:
            str: 格式化后的时间字符串
        """
        return dt.strftime('%m-%d %H:%M')
    
    @staticmethod
    def format_date_only(dt: datetime) -> str:
        """只显示日期 (YYYY-MM-DD)
        
        Args:
            dt: datetime 要格式化的时间
        
        Returns:
            str: 格式化后的日期字符串
        """
        return dt.strftime('%Y-%m-%d') 