from typing import List, Optional
import os

class GPTConfig:
    """GPT配置类"""
    
    def __init__(self):
        # 基础配置
        self.API_KEY: str = os.getenv('GPT_API_KEY', '')
        self.BASE_URL: str = os.getenv('GPT_BASE_URL', 'https://api.openai.com/v1')
        
        # 项目特定配置 - 音乐行业新闻摘要专用
        self.SYSTEM_RULES: List[str] = [
            "你是一位音乐行业新闻摘要专家，请根据标题和副标题生成纯事实性摘要",
            "严格要求：只能输出一行25字以内的文字，禁用感叹号和换行符，禁止使用换行符或多行输出",
            "保留原标题中的核心主体（活动名称/乐队名称/报告名称）", 
            "提取所有关键动态动词：发布、签约、上线、揭晓、收官、巡演、预告、升级等",
            "删除所有营销描述/情感词（如极致浪漫、音浪交织）",
            "省略时间/地点修饰词（除非必要）",
            "作品名称使用完整书名号《》，确保不截断",
        ]
        self.MAX_CHARS: int = 25
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        if not self.API_KEY:
            raise ValueError("请设置GPT_API_KEY环境变量")
        if not self.BASE_URL:
            raise ValueError("请设置GPT_BASE_URL环境变量")
        if not self.SYSTEM_RULES:
            raise ValueError("请设置SYSTEM_RULES")
        if not self.MAX_CHARS:
            raise ValueError("请设置MAX_CHARS")
        return True 