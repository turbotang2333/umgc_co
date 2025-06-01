from sources.rss import RSSSource
from managers.news_manager import NewsManager
from services.ai import AISummarizer
from services.template import HTMLTemplate
from services.database import NewsDatabase
from utils.gpt import GPTConfig
from utils.date_service import DateRangeService
import os
import json
import argparse
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from datetime import datetime, date
import sqlite3
from typing import Optional

# 加载环境变量
load_dotenv()

def create_news_manager():
    """创建并配置新闻管理器"""
    manager = NewsManager()
    
    # 注册RSS来源
    rss_source = RSSSource('src/config/default/subscriptions.opml')
    manager.register_source(rss_source)
    
    # 未来可以在这里添加其他类型的新闻来源
    # api_source = APISource(...)
    # manager.register_source(api_source)
    
    return manager

def fetch_news(args):
    """获取新闻"""
    # 解析日期范围
    start_date, end_date = DateRangeService.parse_args_to_date_range(args)
    
    print(f"\n获取新闻 - 时间范围: {start_date.strftime('%Y-%m-%d %H:%M')} 到 {end_date.strftime('%Y-%m-%d %H:%M')}")
    
    # 创建新闻管理器
    manager = create_news_manager()
    
    # 获取指定来源类型的新闻（如果有指定的话）
    source_types = getattr(args, 'sources', None)
    if source_types:
        source_types = [s.strip() for s in source_types.split(',')]
    
    news_list = manager.get_all_news(start_date, end_date, source_types)
    
    if news_list:
        print(f"\n获取到 {len(news_list)} 条新闻")
        
        # 保存到数据库
        if getattr(args, 'save_to_db', True):  # 默认保存到数据库
            db = NewsDatabase()
            saved_count = db.save_news_batch(news_list)
            print(f"已保存 {saved_count} 条新闻到数据库")
        
        # 可选：保存到临时文件用于调试
        if getattr(args, 'save_temp', False):
            with open('temp_news.json', 'w', encoding='utf-8') as f:
                json.dump(news_list, f, ensure_ascii=False, default=str)
            print("已保存到临时文件 temp_news.json（调试用）")
    else:
        print("\n没有找到任何新闻更新")
    
    return news_list

def query_news(args):
    """查询历史新闻"""
    db = NewsDatabase()
    
    if hasattr(args, 'query_date') and args.query_date:
        # 查询指定日期的新闻
        target_date = datetime.strptime(args.query_date, '%Y-%m-%d').date()
        news_list = db.get_news_by_date(target_date)
        print(f"\n{target_date} 的新闻 ({len(news_list)} 条):")
        
    elif hasattr(args, 'query_range') and args.query_range:
        # 查询日期范围的新闻
        start_str, end_str = args.query_range
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        news_list = db.get_news_by_date_range(start_date, end_date)
        print(f"\n{start_date} 到 {end_date} 的新闻 ({len(news_list)} 条):")
        
    elif hasattr(args, 'query_source') and args.query_source:
        # 查询指定来源的新闻
        news_list = db.get_news_by_source(args.query_source)
        print(f"\n来源 '{args.query_source}' 的新闻 ({len(news_list)} 条):")
        
    elif hasattr(args, 'search') and args.search:
        # 搜索新闻
        news_list = db.search_news(args.search)
        print(f"\n包含 '{args.search}' 的新闻 ({len(news_list)} 条):")
        
    else:
        print("\n请指定查询条件")
        return
    
    # 显示新闻列表
    for news in news_list:
        published = news['published']
        if isinstance(published, str):
            published = datetime.fromisoformat(published.replace('Z', '+00:00'))
        
        # 适配新的数据库结构
        source_name = news.get('source_name', news.get('source', '未知来源'))
        
        # 使用只显示日期的格式
        published_str = DateRangeService.format_date_only(published)
        print(f"- [{published_str}] {source_name}: {news['title']}")
        if news.get('summary'):
            print(f"  总结: {news['summary']}")
        print(f"  链接: {news['link']}")
        print()

def show_stats():
    """显示数据库统计信息"""
    db = NewsDatabase()
    stats = db.get_statistics()
    
    print("\n=== 数据库统计信息 ===")
    print(f"总新闻数: {stats['total_news']}")
    
    if stats['date_range']['earliest']:
        print(f"数据范围: {stats['date_range']['earliest']} 到 {stats['date_range']['latest']}")
    
    print("\n来源统计:")
    for source, count in stats['source_stats'].items():
        print(f"  {source}: {count} 条")
    
    print("\n最近日期统计:")
    for date_str, count in stats['recent_date_stats'].items():
        print(f"  {date_str}: {count} 条")

