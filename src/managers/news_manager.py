from typing import List, Dict, Optional
from datetime import datetime
from sources.base import NewsSource

class NewsManager:
    """新闻管理器，统一管理所有新闻来源"""
    
    def __init__(self):
        """初始化新闻管理器"""
        self.sources: List[NewsSource] = []
    
    def register_source(self, source: NewsSource) -> None:
        """注册新闻来源
        
        Args:
            source: NewsSource 新闻来源实例
        """
        self.sources.append(source)
        print(f"已注册新闻来源: {source.name} ({source.source_type})")
    
    def get_all_news(self, 
                     start_date: Optional[datetime] = None, 
                     end_date: Optional[datetime] = None,
                     source_types: Optional[List[str]] = None) -> List[Dict]:
        """获取所有来源的新闻
        
        Args:
            start_date: Optional[datetime] 开始时间
            end_date: Optional[datetime] 结束时间
            source_types: Optional[List[str]] 指定的来源类型列表，为None则包含所有类型
        
        Returns:
            List[Dict] 合并后的新闻列表
        """
        all_news = []
        
        for source in self.sources:
            # 如果指定了来源类型，则过滤
            if source_types and source.source_type not in source_types:
                continue
                
            try:
                print(f"\n获取来源 {source.name} 的新闻...")
                news_list = source.get_news(start_date, end_date)
                all_news.extend(news_list)
                print(f"从 {source.name} 获取到 {len(news_list)} 条新闻")
            except Exception as e:
                print(f"获取来源 {source.name} 新闻时出错: {str(e)}")
                continue
        
        # 去重（基于ID）
        unique_news = self._deduplicate_news(all_news)
        
        # 按发布时间排序
        sorted_news = sorted(unique_news, key=lambda x: x['published'], reverse=True)
        
        print(f"\n总计获取到 {len(all_news)} 条新闻，去重后 {len(unique_news)} 条")
        return sorted_news
    
    def get_news_by_source_type(self, 
                                source_type: str,
                                start_date: Optional[datetime] = None, 
                                end_date: Optional[datetime] = None) -> List[Dict]:
        """获取指定类型来源的新闻
        
        Args:
            source_type: str 来源类型
            start_date: Optional[datetime] 开始时间
            end_date: Optional[datetime] 结束时间
        
        Returns:
            List[Dict] 指定类型的新闻列表
        """
        return self.get_all_news(start_date, end_date, [source_type])
    
    def get_news_summary(self) -> Dict:
        """获取新闻来源摘要信息
        
        Returns:
            Dict 包含各来源统计信息的字典
        """
        summary = {
            'total_sources': len(self.sources),
            'source_types': {},
            'sources': []
        }
        
        for source in self.sources:
            source_info = {
                'name': source.name,
                'type': source.source_type
            }
            summary['sources'].append(source_info)
            
            # 统计来源类型
            if source.source_type in summary['source_types']:
                summary['source_types'][source.source_type] += 1
            else:
                summary['source_types'][source.source_type] = 1
        
        return summary
    
    def _deduplicate_news(self, news_list: List[Dict]) -> List[Dict]:
        """去重新闻列表
        
        Args:
            news_list: List[Dict] 原始新闻列表
        
        Returns:
            List[Dict] 去重后的新闻列表
        """
        seen_ids = set()
        unique_news = []
        
        for news in news_list:
            news_id = news.get('id')
            if news_id and news_id not in seen_ids:
                seen_ids.add(news_id)
                unique_news.append(news)
            elif not news_id:
                # 如果没有ID，使用标题+链接作为唯一标识
                unique_key = f"{news.get('title', '')}_{news.get('link', '')}"
                if unique_key not in seen_ids:
                    seen_ids.add(unique_key)
                    unique_news.append(news)
        
        return unique_news 