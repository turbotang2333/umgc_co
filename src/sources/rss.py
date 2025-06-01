import feedparser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Optional
from .base import NewsSource
import time
import hashlib
from utils.date_service import DateRangeService
from bs4 import BeautifulSoup
import re

class RSSSource(NewsSource):
    """RSS新闻来源"""
    
    def __init__(self, opml_file: str):
        """初始化RSS来源
        
        Args:
            opml_file: str OPML文件路径
        """
        super().__init__("RSS聚合", "rss")
        self.opml_file = opml_file
    
    def _extract_subtitle(self, entry) -> str:
        """提取RSS条目的副标题（description字段）
        
        Args:
            entry: RSS条目
        
        Returns:
            str: 副标题内容
        """
        subtitle = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
        
        # 清理副标题中的HTML标签
        if subtitle:
            # 移除HTML标签
            subtitle = re.sub(r'<[^>]+>', '', subtitle)
            # 清理多余空白
            subtitle = re.sub(r'\s+', ' ', subtitle).strip()
            # 限制副标题长度，避免过长
            if len(subtitle) > 200:
                subtitle = subtitle[:200] + "..."
        
        return subtitle
    
    def _extract_content(self, entry) -> str:
        """提取RSS条目的完整内容
        
        Args:
            entry: RSS条目
        
        Returns:
            str: 清理后的文本内容
        """
        content = ""
        
        # 优先级1: content:encoded (完整内容)
        if hasattr(entry, 'content') and entry.content:
            for content_item in entry.content:
                if content_item.type == 'text/html' or 'html' in content_item.type:
                    content = content_item.value
                    break
        
        # 优先级2: content (标准content字段)
        if not content and hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value if entry.content else ""
        
        # 优先级3: summary/description (摘要)
        if not content:
            content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
        
        # 清理HTML并提取纯文本
        if content:
            return self._clean_html_content(content)
        
        return ""
    
    def _clean_html_content(self, html_content: str) -> str:
        """清理HTML内容，提取纯文本
        
        Args:
            html_content: str HTML内容
        
        Returns:
            str: 清理后的纯文本
        """
        try:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除script和style标签
            for tag in soup(['script', 'style']):
                tag.decompose()
            
            # 获取纯文本
            text = soup.get_text()
            
            # 清理文本
            # 移除多余的空白字符
            text = re.sub(r'\s+', ' ', text)
            
            # 移除首尾空白
            text = text.strip()
            
            # 移除常见的无用内容
            text = re.sub(r'阅读原文.*', '', text)
            text = re.sub(r'跳转微信打开.*', '', text)
            text = re.sub(r'长按二维码.*', '', text)
            text = re.sub(r'点击收看.*', '', text)
            
            return text
            
        except Exception as e:
            print(f"HTML清理失败，使用原始内容: {str(e)}")
            # 如果解析失败，至少移除基本的HTML标签
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
    
    def get_news(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """获取RSS新闻内容
        
        Args:
            start_date: Optional[datetime] 开始时间
            end_date: Optional[datetime] 结束时间
        
        Returns:
            List[Dict] 标准化的新闻数据列表
        """
        all_news = []
        
        # 解析OPML文件
        tree = ET.parse(self.opml_file)
        root = tree.getroot()
        
        print(f"\n开始获取RSS内容...")
        if start_date and end_date:
            print(f"时间范围: {start_date.strftime('%Y-%m-%d %H:%M')} 到 {end_date.strftime('%Y-%m-%d %H:%M')}")
        print()
        
        # 查找所有RSS源
        outlines = root.findall('.//outline[@type="rss"]')
        
        for outline in outlines:
            source_name = outline.get('text', '未知来源')  # 具体的RSS源名称
            rss_url = outline.get('xmlUrl')
            
            if not rss_url:
                continue
                
            print(f"处理RSS源: {source_name}")
            
            try:
                # 获取RSS内容
                feed = feedparser.parse(rss_url)
                
                if feed.bozo:
                    print(f"RSS源解析警告: {source_name}")
                
                matched_count = 0
                total_count = len(feed.entries)
                
                # 获取RSS源的新闻
                for entry in feed.entries:
                    try:
                        # 解析发布时间
                        published_time = self._parse_published_time(entry)
                        
                        if published_time is None:
                            continue
                        
                        # 使用标准的时间格式显示
                        published_str = published_time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 检查时间范围
                        if start_date and end_date:
                            if not (start_date <= published_time <= end_date):
                                print(f"跳过文章（时间过早）: {entry.title} ({published_str})")
                                continue
                        
                        print(f"✓ 匹配文章: {entry.title} ({published_str})")
                        matched_count += 1
                        
                        # 生成唯一ID
                        unique_id = hashlib.md5(
                            f"{source_name}_{entry.link}_{entry.title}".encode('utf-8')
                        ).hexdigest()
                        
                        # 创建标准化的新闻数据
                        news_item = {
                            'id': unique_id,
                            'source_name': source_name,  # 具体的RSS源名称
                            'source_type': self.source_type,
                            'manager_name': self.name,   # RSS聚合管理器名称
                            'title': entry.title,
                            'content': self._extract_content(entry),
                            'published': published_time,
                            'link': entry.link,
                            'raw_data': {
                                'rss_source': source_name,
                                'rss_url': rss_url,
                                'entry_id': getattr(entry, 'id', ''),
                            },
                            'subtitle': self._extract_subtitle(entry)
                        }
                        
                        all_news.append(news_item)
                        
                    except Exception as e:
                        print(f"处理文章时出错: {str(e)}")
                        continue
                
                print(f"RSS源 {source_name}: 处理 {total_count} 篇文章，匹配 {matched_count} 篇")
                
                # 添加延时避免频繁请求
                time.sleep(1)
                
            except Exception as e:
                print(f"获取RSS源失败: {source_name}")
                continue
        
        print(f"\n总计获取到 {len(all_news)} 条符合时间条件的新闻")
        return all_news
    
    def _parse_published_time(self, entry) -> Optional[datetime]:
        """解析RSS条目的发布时间
        
        Args:
            entry: RSS条目
        
        Returns:
            Optional[datetime] 解析后的时间，失败返回None
        """
        if not hasattr(entry, 'published'):
            return None
            
        try:
            # 尝试不同的时间格式
            published_str = entry.published
            
            # 常见的RSS时间格式
            time_formats = [
                '%a, %d %b %Y %H:%M:%S %z',  # RFC 2822
                '%a, %d %b %Y %H:%M:%S %Z',  # RFC 2822 with timezone name
                '%Y-%m-%dT%H:%M:%S%z',       # ISO 8601
                '%Y-%m-%dT%H:%M:%SZ',        # ISO 8601 UTC
                '%Y-%m-%d %H:%M:%S',         # Simple format
            ]
            
            for fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(published_str, fmt)
                    # 如果没有时区信息，假设为UTC
                    if parsed_time.tzinfo is None:
                        from datetime import timezone
                        parsed_time = parsed_time.replace(tzinfo=timezone.utc)
                    return parsed_time
                except ValueError:
                    continue
            
            # 如果所有格式都失败，尝试使用feedparser的解析
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                from datetime import timezone
                time_tuple = entry.published_parsed
                # 将time_struct转换为datetime
                dt = datetime(*time_tuple[:6])
                return dt.replace(tzinfo=timezone.utc)
            
        except Exception as e:
            print(f"解析时间失败: {published_str} - {str(e)}")
            
        return None 