def summarize_news(start_date=None, end_date=None):
    """AI总结新闻
    
    Args:
        start_date: Optional[datetime] 开始时间
        end_date: Optional[datetime] 结束时间
    """
    try:
        # 从数据库读取新闻
        db = NewsDatabase()
        
        # 获取指定时间范围内未总结的新闻
        with db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if start_date and end_date:
                # 将datetime转换为日期字符串以匹配数据库格式
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT * FROM news_items 
                    WHERE published >= ? AND published <= ? 
                    AND (summary IS NULL OR summary = '')
                    ORDER BY published DESC
                ''', (start_date_str, end_date_str))
            else:
                # 如果没有指定时间范围，则处理今天抓取的新闻
                fetch_date = date.today()
                cursor.execute('''
                    SELECT * FROM news_items 
                    WHERE date(fetch_timestamp) = ? AND (summary IS NULL OR summary = '')
                    ORDER BY published DESC
                ''', (fetch_date,))
            
            news_list = [dict(row) for row in cursor.fetchall()]
        
        if not news_list:
            time_desc = f"{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}" if start_date and end_date else "今天"
            print(f"\n{time_desc} 没有需要总结的新闻")
            return []
        
        print(f"\n找到 {len(news_list)} 条需要AI总结的新闻")
        
        # 初始化GPT配置
        gpt_config = GPTConfig()
        gpt_config.validate()
        
        # AI总结
        ai_summarizer = AISummarizer(gpt_config)
        summarized_news = ai_summarizer.summarize_news(news_list)
        
        # 直接更新数据库中的总结
        with db.get_connection() as conn:
            cursor = conn.cursor()
            for news in summarized_news:
                if news.get('summary'):
                    cursor.execute(
                        'UPDATE news_items SET summary = ? WHERE id = ?',
                        (news['summary'], news['id'])
                    )
            conn.commit()
        print("已更新数据库中的新闻总结")
        
        return summarized_news
    except Exception as e:
        print(f"\nAI总结出错: {str(e)}")
        return []

def generate_html(start_date=None, end_date=None):
    """生成HTML文件
    
    Args:
        start_date: Optional[datetime] 开始时间
        end_date: Optional[datetime] 结束时间
    """
    try:
        # 从数据库读取已总结的新闻
        db = NewsDatabase()
        
        # 获取指定时间范围内已总结的新闻
        with db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if start_date and end_date:
                # 将datetime转换为日期字符串以匹配数据库格式
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT * FROM news_items 
                    WHERE published >= ? AND published <= ? 
                    AND summary IS NOT NULL AND summary != ''
                    ORDER BY published DESC
                ''', (start_date_str, end_date_str))
            else:
                # 如果没有指定时间范围，则处理今天抓取的新闻
                fetch_date = date.today()
                cursor.execute('''
                    SELECT * FROM news_items 
                    WHERE date(fetch_timestamp) = ? AND summary IS NOT NULL AND summary != ''
                    ORDER BY published DESC
                ''', (fetch_date,))
            
            news_list = [dict(row) for row in cursor.fetchall()]
        
        if not news_list:
            time_desc = f"{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}" if start_date and end_date else "今天"
            print(f"\n{time_desc} 没有已总结的新闻，请先运行AI总结步骤")
            return False
        
        print(f"\n找到 {len(news_list)} 条已总结的新闻")
        
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

