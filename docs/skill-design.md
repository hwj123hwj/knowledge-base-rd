# 技能设计 - knowledge-skill

## 1. 设计理念

**核心原则：解耦**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  数据获取技能    │     │  knowledge-skill │     │    检索/问答     │
│                 │     │                 │     │                 │
│ bilibili-toolkit│     │  - 接收内容      │     │  - 关键词搜索    │
│ agent-reach     │ ──► │  - 生成摘要      │ ──► │  - 向量搜索      │
│ xiaohongshu     │     │  - 生成向量      │     │  - RAG 问答      │
│                 │     │  - 入库          │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
      已有技能              本次开发               后续扩展
```

**好处：**
- 数据获取技能不需要关心数据库
- knowledge-skill 可以被任何技能调用
- 检索功能独立，可单独优化

---

## 2. 功能模块

### 2.1 入库模块 (knowledge_save.py)

**输入参数：**
```python
{
    "source_type": "bilibili",      # 必填：来源类型
    "source_id": "BV1xxx",          # 必填：原始ID
    "source_url": "https://...",    # 可选：原始链接
    "title": "AI Agent 开发实战",   # 必填：标题
    "content": "视频文稿全文...",   # 必填：内容
    "metadata": {                   # 可选：平台特有字段
        "author": "UP主名",
        "duration": 3600
    }
}
```

**处理流程：**
1. 检查是否已存在（source_type + source_id）
2. 内容过长（> 4000 字）时，调用 AI 生成摘要
3. 调用 SiliconFlow API 生成 Embedding
4. 写入 knowledge_items 表
5. 返回入库结果

**返回结果：**
```python
{
    "success": true,
    "id": "uuid-xxx",
    "message": "入库成功",
    "summary": "AI 生成的摘要..."
}
```

### 2.2 URL 入库模块 (knowledge_save_from_url.py)

**输入参数：**
```python
{
    "url": "https://www.bilibili.com/video/BV1xxx"
}
```

**处理流程：**
1. 识别 URL 类型（B站/微信/小红书/通用网页）
2. 调用对应技能获取内容
3. 调用 knowledge_save.py 入库
4. 返回入库结果

**URL 类型识别：**
| URL 模式 | 调用技能 |
|----------|----------|
| `bilibili.com/video/` | bilibili-toolkit |
| `mp.weixin.qq.com/` | agent-reach (wechat) |
| `xiaohongshu.com/` | xiaohongshu-skills |
| 其他 | agent-reach (web) |

### 2.3 搜索模块 (knowledge_search.py)

**输入参数：**
```python
{
    "query": "AI Agent 开发",       # 搜索关键词或问题
    "mode": "hybrid",               # keyword/vector/hybrid
    "limit": 10,                    # 返回数量
    "source_type": null,            # 可选：筛选来源
    "tags": []                      # 可选：筛选标签
}
```

**搜索模式：**
| 模式 | 说明 |
|------|------|
| `keyword` | 关键词匹配（标题+内容） |
| `vector` | 向量语义相似度 |
| `hybrid` | 关键词 + 向量结合 |

**返回结果：**
```python
{
    "results": [
        {
            "id": "uuid-xxx",
            "title": "AI Agent 开发实战",
            "summary": "摘要...",
            "source_type": "bilibili",
            "source_url": "https://...",
            "similarity": 0.85,
            "created_at": "2026-03-13T13:00:00Z"
        }
    ],
    "total": 5,
    "query": "AI Agent 开发"
}
```

---

## 3. 文件结构

```
~/.agents/skills/knowledge-skill/
├── SKILL.md                       # 技能说明文档
├── scripts/
│   ├── knowledge_save.py          # 核心入库脚本
│   ├── knowledge_save_from_url.py # URL 一键入库
│   └── knowledge_search.py        # 搜索脚本
├── references/
│   └── db_schema.md               # 数据库结构参考
├── .env                           # 配置文件
└── requirements.txt               # Python 依赖
```

---

## 4. 依赖与配置

### 4.1 Python 依赖
```
psycopg2-binary>=2.9.0
requests>=2.28.0
python-dotenv>=1.0.0
```

### 4.2 环境变量 (.env)
```env
# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=5433
DB_USER=bili
DB_PASSWORD=bili123456
DB_NAME=bilibili

# Embedding API (SiliconFlow)
SILICONFLOW_API_KEY=sk-pjgenkdeoudivpnruwhnkysilysvgpurseenmmrvqgntxela
EMBEDDING_MODEL=text-embedding-ada-002  # 或 SiliconFlow 兼容模型
```

---

## 5. API 调用

### 5.1 SiliconFlow Embedding API

```python
import requests

def get_embedding(text: str) -> list[float]:
    response = requests.post(
        "https://api.siliconflow.cn/v1/embeddings",
        headers={
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "text-embedding-ada-002",
            "input": text[:8000]  # 截断超长文本
        }
    )
    return response.json()["data"][0]["embedding"]
```

### 5.2 数据库操作

```python
import psycopg2

def save_knowledge(data: dict):
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname=DB_NAME
    )
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO knowledge_items 
        (source_type, source_id, source_url, title, content, summary, embedding, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_type, source_id) DO UPDATE
        SET title = EXCLUDED.title,
            content = EXCLUDED.content,
            summary = EXCLUDED.summary,
            updated_at = NOW()
        RETURNING id
    """, (
        data["source_type"],
        data["source_id"],
        data.get("source_url"),
        data["title"],
        data["content"],
        data.get("summary"),
        data.get("embedding"),
        psycopg2.extras.Json(data.get("metadata", {}))
    ))
    
    conn.commit()
    return cur.fetchone()[0]
```

---

## 6. AI 调用方式

AI 助手通过命令行调用脚本：

```bash
# 入库
uv run ~/.agents/skills/knowledge-skill/scripts/knowledge_save.py \
  --source-type bilibili \
  --source-id BV1xxx \
  --title "AI Agent 开发实战" \
  --content "文稿全文..." \
  --metadata '{"author": "UP主名"}'

# URL 一键入库
uv run ~/.agents/skills/knowledge-skill/scripts/knowledge_save_from_url.py \
  --url "https://www.bilibili.com/video/BV1xxx"

# 搜索
uv run ~/.agents/skills/knowledge-skill/scripts/knowledge_search.py \
  --query "AI Agent" \
  --mode hybrid \
  --limit 10
```

---

## 7. 后续扩展

### 7.1 Phase 2：RAG 问答
- 基于检索结果的智能问答
- 引用来源追踪

### 7.2 Phase 2：知识图谱
- 自动发现内容关联
- 可视化展示

### 7.3 Phase 3：Obsidian 集成
- 导出为 Markdown
- 同步到 Obsidian vault