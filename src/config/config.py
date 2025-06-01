import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# OPML文件配置
DEFAULT_OPML = os.path.join(BASE_DIR, 'src', 'config', 'default', 'subscriptions.opml')
CUSTOM_OPML = os.path.join(BASE_DIR, 'src', 'config', 'custom', 'subscriptions.opml')

# 使用自定义配置（如果存在），否则使用默认配置
OPML_FILE = CUSTOM_OPML if os.path.exists(CUSTOM_OPML) else DEFAULT_OPML

# 邮件配置
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')

# 定时任务配置
SCHEDULE_HOUR = int(os.getenv('SCHEDULE_HOUR', 9))  # 默认早上9点
SCHEDULE_MINUTE = int(os.getenv('SCHEDULE_MINUTE', 0)) 