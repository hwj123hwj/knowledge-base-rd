# 数据库设计

## 1. 技术选型

| 组件 | 选型 | 说明 |
|------|------|------|
| 数据库 | PostgreSQL 15 | 成熟稳定，扩展丰富 |
| 向量扩展 | pgvector | 开源，性能好，兼容 SiliconFlow embedding |
| Embedding | vector(1024) | SiliconFlow BGE-M3 维度 |

## 2. 连接信息

```
Host: 127.0.0.1
Port: 5433
User: bili
Password: bili123456
Database: bilibili
```

## 3. 表结构

### 3.1 knowledge_items（知识条目表）

统一存储所有来源的知识内容。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键，自动生成 |
| source_type | VARCHAR(50) | 来源类型 |
| source_id | VARCHAR(255) | 原始平台ID |
| source_url | TEXT | 原始链接 |
| title | VARCHAR(500) | 标题 |
| content | TEXT | 全文内容 |
| summary | TEXT | AI 摘要 |
| embedding | vector(1024) | 向量（SiliconFlow BGE-M3）|
| metadata | JSONB | 平台特有字段 |
| created_at | TIMESTAMPTZ | 入库时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**source_type 枚举值：**
- `bilibili` - B站视频
- `wechat` - 微信公众号
- `xiaohongshu` - 小红书
- `web` - 通用网页
- `manual` - 手动录入

**metadata 示例：**
```json
// B站视频
{
  "author": "UP主名",
  "duration": 3600,
  "bvid": "BV1xxx",
  "view_count": 10000
}

// 微信文章
{
  "author": "作者名",
  "account": "公众号名",
  "publish_date": "2026-03-13"
}
```

### 3.2 tags（标签表）

独立管理标签，支持分类。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(100) | 标签名（唯一） |
| category | VARCHAR(50) | 分类 |
| created_at | TIMESTAMPTZ | 创建时间 |

**category 枚举值：**
- `topic` - 主题标签（AI、编程、设计）
- `person` - 人物标签（作者、UP主）
- `project` - 项目标签（个人项目关联）
- `source` - 来源标签（自动生成）

### 3.3 knowledge_tags（关联表）

知识条目与标签的多对多关系。

| 字段 | 类型 | 说明 |
|------|------|------|
| knowledge_id | UUID | 外键 → knowledge_items.id |
| tag_id | INTEGER | 外键 → tags.id |

**主键：** (knowledge_id, tag_id)

---

## 4. 索引设计

```sql
-- 唯一索引：防止重复入库
CREATE UNIQUE INDEX idx_knowledge_items_unique_source
ON knowledge_items(source_type, source_id);

-- 向量索引：语义搜索
CREATE INDEX idx_knowledge_items_embedding
ON knowledge_items USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 时间索引：按时间排序
CREATE INDEX idx_knowledge_items_created_at
ON knowledge_items(created_at DESC);

-- 标签索引
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_category ON tags(category);
```

---

## 5. 查询示例

### 5.1 向量搜索（语义相似）

```sql
-- 搜索与查询向量最相似的 10 条内容
SELECT id, title, summary,
       1 - (embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM knowledge_items
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

### 5.2 关键词搜索

```sql
-- 全文搜索标题和内容
SELECT id, title, source_type
FROM knowledge_items
WHERE title ILIKE '%AI%' OR content ILIKE '%AI%'
ORDER BY created_at DESC
LIMIT 20;
```

### 5.3 按来源统计

```sql
SELECT source_type, COUNT(*) as count
FROM knowledge_items
GROUP BY source_type
ORDER BY count DESC;
```

### 5.4 按标签查询

```sql
-- 查询带有 "AI" 标签的所有内容
SELECT k.id, k.title, k.source_type
FROM knowledge_items k
JOIN knowledge_tags kt ON k.id = kt.knowledge_id
JOIN tags t ON kt.tag_id = t.id
WHERE t.name = 'AI';
```

---

## 6. 初始化脚本

完整 SQL 文件：`../sql/init_knowledge_db.sql`

执行方式：
```bash
PGPASSWORD=bili123456 psql -h 127.0.0.1 -p 5433 -U bili -d bilibili -f sql/init_knowledge_db.sql
```

---

## 7. 注意事项

1. **向量索引** - 数据量小时 ivfflat 索引可能效率不高，建议数据量 > 1000 后再创建
2. **metadata 灵活性** - JSONB 字段可以存储任意平台特有信息，但查询时需要使用 JSON 操作符
3. **唯一约束** - 通过 (source_type, source_id) 确保同一内容不会重复入库