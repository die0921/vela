# Digital Persona

一个运行在本地的数字副本 Agent，基于你真实的记忆、价值观和情绪系统构建。支持在 **Claude Code** 和 **OpenClaw** 中使用。

## 功能特性

- **记忆系统**：通过问卷建立向量化记忆，对话时自动召回相关记忆（ChromaDB）
- **情绪引擎**：三维情绪状态（即时情绪 / 悲伤 / 愤怒），随对话和时间自然变化
- **价值观守卫**：双层守卫机制（关键词匹配 + AI 语义检测），拒绝违背价值观的请求
- **自动维护**：每小时情绪衰减、每天记忆去重、每周灵魂一致性检查
- **互动系统**：支持送礼、道歉、分享好消息等情感互动动作
- **OpenClaw 插件**：可通过 WhatsApp / Telegram / Discord 等渠道与副本聊天

## 快速开始

### 前置条件

- Python 3.11+
- [Claude Code](https://claude.ai/code)（提供 Anthropic 认证，无需手动填写 API Key）

### 安装

```bash
git clone https://github.com/die0921/digital-persona.git
cd digital-persona
pip install -r requirements.txt
```

> 首次运行时 `sentence-transformers` 会自动下载 `all-MiniLM-L6-v2` 模型（约 90MB）。

### 初始化副本

```bash
python scripts/init_persona.py
```

流程：同意授权 → 输入姓名 → 完成问卷（建立记忆、价值观、情绪基线）

### 在 Claude Code 中使用

将项目目录设为工作目录，`agent.md` 定义了完整的对话流程：

```
用户消息 → 价值观守卫 → 召回记忆 → 生成回复 → 更新情绪
```

### 手动维护

```bash
python scripts/maintenance.py <persona_id>
```

### 互动动作

```bash
python scripts/interactions.py <persona_id> send_gift
python scripts/interactions.py <persona_id> apologize
python scripts/interactions.py <persona_id> share_good_news
python scripts/interactions.py <persona_id> share_memory
python scripts/interactions.py <persona_id> do_together
```

## 目录结构

```
digital-persona/
├── agent.md                  # Claude Code agent 定义
├── scripts/
│   ├── init_persona.py       # 初始化流程（同意 + 问卷 + 建库）
│   ├── respond.py            # 三层响应管道
│   ├── emotion_engine.py     # 情绪计算引擎
│   ├── memory_manager.py     # ChromaDB 向量记忆管理
│   ├── values_guard.py       # 价值观守卫（Layer 1）
│   ├── maintenance.py        # 定时维护任务
│   ├── interactions.py       # 互动动作
│   ├── questionnaire.py      # 初始化问卷
│   ├── ai_client.py          # AI 调用（Anthropic SDK + 本地 embedding）
│   └── db.py                 # SQLite 数据库操作
├── skills/
│   ├── respond.md            # 回复技能说明
│   ├── recall-memory.md      # 记忆召回技能
│   ├── update-emotion.md     # 情绪更新技能
│   ├── values-guard.md       # 价值观守卫技能
│   └── maintenance.md        # 维护技能
├── openclaw-plugin/          # OpenClaw 插件
│   ├── index.ts              # 插件入口（注册 persona_chat / persona_status 工具）
│   ├── openclaw.plugin.json  # 插件清单
│   └── AGENTS.md             # OpenClaw agent 指令
├── tests/                    # 测试套件
├── data/                     # 本地数据（SQLite + ChromaDB，不上传）
└── requirements.txt
```

## OpenClaw 集成

支持通过 [OpenClaw](https://openclaw.ai) 以 WhatsApp / Telegram / Discord 等渠道与副本聊天。

### 安装插件

```bash
# 安装 OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash
openclaw onboard

# 安装本地插件
openclaw plugins install ./openclaw-plugin
```

### 插件配置

在 OpenClaw 设置中配置 `digital-persona` 插件：

```json
{
  "personaId": 1,
  "projectPath": "/path/to/digital-persona",
  "pythonPath": "python"
}
```

### 可用工具

| 工具 | 说明 |
|------|------|
| `persona_chat` | 发送消息，经完整副本流程生成回复 |
| `persona_status` | 查看副本当前情绪状态和记忆数量 |

## 技术架构

```
用户消息
  ↓
Layer 1: 关键词 + 向量相似度守卫（ValuesGuard）
  ↓
Layer 2: AI 语义价值观检测（guard_check）
  ↓
Layer 3: 情绪感知 System Prompt + 记忆注入 → Claude 生成回复
  ↓
情绪状态更新（EmotionEngine）
```

### 数据存储

| 存储 | 用途 |
|------|------|
| SQLite (`data/persona.db`) | 副本信息、情绪状态、对话历史、维护日志 |
| ChromaDB (`data/chroma/`) | 向量化记忆，用于语义召回 |

### AI 依赖

| 功能 | 方案 |
|------|------|
| 对话生成 / 守卫检测 | Anthropic Claude（`claude-haiku-4-5-20251001`） |
| 向量 Embedding | `sentence-transformers` 本地模型（`all-MiniLM-L6-v2`） |

> **无需手动配置 API Key**：在 Claude Code 环境中运行时，`ANTHROPIC_API_KEY` 由 Claude Code 自动注入。

## 定时任务

初始化完成后会打印 3 个 cron 任务定义，在 Claude Code 中通过 `CronCreate` 注册：

| 任务 | 频率 | 内容 |
|------|------|------|
| `emotion_decay` | 每小时 | 情绪向基线衰减 |
| `memory_consolidation` | 每天 3:00 | 记忆去重整合 |
| `soul_consistency_check` | 每周日 4:00 | 检查近期回答与价值观的一致性 |

## 隐私说明

所有数据（记忆、价值观、情绪、对话记录）均保存在本地 `data/` 目录，不会上传到任何服务器。`data/` 已加入 `.gitignore`。

## License

MIT
