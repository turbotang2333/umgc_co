import feedparser
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict
from .base import NewsSource
import time

class RSSSource(NewsSource):
    """RSS新闻来源"""
    
    def __init__(self, opml_file: str):
        """初始化RSS来源
        
        Args:
            opml_file: str OPML文件路径
        """
        self.opml_file = opml_file
    
    def get_news(self) -> List[Dict]:
        """获取RSS新闻内容"""
        all_news = []
        
        # 解析OPML文件
        tree = ET.parse(self.opml_file)
        root = tree.getroot()
        
        print("\n开始获取RSS内容...")
        
        # 遍历所有RSS源
        for outline in root.findall('.//outline'):
            source_name = outline.get('text', '')
            xml_url = outline.get('xmlUrl', '')
            
            if not xml_url:
                continue
                
            print(f"\n处理RSS源: {source_name}")
            
            # 获取RSS内容
            feed = feedparser.parse(xml_url)
            
            if hasattr(feed, 'status') and feed.status == 200:
                # 获取最新的内容
                for entry in feed.entries[:2]:
                    try:
                        # 构建内容
                        content = entry.title
                        if hasattr(entry, 'summary'):
                            content += f"\n{entry.summary}"
                        
                        # 添加到新闻列表
                        news = {
                            'source': source_name,
                            'title': entry.title,
                            'content': content,
                            'link': entry.link,
                            'published': datetime.fromtimestamp(
                                datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').timestamp()
                            )
                        }
                        all_news.append(news)
                        print(f"处理文章: {entry.title}")
                        
                        # 添加延时避免API调用过于频繁
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"处理RSS文章时出错: {str(e)}")
                        continue
            else:
                print(f"获取RSS源失败: {source_name}")
        
        # 按时间排序
        return sorted(all_news, key=lambda x: x['published'], reverse=True) 