from typing import List, Dict
from itertools import groupby
from datetime import datetime
import os

class HTMLTemplate:
    """HTML模板服务"""
    
    def __init__(self):
        """初始化HTML模板服务"""
        self.styles = {
            'container': 'font-family:Arial,sans-serif;max-width:800px;margin:20px auto;padding:0 20px',
            'card': 'background:#f8f8f8;border:1px solid #e8e8e8;border-radius:8px;padding:15px 20px;margin-bottom:30px',
            'text': 'display:flex;align-items:flex-start;margin:0;line-height:1.6;color:#000000',
            'source': 'color:#000000;display:block;margin-bottom:20px;font-size:16px;border-bottom:1px solid #e8e8e8;padding-bottom:10px',
            'link': 'color:#4a90e2;text-decoration:none;margin-left:8px',
            'article': 'margin:15px 0',
            'date': 'color:#666666;margin-left:8px',
            'bullet': 'color:#4a90e2;margin-right:8px;flex-shrink:0',
            'content': 'flex:1'
        }
        
        self.mobile_styles = """
        @media screen and (max-width: 480px) {
            div[style*="background:#f8f8f8"] {
                padding: 20px !important;
                margin-bottom: 25px !important;
            }
            .news-item {
                line-height: 1.8 !important;
                font-size: 15px !important;
                margin: 12px 0 !important;
            }
            b[style*="margin-bottom:20px"] {
                margin-bottom: 25px !important;
                font-size: 18px !important;
            }
            div[style*="margin:15px"] {
                margin: 20px 0 !important;
            }
            span[style*="margin-left:8px"] {
                margin-left: 10px !important;
            }
        }
        """
    
    def format_date(self, published_date: datetime) -> str:
        """格式化日期
        
        Args:
            published_date: datetime 发布日期
        
        Returns:
            str 格式化后的日期字符串
        """
        return f"({published_date.strftime('%-m-%-d')})"
    
    def generate_article_line(self, article: Dict) -> str:
        """生成单条文章的HTML
        
        Args:
            article: Dict 文章信息
        
        Returns:
            str 文章HTML
        """
        date_str = self.format_date(article['published'])
        return f"""
            <p class="news-item" style="{self.styles['text']}">
                <span style="{self.styles['bullet']}">•</span>
                <span style="{self.styles['content']}">{article['summary']}
                <span style="{self.styles['date']}">{date_str}</span>
                <a href="{article['link']}" style="{self.styles['link']}" target="_blank">[查看]</a></span>
            </p>"""
    
    def generate_source_card(self, source_name: str, articles: List[Dict]) -> str:
        """生成单个来源的卡片HTML
        
        Args:
            source_name: str 来源名称
            articles: List[Dict] 文章列表
        
        Returns:
            str 来源卡片HTML
        """
        articles_html = []
        articles_html.append(f"""
            <b style="{self.styles['source']}">{source_name}</b>""")
        
        articles_html.append(self.generate_article_line(articles[0]))
        
        for article in articles[1:]:
            articles_html.append(f"""
            <div style="{self.styles['article']}">
                {self.generate_article_line(article)}
            </div>""")
        
        return f"""
        <div style="{self.styles['card']}">{''.join(articles_html)}
        </div>
        """
    
    def generate_html(self, news_list: List[Dict], output_file: str = 'news_summary.html') -> None:
        """生成完整的HTML并保存到文件
        
        Args:
            news_list: List[Dict] 新闻列表
            output_file: str 输出文件路径
        """
        print("\n开始生成HTML...")
        
        if not news_list:
            print("没有找到任何更新内容")
            return
        
        # 确保使用绝对路径
        output_path = os.path.abspath(output_file)
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="zh-CN">',
            '<head>',
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<title>音乐新闻聚合</title>',
            '<style>',
            self.mobile_styles,
            '</style>',
            '</head>',
            '<body>',
            f'<div style="{self.styles["container"]}">']
        
        # 按来源分组并排序
        sorted_news = sorted(news_list, key=lambda x: (x['source'], x['published']), reverse=True)
        grouped_news = {}
        for source, items in groupby(sorted_news, key=lambda x: x['source']):
            grouped_news[source] = list(items)
        
        # 添加每个来源的卡片
        for source_name, articles in grouped_news.items():
            html_parts.append(self.generate_source_card(source_name, articles))
        
        html_parts.extend(['</div>', '</body>', '</html>'])
        
        # 保存到文件
        html_content = "\n".join(html_parts)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nHTML文件已生成：{output_path}（共 {len(news_list)} 条内容）") 