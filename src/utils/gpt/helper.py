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
        
        # 尝试最简单的初始化方式
        try:
            # 方法1: 只使用api_key
            self.client = OpenAI(api_key=self.config.API_KEY)
            print(f"[DEBUG] 成功使用api_key初始化OpenAI客户端")
        except Exception as e:
            print(f"[DEBUG] 仅使用api_key初始化失败: {e}")
            try:
                # 方法2: 使用关键字参数
                self.client = OpenAI(**{
                    'api_key': self.config.API_KEY,
                    'base_url': self.config.BASE_URL
                })
                print(f"[DEBUG] 成功使用关键字参数初始化OpenAI客户端")
            except Exception as e2:
                print(f"[DEBUG] 关键字参数初始化也失败: {e2}")
                # 方法3: 尝试清除可能的代理环境变量
                try:
                    # 临时清除代理环境变量
                    old_env = {}
                    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
                    for var in proxy_vars:
                        if var in os.environ:
                            old_env[var] = os.environ[var]
                            del os.environ[var]
                    
                    self.client = OpenAI(api_key=self.config.API_KEY)
                    print(f"[DEBUG] 清除代理环境变量后成功初始化")
                    
                    # 恢复环境变量
                    for var, value in old_env.items():
                        os.environ[var] = value
                        
                except Exception as e3:
                    print(f"[DEBUG] 清除代理环境变量后仍失败: {e3}")
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