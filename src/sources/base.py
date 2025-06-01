from abc import ABC, abstractmethod

class NewsSource(ABC):
    """新闻源基类"""
    
    def __init__(self, name):
        self.name = name
    
    @abstractmethod
    def get_news(self):
        """获取新闻文章列表"""
        pass