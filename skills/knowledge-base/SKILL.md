# Knowledge Base Skill

Manage and retrieve knowledge from your personal database. Supports storing content from various sources (web, Bilibili, WeChat, etc.) and semantic search.

## Usage

### Ingest Knowledge
Save new information to the database with automatic embedding generation.

**Trigger Phrases**:
- "Save this to my knowledge base"
- "Remember this: [content]"
- "Add to knowledge base"
- "Ingest knowledge"

**Parameters**:
- `source_type`: (string, required) Source type (e.g., 'bilibili', 'web', 'manual', 'wechat').
- `source_id`: (string, required) Unique identifier for the source.
- `title`: (string, required) Title of the entry.
- `content`: (string, required) The main body of text.
- `source_url`: (string, optional) URL of the source.
- `summary`: (string, optional) Brief summary.
- `tags`: (string, optional) Comma-separated tags.
- `metadata`: (string, optional) JSON string for additional metadata.

**Execution**:
```bash
python3 scripts/ingest.py --source-type {{source_type}} --source-id {{source_id}} --title "{{title}}" --content "{{content}}" --source-url "{{source_url}}" --summary "{{summary}}" --tags "{{tags}}" --metadata '{{metadata}}'
```

### Search Knowledge
Search for stored information using keyword, vector (semantic), or hybrid search.

**Trigger Phrases**:
- "Search my knowledge for [query]"
- "Find info about [query] in my database"
- "What do I know about [query]?"
- "Retrieve knowledge"

**Parameters**:
- `query`: (string, required) Search query.
- `mode`: (string, optional, default: 'hybrid') Search mode: 'keyword', 'vector', or 'hybrid'.
- `limit`: (number, optional, default: 10) Max number of results.

**Execution**:
```bash
python3 scripts/retrieve.py --query "{{query}}" --mode {{mode}} --limit {{limit}}
```

## Configuration

This skill requires the following environment variables (defined in your `.env` or system environment):

- `DB_HOST`: Database host (default: 127.0.0.1)
- `DB_PORT`: Database port (default: 5432)
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name
- `SILICONFLOW_API_KEY`: API key for SiliconFlow (required for embeddings)
- `EMBEDDING_MODEL`: Embedding model name (default: BAAI/bge-m3)

## Installation

1. Ensure you have a PostgreSQL database with `pgvector` extension installed.
2. Run the SQL initialization script found in `sql/init_knowledge_db.sql`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Set up your environment variables.
