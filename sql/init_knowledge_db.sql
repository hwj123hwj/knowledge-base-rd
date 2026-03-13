-- ============================================
-- 知识管理数据库初始化脚本
-- 数据库: bilibili (PostgreSQL + pgvector)
-- 创建时间: 2026-03-13
-- ============================================

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 1. 知识条目表 (knowledge_items)
-- 统一存储所有来源的知识内容
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL,          -- 来源类型: bilibili/wechat/xiaohongshu/web/manual
    source_id VARCHAR(255),                     -- 原始平台ID
    source_url TEXT,                            -- 原始链接
    title VARCHAR(500),                         -- 标题
    content TEXT,                               -- 全文内容
    summary TEXT,                               -- AI 摘要
    embedding vector(1536),                     -- OpenAI embedding 向量 (1536维)
    metadata JSONB DEFAULT '{}',                -- 平台特有字段，灵活扩展
    created_at TIMESTAMPTZ DEFAULT NOW(),       -- 入库时间
    updated_at TIMESTAMPTZ DEFAULT NOW()        -- 更新时间
);

-- 注释
COMMENT ON TABLE knowledge_items IS '知识条目表 - 统一存储所有来源的知识内容';
COMMENT ON COLUMN knowledge_items.source_type IS '来源类型: bilibili/wechat/xiaohongshu/web/manual';
COMMENT ON COLUMN knowledge_items.source_id IS '原始平台ID，如 B站BV号、微信文章ID等';
COMMENT ON COLUMN knowledge_items.metadata IS '平台特有字段，JSON格式，灵活扩展';

-- 索引
CREATE INDEX IF NOT EXISTS idx_knowledge_items_source ON knowledge_items(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_created_at ON knowledge_items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_embedding ON knowledge_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 唯一约束：同一来源的同一内容只存一次
CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_items_unique_source ON knowledge_items(source_type, source_id);

-- ============================================
-- 2. 标签表 (tags)
-- 独立管理标签，支持分类
-- ============================================
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,          -- 标签名
    category VARCHAR(50),                       -- 分类: topic/person/project/source
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 注释
COMMENT ON TABLE tags IS '标签表 - 独立管理标签，支持分类';
COMMENT ON COLUMN tags.category IS '标签分类: topic(主题)/person(人物)/project(项目)/source(来源)';

-- 索引
CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- ============================================
-- 3. 知识-标签关联表 (knowledge_tags)
-- 多对多关系
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_tags (
    knowledge_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (knowledge_id, tag_id)
);

-- 注释
COMMENT ON TABLE knowledge_tags IS '知识-标签关联表 - 多对多关系';

-- ============================================
-- 4. 自动更新 updated_at 触发器
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_knowledge_items_updated_at
    BEFORE UPDATE ON knowledge_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 5. 常用查询视图（可选）
-- ============================================

-- 按来源统计
CREATE OR REPLACE VIEW v_source_stats AS
SELECT 
    source_type,
    COUNT(*) as total_count,
    COUNT(embedding) as embedded_count,
    MAX(created_at) as latest_added
FROM knowledge_items
GROUP BY source_type
ORDER BY total_count DESC;

-- ============================================
-- 完成
-- ============================================
-- 执行完成后可以运行以下命令验证:
-- \dt           -- 查看所有表
-- \di           -- 查看所有索引
-- SELECT * FROM v_source_stats;  -- 查看来源统计