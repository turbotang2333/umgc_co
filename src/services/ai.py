from typing import List, Dict, Optional
from utils.gpt import GPTHelper, GPTConfig
import time

class AISummarizer:
    """AI总结服务"""
    
    def __init__(self, gpt_config: Optional[GPTConfig] = None):
        """初始化AI总结服务
        
        Args:
            gpt_config: GPTConfig GPT配置，如果为None则使用默认配置
        """
        self.gpt = GPTHelper(gpt_config)
    
    def summarize_news(self, news_list: List[Dict]) -> List[Dict]:
        """总结新闻列表
        
        Args:
            news_list: List[Dict] 新闻列表
        
        Returns:
            List[Dict] 添加了summary字段的新闻列表
        """
        print("\n开始AI总结...")
        total = len(news_list)
        
        for i, news in enumerate(news_list, 1):
            try:
                # 使用GPT总结标题和副标题
                title = news['title']
                subtitle = news.get('subtitle', '')
                summary = self.gpt.summarize_text(title, subtitle)
                news['summary'] = summary
                print(f"总结进度: {i}/{total}")
                print(f"原标题: {title}")
                if subtitle:
                    print(f"副标题: {subtitle}")
                print(f"总结: {summary}")
                
                # 添加延时避免API调用过于频繁
                if i < total:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"总结新闻时出错: {str(e)}")
                news['summary'] = news['title']
        
        print("总结完成")
        return news_list 