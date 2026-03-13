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
- [ ] knowledge-skill 开发
- [ ] 检索功能
- [ ] RAG 问答

## 如何使用本文档

1. 阅读 `docs/requirements.md` 了解用户需求
2. 阅读 `docs/database-design.md` 了解数据结构
3. 阅读 `docs/skill-design.md` 了解技能设计
4. 基于设计实现代码，或提出优化建议

---

创建时间: 2026-03-13
创建者: AI 助手（基于用户需求整理）