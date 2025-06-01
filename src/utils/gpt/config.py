from typing import List, Optional
import os

class GPTConfig:
    """GPT配置类"""
    
    def __init__(self):
        # 基础配置
        self.API_KEY: str = os.getenv('GPT_API_KEY', '')
        self.BASE_URL: str = "https://api.gptsapi.net/v1"
        
        # 项目特定配置
        self.SYSTEM_RULES: List[str] = [
            "严格按照[主语+动作+关键信息]格式输出",
            "只保留一个完整陈述句",
            "删除所有附加句和补充说明",
            "不使用任何标点符号结尾",
            "所有作品名称严格使用书名号《》，包括中英文",
            "禁止使用：形容词、评价词、感叹词",
            "禁止使用：情感类描述（共鸣/感动/热爱等）",
            "禁止使用：号召性、祝愿性词语"
        ]
        self.MAX_CHARS: int = 30
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        if not self.API_KEY:
            raise ValueError("请设置GPT_API_KEY环境变量")
        if not self.SYSTEM_RULES:
            raise ValueError("请设置SYSTEM_RULES")
        if not self.MAX_CHARS:
            raise ValueError("请设置MAX_CHARS")
        return True 