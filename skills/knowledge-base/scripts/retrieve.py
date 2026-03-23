import os
import argparse
import requests
import json
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from typing import List, Dict

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
    """获取查询向量"""
    url = "https://api.siliconflow.cn/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text[:8000]
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    embedding = response.json()["data"][0]["embedding"]

    # Verify vector dimension
    if len(embedding) != VECTOR_DIMENSION:
        print(f"Warning: Expected {VECTOR_DIMENSION} dimensions, but got {len(embedding)}")

    return embedding

def search_knowledge(query: str, mode: str = "hybrid", limit: int = 10) -> List[Dict]:
    """执行混合搜索"""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname=DB_NAME
    )
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. 向量搜索
        if mode in ["vector", "hybrid"]:
            embedding = get_embedding(query)

            # 使用 cosine_ops 进行向量检索 (pgvector)
            cur.execute("""
                SELECT
                    id, source_type, source_url, title, summary,
                    1 - (embedding <=> %s::vector) as similarity,
                    created_at
                FROM knowledge_items
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (embedding, embedding, limit))
            vector_results = cur.fetchall()
            if mode == "vector":
                return vector_results

        # 2. 关键词搜索
        if mode in ["keyword", "hybrid"]:
            cur.execute("""
                SELECT
                    id, source_type, source_url, title, summary,
                    1.0 as similarity,
                    created_at
                FROM knowledge_items
                WHERE title ILIKE %s OR content ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (f"%{query}%", f"%{query}%", limit))
            keyword_results = cur.fetchall()
            if mode == "keyword":
                return keyword_results

        # 3. 混合去重并加权
        all_results = {}
        for r in vector_results:
            all_results[r['id']] = r
            all_results[r['id']]['score'] = r['similarity'] * 0.7  # 向量权重 0.7

        for r in keyword_results:
            if r['id'] in all_results:
                all_results[r['id']]['score'] += 0.3  # 命中了关键词 +0.3
            else:
                all_results[r['id']] = r
                all_results[r['id']]['score'] = 0.5  # 纯关键词加分

        # 按得分排序
        sorted_results = sorted(all_results.values(), key=lambda x: x['score'], reverse=True)
        return sorted_results[:limit]

    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search knowledge")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--mode", default="hybrid", choices=["keyword", "vector", "hybrid"])
    parser.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    results = search_knowledge(args.query, args.mode, args.limit)
    print(json.dumps({"results": [dict(r) for r in results], "total": len(results)}, default=str))
