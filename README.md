# 中国音乐新闻聚合系统 (UMGC News)

自动获取音乐行业RSS新闻，使用AI总结内容并生成HTML邮件简报。支持智能通知和历史数据检索。

## ✨ 功能特点

- 🎵 **音乐行业专注**：聚合腾讯音乐、索尼、华纳、摩登天空等主流音乐媒体
- 🤖 **AI智能总结**：使用GPT生成25字以内精准摘要，支持标题+字幕双输入
- 📧 **智能邮件通知**：三种邮件类型（正常新闻/无内容/错误通知）
- 🗄️ **数据库存储**：SQLite本地存储，支持字幕字段和历史检索
- ⏰ **自动化运行**：GitHub Actions每日定时抓取
- 🎯 **灵活时间选择**：支持昨天/过去N天/自定义日期范围

## 🏗️ 项目结构

```
project/
├── src/
│   ├── config/default/
│   │   └── subscriptions.opml     # RSS订阅源配置
│   ├── services/
│   │   ├── ai.py                  # AI总结服务
│   │   ├── database.py            # 数据库服务  
│   │   └── template.py            # HTML模板服务
│   ├── sources/
│   │   ├── base.py                # 新闻源基类
│   │   └── rss.py                 # RSS实现
│   ├── managers/
│   │   └── news_manager.py        # 新闻管理器
│   ├── utils/
│   │   ├── gpt/                   # GPT工具包
│   │   └── date_service.py        # 日期处理服务
│   └── main.py                    # 主程序入口
├── data/
│   └── news.db                    # SQLite数据库
└── .github/workflows/
    └── daily-news.yml             # 定时任务配置
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
创建`.env`文件：
```env
# AI配置
GPT_API_KEY=your-api-key
GPT_BASE_URL=https://api.openai.com/v1

# 邮件配置
SMTP_SERVER=smtp.163.com
SMTP_USERNAME=your-email@163.com
SMTP_PASSWORD=your-password
SENDER_EMAIL=your-email@163.com
RECEIVER_EMAIL=receiver@gmail.com
```

### 3. 运行
```bash
# 完整流程（获取→总结→生成HTML→发送邮件）
python src/main.py all

# 获取昨天新闻（默认）
python src/main.py fetch

# 获取过去7天新闻
python src/main.py all --days 7
```

## 📋 使用方法

### 基础操作
```bash
# 获取新闻并处理
python src/main.py all                          # 昨天的新闻
python src/main.py all --days 7                # 过去7天
python src/main.py all --date 2024-12-25       # 指定日期
python src/main.py all --date-range 2024-12-20 2024-12-25  # 日期范围
```

### 数据查询
```bash
python src/main.py stats                        # 数据库统计
python src/main.py query --search "草莓音乐节"   # 关键词搜索
python src/main.py query --query-date 2024-12-25           # 指定日期
python src/main.py query --query-source "摩登天空"         # 指定来源
```

### 分步执行
```bash
python src/main.py fetch      # 1. 获取新闻
python src/main.py summarize  # 2. AI总结
python src/main.py html       # 3. 生成HTML  
python src/main.py email      # 4. 发送邮件
```

## ⚙️ GitHub Actions 自动化

### 自动运行
- **时间**：每天北京时间8点（UTC 0点）
- **内容**：获取前一天的音乐新闻
- **通知**：自动发送邮件（有内容/无内容/出错都会通知）

### 手动触发
在GitHub仓库Actions页面可手动运行，支持三种模式：
- **默认模式**：获取昨天的新闻
- **过去N天**：可指定天数（如7天）
- **日期范围**：可指定开始和结束日期

## 🗃️ 数据库结构

```sql
news_items (
    id TEXT PRIMARY KEY,           -- 唯一ID
    manager_name TEXT,             -- 管理器名称
    source_type TEXT NOT NULL,     -- 来源类型（rss）
    source_name TEXT NOT NULL,     -- 来源名称
    published DATETIME NOT NULL,   -- 发布时间
    title TEXT NOT NULL,           -- 标题
    subtitle TEXT,                 -- 字幕/摘要（200字以内）
    summary TEXT,                  -- AI总结（25字以内）
    content TEXT NOT NULL,         -- 正文内容
    link TEXT NOT NULL,            -- 原文链接
    fetch_timestamp DATETIME,      -- 抓取时间
    raw_data TEXT                  -- 原始数据JSON
)
```

## 📧 邮件通知系统

系统会根据不同情况发送对应邮件：

### 正常新闻邮件
- **触发**：成功获取并处理新闻
- **内容**：完整的HTML新闻简报，包含AI总结

### 无内容通知邮件  
- **触发**：指定时间范围内没有新闻
- **内容**：说明情况和可能原因

### 错误通知邮件
- **触发**：处理过程中出现错误
- **内容**：详细错误信息，便于排查问题

## 🎼 音乐新闻源

目前聚合的音乐媒体：
- 腾讯音乐娱乐集团
- 索尼音乐娱乐
- 华纳音乐
- 摩登天空
- 太合音乐
- 滚石唱片

## 🔧 高级配置

### 添加新RSS源
编辑`src/config/default/subscriptions.opml`：
```xml
<outline text="新音乐媒体" type="rss" 
         xmlUrl="https://example.com/rss" 
         title="新音乐媒体" />
```

### 数据库维护
```bash
python src/main.py cleanup-db --days-to-keep 30  # 清理30天前数据
python src/main.py clear-db                      # 清空所有数据
```

## 📞 技术支持

如遇问题，可查看：
1. GitHub Actions运行日志
2. 邮件错误通知内容
3. 本地运行时的控制台输出

---

**适用场景**：音乐行业从业者、音乐爱好者、娱乐媒体工作者的日常新闻获取需求 