# RSS Newsletter Generator

自动获取微信公众号RSS更新，使用AI总结内容并生成HTML格式的新闻简报。

## 功能特点

- 自动获取RSS源更新
- 使用GPT进行内容总结
- 生成美观的HTML新闻简报
- 支持自定义配置

## 项目结构

```
project/
├── src/
│   ├── config/
│   │   ├── default/        # 默认配置
│   │   │   ├── subscriptions.opml  # RSS订阅源配置
│   │   │   └── gpt_config.json     # GPT配置
│   │   ├── custom/        # 用户自定义配置（可选）
│   │   └── config.py      # 主配置文件
│   ├── services/          # 核心服务
│   │   ├── ai.py         # AI总结服务
│   │   └── template.py   # HTML模板服务
│   ├── sources/          # 新闻来源
│   │   ├── base.py      # 基类
│   │   └── rss.py       # RSS实现
│   ├── utils/           # 工具类
│   │   └── gpt_tools/   # GPT工具包
│   └── main.py          # 主程序入口
```

## 环境要求

- Python 3.7+
- 见 requirements.txt

## 配置说明

1. 创建 `.env` 文件，包含以下配置：
```
GPT_API_KEY=your-api-key-here
```

2. 自定义RSS源（可选）：
   - 复制 `src/config/default/subscriptions.opml` 到 `src/config/custom/`
   - 在自定义配置中添加或修改RSS源

3. 自定义GPT配置（可选）：
   - 复制 `src/config/default/gpt_config.json` 到 `src/config/custom/`
   - 修改AI总结规则和参数

## 使用方法

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行程序：
```bash
python src/main.py
```

## 添加新的RSS源

在 OPML 文件中添加新的 `outline` 节点：
```xml
<outline 
    text="订阅源名称" 
    type="rss" 
    xmlUrl="RSS源的URL地址" 
    title="订阅源名称" />
``` 