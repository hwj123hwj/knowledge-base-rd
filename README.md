# 知识管理系统 - 需求与设计文档

> 个人知识管理系统的需求文档和技术设计，供 AI 助手参考和实现。

## 项目背景

用户每天阅读大量信息（微信公众号、B站视频、小红书等），希望将这些内容沉淀为自己的知识库，支持：

1. **统一存储** - 所有来源的内容集中管理
2. **智能检索** - 关键词 + 向量语义搜索
3. **知识关联** - 标签、引用、知识图谱
4. **后续扩展** - RAG 问答、导出到 Obsidian

## 文档目录

- [需求文档](./docs/requirements.md) - 用户场景和功能需求
- [数据库设计](./docs/database-design.md) - PostgreSQL + pgvector 表结构
- [技能设计](./docs/skill-design.md) - knowledge-skill 技能设计

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| 数据库 | PostgreSQL 15 + pgvector |
| 向量维度 | 1536 (OpenAI/SiliconFlow 兼容) |
| Embedding API | SiliconFlow |
| 技能框架 | OpenClaw AgentSkills |

## 当前状态

- [x] 需求整理
- [x] 数据库设计
- [x] 数据库初始化 SQL
- [x] knowledge-skill 开发
- [x] 入库功能（自动生成 embedding）
- [x] 搜索功能（关键词 + 向量 + 混合）
- [ ] URL 一键入库（待完善）
- [ ] RAG 问答

## 更新日志 (2026-03-17)

- **升级 PG 17**: 适配了最新的 PostgreSQL 17 版本。
- **切换 BGE-M3**: 采用 SiliconFlow 的 `BAAI/bge-m3` 模型，向量维度调整为 1024。
- **混合搜索**: 实现了 `keyword` + `vector` 的加权混合检索算法。
- **自动标签**: 入库时支持自动创建标签并建立多对多关联。

## 如何使用本文档

1. 阅读 `docs/requirements.md` 了解用户需求
2. 阅读 `docs/database-design.md` 了解数据结构
3. 阅读 `docs/skill-design.md` 了解技能设计
4. 基于设计实现代码，或提出优化建议

---

创建时间: 2026-03-13
创建者: AI 助手（基于用户需求整理）