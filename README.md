# 多平台智能客服 Agent 系统

基于 [nanobot-ai](https://github.com/HKUDS/nanobot)（HKUDS，37K+ Stars）构建的智能客服 Agent，实现"知识库优先匹配 → MCP 工单兜底"的决策闭环。

## 架构

```
用户消息（飞书/钉钉/Telegram/CLI）
    │
    ▼
┌─────────────────────────────────┐
│        nanobot-ai Agent         │
│                                 │
│  AGENTS.md  → 行为约束          │
│  MEMORY.md  → 用户记忆          │
│                                 │
│  Skills:                        │
│  ├── faq     → 知识库匹配       │
│  └── ticket  → 工单管理         │
│                                 │
│  MCP Server:                    │
│  └── ticket_server.py → SQLite  │
└─────────────────────────────────┘
```

## 目录结构

```
multi-platform-cs-bot/
├── AGENTS.md               # Agent 身份与行为定义
├── knowledge_base/         # FAQ 知识库
│   └── general.md
├── skills/
│   ├── faq/SKILL.md        # FAQ 查询技能
│   └── ticket/SKILL.md     # 工单管理技能
├── mcp_servers/
│   └── ticket_server.py    # 工单 MCP Server
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 决策链路

```
用户提问
    │
    ▼
读 MEMORY.md（用户画像）
    │
    ▼
判断问题类型
    ├── FAQ 类 → faq Skill → read_file knowledge_base/
    │              ├── 命中 → 返回答案
    │              └── 未命中 → 创建工单
    └── 工单类 → ticket Skill → MCP Server → 创建/查询/更新
```

## 快速开始

```bash
# 1. 安装
pip install nanobot-ai
nanobot onboard

# 2. 配置（编辑 ~/.nanobot/config.json）
#   "workspace": "项目路径"
#   "mcpServers": { "ticket_server": { ... } }
#   "providers": { "deepseek": { "apiKey": "...", ... } }

# 3. 启动
cd multi-platform-cs-bot
nanobot
```

## Docker 部署

```bash
cp .env.example .env    # 填入 API key
docker compose up -d
docker exec -it cs-bot nanobot
```

## 功能

- **知识库匹配**：FAQ 精确匹配 + 语义匹配，未命中自动创建工单
- **MCP Server**：独立工单系统，创建/查询/列表/更新四个工具
- **用户记忆**：MEMORY.md 记录偏好语言、问题类型、满意度，跨会话召回
- **多模型**：支持 DeepSeek / OpenAI / Anthropic / 通义千问 / 智谱 / Moonshot / Ollama，一键切换
- **多平台**：预留飞书、钉钉、Telegram Channel 接入

## 技术栈

Python · nanobot-ai · MCP 协议 · SQLite · Docker · LLM API
