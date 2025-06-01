# RSS Newsletter Generator

自动获取微信公众号RSS更新，使用AI总结内容并生成HTML格式的新闻简报。支持SQLite数据库存储，便于历史数据检索。

## 功能特点

- 🔄 自动获取RSS源更新
- 🤖 使用GPT进行内容总结
- 📧 生成美观的HTML新闻简报并邮件发送
- 🗄️ SQLite数据库存储，支持历史数据检索
- 📅 灵活的日期范围选择
- 🔍 多维度检索功能
- ⚙️ 支持自定义配置
- 🏗️ 可扩展架构，便于添加新的新闻来源

## 项目结构

```
project/
├── src/
│   ├── config/
│   │   ├── default/        # 默认配置
│   │   │   ├── subscriptions.opml  # RSS订阅源配置
│   │   │   └── gpt_config.json     # GPT配置
│   │   └── custom/        # 用户自定义配置（可选）
│   ├── services/          # 核心服务
│   │   ├── ai.py         # AI总结服务
│   │   ├── template.py   # HTML模板服务
│   │   └── database.py   # 数据库服务
│   ├── sources/          # 新闻来源
│   │   ├── base.py      # 基类
│   │   └── rss.py       # RSS实现
│   ├── managers/         # 管理器
│   │   └── news_manager.py  # 新闻管理器
│   ├── utils/           # 工具类
│   │   ├── gpt/         # GPT工具包
│   │   └── date_service.py  # 日期处理服务
│   └── main.py          # 主程序入口
├── data/                # 数据目录
│   └── news.db         # SQLite数据库
└── .github/workflows/   # GitHub Actions定时任务
```

## 环境要求

- Python 3.7+
- 见 requirements.txt

## 配置说明

1. 创建 `.env` 文件，包含以下配置：
```
GPT_API_KEY=your-api-key-here
GPT_BASE_URL=https://api.openai.com/v1
SMTP_SERVER=smtp.163.com
SMTP_USERNAME=your-email@163.com
SMTP_PASSWORD=your-password
SENDER_EMAIL=your-email@163.com
RECEIVER_EMAIL=receiver@gmail.com
```

2. 自定义RSS源（可选）：
   - 复制 `src/config/default/subscriptions.opml` 到 `src/config/custom/`
   - 在自定义配置中添加或修改RSS源

## 使用方法

### 基础使用

```bash
# 安装依赖
pip install -r requirements.txt

# 获取昨天的新闻（默认行为，适合定时任务）
python src/main.py fetch

# 完整流程：获取、总结、生成HTML、发送邮件
python src/main.py all
```

### 日期选择

```bash
# 获取指定日期的新闻
python src/main.py fetch --date 2025-05-31

# 获取日期范围内的新闻
python src/main.py fetch --date-range 2025-05-25 2025-05-31

# 获取过去7天的新闻
python src/main.py fetch --days 7
```

### 数据库检索

```bash
# 查看数据库统计信息
python src/main.py stats

# 查询指定日期的新闻
python src/main.py query --query-date 2025-05-31

# 查询日期范围内的新闻
python src/main.py query --query-range 2025-05-25 2025-05-31

# 搜索包含关键词的新闻
python src/main.py query --search "草莓音乐节"

# 查询指定来源的新闻
python src/main.py query --query-source "摩登天空"
```

### 数据库管理

```bash
# 清理90天前的旧数据（默认）
python src/main.py cleanup-db

# 清理30天前的旧数据
python src/main.py cleanup-db --days-to-keep 30

# 获取新闻但不保存到数据库
python src/main.py fetch --no-save-db
```

### 分步执行

```bash
# 1. 获取新闻
python src/main.py fetch

# 2. AI总结
python src/main.py summarize

# 3. 生成HTML
python src/main.py html

# 4. 发送邮件
python src/main.py email

# 5. 清理临时文件
python src/main.py cleanup
```

## 定时任务

项目配置了GitHub Actions定时任务：
- **时间**: 每天北京时间9点
- **行为**: 获取前一天的新闻 → AI总结 → 生成HTML → 发送邮件
- **存储**: 自动保存到数据库，便于后续检索

## 数据库结构

```sql
news_items (
    id TEXT PRIMARY KEY,           -- 唯一标识符
    source TEXT,                   -- 来源名称
    source_type TEXT,              -- 来源类型（rss等）
    title TEXT,                    -- 标题
    content TEXT,                  -- 内容
    summary TEXT,                  -- AI总结
    published DATETIME,            -- 发布时间
    link TEXT,                     -- 原文链接
    fetch_date DATE,              -- 获取日期
    created_at DATETIME,          -- 创建时间
    raw_data TEXT                 -- 原始数据（JSON）
)
```

## 扩展性

### 添加新的新闻来源

1. 继承 `NewsSource` 基类
2. 实现 `get_news()` 方法
3. 在 `main.py` 中注册新来源

示例：
```python
class APISource(NewsSource):
    def get_news(self, start_date=None, end_date=None):
        # 实现API数据获取逻辑
        return news_list

# 在main.py中注册
manager.register_source(APISource())
```

### 添加新的RSS源

在 OPML 文件中添加新的 `outline` 节点：
```xml
<outline 
    text="订阅源名称" 
    type="rss" 
    xmlUrl="RSS源的URL地址" 
    title="订阅源名称" />
```

## 故障排除

### 常见问题

1. **时区问题**: 所有时间处理都使用UTC时区，确保一致性
2. **API限制**: 添加了延时机制避免频繁调用
3. **重复数据**: 数据库自动去重，基于唯一ID
4. **邮件发送**: 支持多种SMTP连接方式

### 调试模式

```bash
# 查看帮助
python src/main.py --help

# 查看新闻来源摘要
python src/main.py summary

# 测试获取但不保存到数据库
python src/main.py fetch --no-save-db --days 1
``` 