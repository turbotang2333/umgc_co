from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional

class NewsSource(ABC):
    """新闻源基类"""
    
    def __init__(self, name: str, source_type: str):
        """初始化新闻源
        
        Args:
            name: str 新闻源名称
            source_type: str 新闻源类型（rss, api, web等）
        """
        self.name = name
        self.source_type = source_type
    
    @abstractmethod
    def get_news(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """获取新闻文章列表
        
        Args:
            start_date: Optional[datetime] 开始时间，为None则不限制
            end_date: Optional[datetime] 结束时间，为None则不限制
        
        Returns:
            List[Dict] 标准化的新闻数据列表，每个字典包含：
            - id: str 唯一标识符
            - source: str 来源名称
            - source_type: str 来源类型
            - title: str 标题
            - content: str 内容
            - published: datetime 发布时间
            - link: str 原文链接
            - raw_data: Dict 原始数据（可选，用于扩展）
        """
        pass
    
    def filter_by_date(self, news_list: List[Dict], start_date: Optional[datetime], end_date: Optional[datetime]) -> List[Dict]:
        """按日期过滤新闻列表
        
        Args:
            news_list: List[Dict] 新闻列表
            start_date: Optional[datetime] 开始时间
            end_date: Optional[datetime] 结束时间
        
        Returns:
            List[Dict] 过滤后的新闻列表
        """
        if not start_date and not end_date:
            return news_list
        
        filtered_news = []
        for news in news_list:
            published = news.get('published')
            if not published:
                continue
                
            # 确保published是datetime对象
            if isinstance(published, str):
                try:
                    published = datetime.fromisoformat(published.replace('Z', '+00:00'))
                except:
                    continue
            
            # 检查是否在时间范围内
            if start_date and published < start_date:
                continue
            if end_date and published > end_date:
                continue
                
            filtered_news.append(news)
        
        return filtered_news
    
    def create_standard_news_item(self, 
                                  id: str,
                                  title: str, 
                                  content: str, 
                                  published: datetime, 
                                  link: str,
                                  raw_data: Optional[Dict] = None) -> Dict:
        """创建标准化的新闻数据项
        
        Args:
            id: str 唯一标识符
            title: str 标题
            content: str 内容
            published: datetime 发布时间
            link: str 原文链接
            raw_data: Optional[Dict] 原始数据
        
        Returns:
            Dict 标准化的新闻数据项
        """
        return {
            'id': id,
            'source': self.name,
            'source_type': self.source_type,
            'title': title,
            'content': content,
            'published': published,
            'link': link,
            'raw_data': raw_data or {}
        }