from sources.rss import RSSSource
from services.ai import AISummarizer
from services.template import HTMLTemplate
from utils.gpt import GPTConfig
import os
import json
import argparse
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from datetime import datetime

# 加载环境变量
load_dotenv()

def fetch_news():
    """获取新闻"""
    rss_source = RSSSource('src/config/default/subscriptions.opml')
    news_list = rss_source.get_news()
    
    # 保存原始新闻到临时文件
    if news_list:
        with open('temp_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, default=str)
        print(f"\n获取到 {len(news_list)} 条新闻，已保存到 temp_news.json")
    else:
        print("\n没有找到任何新闻更新")
    
    return news_list

def summarize_news():
    """AI总结新闻"""
    try:
        # 读取原始新闻
        if not os.path.exists('temp_news.json'):
            print("\n未找到原始新闻文件 temp_news.json，请先运行获取新闻步骤")
            return None
            
        with open('temp_news.json', 'r', encoding='utf-8') as f:
            news_list = json.load(f)
        
        # 初始化GPT配置
        gpt_config = GPTConfig()
        gpt_config.validate()
        
        # AI总结
        ai_summarizer = AISummarizer(gpt_config)
        summarized_news = ai_summarizer.summarize_news(news_list)
        
        # 保存总结后的新闻
        with open('temp_summarized_news.json', 'w', encoding='utf-8') as f:
            json.dump(summarized_news, f, ensure_ascii=False, default=str)
        print("\n新闻总结完成，已保存到 temp_summarized_news.json")
        
        return summarized_news
    except Exception as e:
        print(f"\nAI总结出错: {str(e)}")
        return None

def generate_html():
    """生成HTML文件"""
    try:
        # 读取总结后的新闻
        if not os.path.exists('temp_summarized_news.json'):
            print("\n未找到总结后的新闻文件 temp_summarized_news.json，请先运行AI总结步骤")
            return False
            
        with open('temp_summarized_news.json', 'r', encoding='utf-8') as f:
            news_list = json.load(f)
            
        # 将字符串日期转换为datetime对象
        for news in news_list:
            if isinstance(news['published'], str):
                news['published'] = datetime.fromisoformat(news['published'].replace('Z', '+00:00'))
        
        # 生成HTML
        html_template = HTMLTemplate()
        html_template.generate_html(news_list)
        print("\nHTML生成完成")
        return True
    except Exception as e:
        print(f"\nHTML生成出错: {str(e)}")
        return False

def send_email():
    """发送邮件"""
    try:
        # 检查HTML文件是否存在
        if not os.path.exists('news_summary.html'):
            print("\n未找到HTML文件 news_summary.html，请先运行生成HTML步骤")
            return False
            
        # 读取HTML内容
        with open('news_summary.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # 从配置文件获取邮件设置
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.163.com')
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL')
        receiver_email = os.getenv('RECEIVER_EMAIL')
        
        # 验证必要的邮件配置
        if not all([smtp_username, smtp_password, sender_email, receiver_email]):
            print("\n邮件配置不完整，请检查环境变量：")
            print("SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL, RECEIVER_EMAIL")
            return False
            
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'音乐新闻日报 - {datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Date'] = formatdate(localtime=True)
        
        # 添加HTML内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 尝试不同的连接方式
        errors = []
        
        # 1. 尝试SSL连接（端口465）
        try:
            print("\n尝试SSL连接（端口465）...")
            with smtplib.SMTP_SSL(smtp_server, 465, timeout=10) as server:
                print("SSL连接成功，尝试登录...")
                server.login(smtp_username, smtp_password)
                print("登录成功，开始发送邮件...")
                server.send_message(msg)
                print(f"\n邮件已通过SSL发送至 {receiver_email}")
                return True
        except Exception as e:
            errors.append(f"SSL连接失败: {str(e)}")
            print(f"\nSSL连接失败，尝试普通连接...")
        
        # 2. 尝试普通SMTP连接（端口25）
        try:
            print("\n尝试普通连接（端口25）...")
            with smtplib.SMTP(smtp_server, 25, timeout=10) as server:
                print("连接成功，启用TLS...")
                server.starttls()
                print("TLS启用成功，尝试登录...")
                server.login(smtp_username, smtp_password)
                print("登录成功，开始发送邮件...")
                server.send_message(msg)
                print(f"\n邮件已通过普通SMTP发送至 {receiver_email}")
                return True
        except Exception as e:
            errors.append(f"普通连接失败: {str(e)}")
        
        # 如果所有尝试都失败
        print("\n所有连接方式都失败:")
        for error in errors:
            print(f"- {error}")
        print("\n请检查：")
        print("1. 邮箱地址是否正确")
        print("2. SMTP服务是否已开启")
        print("3. 授权码是否正确且是最新生成的")
        print("4. 网络环境是否限制了邮件端口")
        return False
            
    except Exception as e:
        print(f"\n邮件发送出错: {str(e)}")
        return False

def cleanup():
    """清理临时文件"""
    temp_files = ['temp_news.json', 'temp_summarized_news.json']
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)
    print("\n临时文件已清理")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='新闻处理工具')
    parser.add_argument('action', choices=['fetch', 'summarize', 'html', 'email', 'all', 'cleanup'],
                      help='执行的操作：fetch=获取新闻, summarize=AI总结, html=生成HTML, email=发送邮件, all=执行所有步骤, cleanup=清理临时文件')
    args = parser.parse_args()
    
    # 根据参数执行相应功能
    if args.action == 'fetch':
        fetch_news()
    elif args.action == 'summarize':
        summarize_news()
    elif args.action == 'html':
        generate_html()
    elif args.action == 'email':
        send_email()
    elif args.action == 'cleanup':
        cleanup()
    elif args.action == 'all':
        news_list = fetch_news()
        if news_list:
            summarized_news = summarize_news()
            if summarized_news:
                if generate_html():
                    send_email()
        cleanup()

if __name__ == "__main__":
    main() 