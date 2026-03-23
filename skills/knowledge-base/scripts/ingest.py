import os
import sys
import argparse
import requests
import json
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from typing import Optional, List

# 加载环境变量
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "bili")
DB_PASSWORD = os.getenv("DB_PASSWORD", "bili123456")
DB_NAME = os.getenv("DB_NAME", "bilibili")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
VECTOR_DIMENSION = 1024  # Explicitly set vector dimension for SiliconFlow BGE-M3

def get_embedding(text: str) -> List[float]:
    """调用 SiliconFlow API 获取 Embedding"""
    if not SILICONFLOW_API_KEY:
        raise ValueError("SILICONFLOW_API_KEY not found in environment variables")

    url = "https://api.siliconflow.cn/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text[:8000]  # 适当截断
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    embedding = data["data"][0]["embedding"]

    # Verify vector dimension
    if len(embedding) != VECTOR_DIMENSION:
        print(f"Warning: Expected {VECTOR_DIMENSION} dimensions, but got {len(embedding)}")

    return embedding

def save_knowledge(data: dict):
    """保存知识到 PostgreSQL"""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname=DB_NAME
    )
    try:
        cur = conn.cursor()

        # 1. 插入或更新知识条目
        cur.execute("""
            INSERT INTO knowledge_items
            (source_type, source_id, source_url, title, content, summary, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_type, source_id) DO UPDATE
            SET title = EXCLUDED.title,
                content = EXCLUDED.content,
                summary = EXCLUDED.summary,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata,
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

        knowledge_id = cur.fetchone()[0]

        # 2. 处理标签 (可选)
        tags = data.get("tags", [])
        for tag_name in tags:
            # 获取或创建标签
            cur.execute("""
                INSERT INTO tags (name, category)
                VALUES (%s, 'topic')
                ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category
                RETURNING id
            """, (tag_name,))
            tag_id = cur.fetchone()[0]

            # 建立关联
            cur.execute("""
                INSERT INTO knowledge_tags (knowledge_id, tag_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (knowledge_id, tag_id))

        conn.commit()
        return knowledge_id
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save knowledge to database")
    parser.add_argument("--source-type", required=True, help="bilibili/wechat/xiaohongshu/web/manual")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-url", help="URL of the source")
    parser.add_argument("--title", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument("--summary", help="AI summary of the content")
    parser.add_argument("--tags", help="Comma separated tags")
    parser.add_argument("--metadata", help="JSON string of metadata")

    args = parser.parse_args()

    # 提取 Embedding：优先用 summary（更浓缩），fallback 到 content 前 2000 字
    print(f"Generating embedding for: {args.title}...", file=sys.stderr)
    embed_text = args.summary if args.summary else args.content[:2000]
    embedding = get_embedding(f"{args.title}\n{embed_text}")

    # 解析数据
    data = {
        "source_type": args.source_type,
        "source_id": args.source_id,
        "source_url": args.source_url,
        "title": args.title,
        "content": args.content,
        "summary": args.summary,
        "embedding": embedding,
        "metadata": json.loads(args.metadata) if args.metadata else {},
        "tags": [t.strip() for t in args.tags.split(",")] if args.tags else []
    }

    # 保存
    knowledge_id = save_knowledge(data)
    print(json.dumps({"success": True, "id": knowledge_id, "message": "Knowledge saved successfully"}))
