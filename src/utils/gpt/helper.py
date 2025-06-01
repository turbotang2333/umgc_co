from openai import OpenAI
from typing import Dict, List, Optional
from .config import GPTConfig
import os

class GPTHelper:
    def __init__(self, config: Optional[GPTConfig] = None):
        """初始化GPT助手
        
        Args:
            config: GPT配置对象，如果为None则创建新的配置对象
        """
        self.config = config or GPTConfig()
        
        # 检查环境变量，看是否有代理相关配置
        print(f"[DEBUG] HTTP_PROXY: {os.getenv('HTTP_PROXY', 'None')}")
        print(f"[DEBUG] HTTPS_PROXY: {os.getenv('HTTPS_PROXY', 'None')}")
        print(f"[DEBUG] http_proxy: {os.getenv('http_proxy', 'None')}")
        print(f"[DEBUG] https_proxy: {os.getenv('https_proxy', 'None')}")
        
        # 显示实际使用的配置（不完整显示敏感信息）
        api_key_display = f"{self.config.API_KEY[:8]}...{self.config.API_KEY[-4:]}" if self.config.API_KEY else "None"
        print(f"[DEBUG] 使用的API Key: {api_key_display}")
        print(f"[DEBUG] 使用的Base URL: {self.config.BASE_URL}")
        
        # 尝试使用base_url的初始化方式
        try:
            # 直接使用api_key和base_url参数
            self.client = OpenAI(
                api_key=self.config.API_KEY,
                base_url=self.config.BASE_URL
            )
            print(f"[DEBUG] 成功使用api_key和base_url初始化OpenAI客户端")
        except Exception as e:
            print(f"[DEBUG] 使用api_key和base_url初始化失败: {e}")
            try:
                # 方法2: 使用字典方式传参
                self.client = OpenAI(**{
                    'api_key': self.config.API_KEY,
                    'base_url': self.config.BASE_URL
                })
                print(f"[DEBUG] 成功使用字典参数初始化OpenAI客户端")
            except Exception as e2:
                print(f"[DEBUG] 字典参数初始化也失败: {e2}")
                # 方法3: 只使用api_key（不推荐，会调用官方API）
                try:
                    self.client = OpenAI(api_key=self.config.API_KEY)
                    print(f"[DEBUG] 警告：只使用api_key初始化，将调用OpenAI官方API")
                except Exception as e3:
                    print(f"[DEBUG] 所有初始化方法都失败: {e3}")
                    raise e3
    
    def summarize_text(
        self, 
        text: str,
        system_rules: Optional[List[str]] = None,
        max_chars: Optional[int] = None
    ) -> str:
        """文本总结方法
        
        Args:
            text: 需要总结的文本
            system_rules: 自定义规则列表，如果为None则使用配置中的规则
            max_chars: 自定义字符限制，如果为None则使用配置中的限制
        
        Returns:
            str: 总结后的文本
        """
        try:
            rules = system_rules or self.config.SYSTEM_RULES
            chars_limit = max_chars or self.config.MAX_CHARS
            
            system_prompt = "你是一个专业的内容编辑。\n" + "\n".join(rules)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            
            result = response.choices[0].message.content.strip('"').strip("'")
            return result.rstrip('。')
            
        except Exception as e:
            return f"总结失败: {str(e)}"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """通用对话方法
        
        Args:
            messages: 对话历史
            system_prompt: 系统提示词，如果为None则使用默认提示词
        
        Returns:
            str: GPT的回复
        """
        try:
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"对话失败: {str(e)}"