def send_email(email_type="normal", error_message="", time_range=""):
    """发送邮件
    
    Args:
        email_type: str 邮件类型 - "normal"(正常新闻), "no_content"(无内容), "error"(错误通知)
        error_message: str 错误信息（当email_type为"error"时使用）
        time_range: str 时间范围描述
    """
    try:
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
        
        # 根据邮件类型生成不同的内容
        if email_type == "normal":
            # 正常新闻邮件
            if not os.path.exists('news_summary.html'):
                print("\n未找到HTML文件 news_summary.html，请先运行生成HTML步骤")
                return False
                
            # 读取HTML内容
            with open('news_summary.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            subject = f'音乐新闻日报 - {datetime.now().strftime("%Y-%m-%d")}'
            
        elif email_type == "no_content":
            # 无内容通知邮件
            subject = f'音乐新闻日报 - 无内容通知 - {datetime.now().strftime("%Y-%m-%d")}'
            html_content = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <title>无内容通知</title>
                <style>
                    body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    .header {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                    .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #7f8c8d; font-size: 12px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <h1 class="header">🎵 音乐新闻日报</h1>
                <div class="content">
                    <h2>📭 无内容通知</h2>
                    <p><strong>时间范围：</strong>{time_range}</p>
                    <p>在指定时间范围内没有获取到任何音乐新闻内容。</p>
                    <p>可能的原因：</p>
                    <ul>
                        <li>各音乐媒体在该时间段内没有发布新内容</li>
                        <li>RSS源临时不可访问</li>
                        <li>内容发布时间与抓取时间不匹配</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
            </body>
            </html>
            """
            
        elif email_type == "error":
            # 错误通知邮件
            subject = f'音乐新闻日报 - 错误通知 - {datetime.now().strftime("%Y-%m-%d")}'
            html_content = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <title>错误通知</title>
                <style>
                    body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    .header {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }}
                    .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .error {{ background-color: #fee; border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; }}
                    .footer {{ text-align: center; color: #7f8c8d; font-size: 12px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <h1 class="header">🎵 音乐新闻日报</h1>
                <div class="content">
                    <h2>⚠️ 执行错误通知</h2>
                    <p><strong>时间范围：</strong>{time_range}</p>
                    <p>在处理音乐新闻时遇到问题：</p>
                    <div class="error">
                        <strong>错误详情：</strong><br>
                        {error_message}
                    </div>
                    <p>请检查系统日志以获取更多详细信息。</p>
                </div>
                <div class="footer">
                    <p>自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
            </body>
            </html>
            """
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
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
            print(f"\n尝试发送{subject}...")
            print("尝试SSL连接（端口465）...")
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

def cleanup_db(args):
    """清理数据库旧数据"""
    days = getattr(args, 'days_to_keep', 90)
    db = NewsDatabase()
    deleted_count = db.cleanup_old_data(days)
    return deleted_count

def clear_db():
    """清空数据库所有数据"""
    db = NewsDatabase()
    deleted_count = db.clear_all_data()
    return deleted_count

def show_summary():
    """显示新闻来源摘要"""
    manager = create_news_manager()
    summary = manager.get_news_summary()
    
    print("\n=== 新闻来源摘要 ===")
    print(f"总来源数: {summary['total_sources']}")
    print("\n来源类型统计:")
    for source_type, count in summary['source_types'].items():
        print(f"  {source_type}: {count} 个")
    
    print("\n详细来源列表:")
    for source in summary['sources']:
        print(f"  - {source['name']} ({source['type']})")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='新闻处理工具')
    parser.add_argument('action', choices=['fetch', 'summarize', 'html', 'email', 'all', 'cleanup', 'summary', 'query', 'stats', 'cleanup-db', 'clear-db'],
                      help='执行的操作：fetch=获取新闻, summarize=AI总结, html=生成HTML, email=发送邮件, all=执行所有步骤, cleanup=清理临时文件, summary=显示来源摘要, query=查询历史新闻, stats=显示统计信息, cleanup-db=清理数据库旧数据, clear-db=清空数据库所有数据')
    
    # 日期相关参数
    parser.add_argument('--date', type=str, help='指定日期 (YYYY-MM-DD)')
    parser.add_argument('--date-range', nargs=2, metavar=('START', 'END'), help='指定日期范围 (YYYY-MM-DD YYYY-MM-DD)')
    parser.add_argument('--days', type=int, help='过去N天')
    
    # 来源相关参数
    parser.add_argument('--sources', type=str, help='指定来源类型，用逗号分隔 (如: rss,api)')
    
    # 查询相关参数
    parser.add_argument('--query-date', type=str, help='查询指定日期的新闻 (YYYY-MM-DD)')
    parser.add_argument('--query-range', nargs=2, metavar=('START', 'END'), help='查询日期范围的新闻 (YYYY-MM-DD YYYY-MM-DD)')
    parser.add_argument('--query-source', type=str, help='查询指定来源的新闻')
    parser.add_argument('--search', type=str, help='搜索包含关键词的新闻')
    
    # 数据库相关参数
    parser.add_argument('--no-save-db', action='store_true', help='不保存到数据库')
    parser.add_argument('--days-to-keep', type=int, default=90, help='清理数据库时保留的天数 (默认90天)')
    
    # 调试相关参数
    parser.add_argument('--save-temp', action='store_true', help='保存临时文件用于调试')
    
    args = parser.parse_args()
    args.save_to_db = not args.no_save_db  # 转换为正向逻辑
    
    # 确定处理日期
    fetch_date = None
    if hasattr(args, 'date') and args.date:
        fetch_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    elif not hasattr(args, 'date_range'):
        fetch_date = date.today()
    
    # 根据参数执行相应功能
    if args.action == 'fetch':
        fetch_news(args)
    elif args.action == 'summarize':
        # 如果指定了时间范围参数，则基于发布时间处理
        if hasattr(args, 'date_range') and args.date_range:
            start_date, end_date = DateRangeService.parse_args_to_date_range(args)
            summarize_news(start_date, end_date)
        elif hasattr(args, 'days') and args.days:
            start_date, end_date = DateRangeService.parse_args_to_date_range(args)
            summarize_news(start_date, end_date)
        else:
            # 默认处理今天抓取的新闻
            summarize_news()
    elif args.action == 'html':
        # 如果指定了时间范围参数，则基于发布时间处理
        if hasattr(args, 'date_range') and args.date_range:
            start_date, end_date = DateRangeService.parse_args_to_date_range(args)
            generate_html(start_date, end_date)
        elif hasattr(args, 'days') and args.days:
            start_date, end_date = DateRangeService.parse_args_to_date_range(args)
            generate_html(start_date, end_date)
        else:
            # 默认处理今天抓取的新闻
            generate_html()
    elif args.action == 'email':
        send_email()
    elif args.action == 'cleanup':
        cleanup()
    elif args.action == 'summary':
        show_summary()
    elif args.action == 'query':
        query_news(args)
    elif args.action == 'stats':
        show_stats()
    elif args.action == 'cleanup-db':
        cleanup_db(args)
    elif args.action == 'clear-db':
        clear_db()
    elif args.action == 'all':
        # 记录执行过程中的错误
        execution_errors = []
        
        # 获取新闻（可能没有新的）
        try:
            news_list = fetch_news(args)
        except Exception as e:
            error_msg = f"获取新闻时出错: {str(e)}"
            print(f"\n{error_msg}")
            execution_errors.append(error_msg)
            news_list = []
        
        # 解析时间范围用于后续处理
        start_date, end_date = DateRangeService.parse_args_to_date_range(args)
        time_range_desc = f"{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}"
        
        # 检查指定时间范围内是否有新闻（基于发布时间）
        db = NewsDatabase()
        try:
            with db.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # 将datetime转换为日期字符串以匹配数据库格式
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT COUNT(*) as count FROM news_items 
                    WHERE published >= ? AND published <= ?
                ''', (start_date_str, end_date_str))
                existing_count = cursor.fetchone()['count']
        except Exception as e:
            error_msg = f"查询数据库时出错: {str(e)}"
            print(f"\n{error_msg}")
            execution_errors.append(error_msg)
            existing_count = 0
        
        if news_list or existing_count > 0:
            print(f"\n时间范围内总共有 {existing_count} 条新闻")
            
            # 总结新闻（处理该时间范围内未总结的）
            try:
                summarized_news = summarize_news(start_date, end_date)
            except Exception as e:
                error_msg = f"AI总结时出错: {str(e)}"
                print(f"\n{error_msg}")
                execution_errors.append(error_msg)
                summarized_news = []
            
            # 生成HTML（基于该时间范围内所有已总结的新闻）
            html_success = False
            try:
                html_success = generate_html(start_date, end_date)
            except Exception as e:
                error_msg = f"HTML生成时出错: {str(e)}"
                print(f"\n{error_msg}")
                execution_errors.append(error_msg)
            
            # 发送邮件
            if execution_errors:
                # 有错误发生，发送错误通知邮件
                error_details = "\n".join(execution_errors)
                send_email("error", error_details, time_range_desc)
            elif html_success:
                # 正常情况，发送新闻邮件
                send_email("normal", "", time_range_desc)
            else:
                # HTML生成失败，发送错误通知
                send_email("error", "HTML生成失败，无法创建新闻邮件", time_range_desc)
        else:
            # 没有任何新闻数据，发送无内容通知邮件
            print(f"\n指定时间范围 {time_range_desc} 没有任何新闻数据")
            if execution_errors:
                # 即使没有新闻，但有错误发生
                error_details = f"没有获取到新闻内容，且出现以下错误：\n" + "\n".join(execution_errors)
                send_email("error", error_details, time_range_desc)
            else:
                # 单纯没有内容
                send_email("no_content", "", time_range_desc)
        
        # 清理临时文件
        cleanup()

if __name__ == "__main__":
    main() 