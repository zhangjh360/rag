# RAG系统文档中心

本目录包含RAG系统的所有技术文档。

---

## 📂 文档分类

### 🗂️ 文档管理
**目录**: [document/](./document/)

文档增量更新功能的完整文档:
- [增量更新使用指南](./document/INCREMENTAL_UPDATE_GUIDE.md) - API接口、使用场景、数据库设计
- [Phase 1 测试报告](./document/PHASE1_TEST_REPORT.md) - 功能测试、性能预估、验收标准
- [文档管理README](./document/README.md) - 功能概述、快速开始、开发路线图

### 🔧 系统配置

- [EMBEDDING_CONFIG.md](./EMBEDDING_CONFIG.md) - 嵌入服务配置
- [EMBEDDING_FIX_GUIDE.md](./EMBEDDING_FIX_GUIDE.md) - 嵌入问题修复指南
- [LOGGING_GUIDE.md](./LOGGING_GUIDE.md) - 日志配置指南

### 🚀 性能优化

- [QUERY_OPTIMIZATION_GUIDE.md](./QUERY_OPTIMIZATION_GUIDE.md) - 查询优化指南
- [QUERY_IMPROVEMENTS.md](./QUERY_IMPROVEMENTS.md) - 查询改进方案
- [GENERATION_FIX_SUMMARY.md](./GENERATION_FIX_SUMMARY.md) - 生成问题修复总结

---

## 🎯 快速导航

### 新手入门
1. 📖 先阅读系统配置文档了解基础架构
2. 🔧 根据LOGGING_GUIDE配置日志系统
3. 🚀 参考QUERY_OPTIMIZATION_GUIDE优化查询性能

### 文档管理功能
1. 📚 阅读 [document/README.md](./document/README.md) 了解功能概述
2. 🛠️ 参考 [INCREMENTAL_UPDATE_GUIDE.md](./document/INCREMENTAL_UPDATE_GUIDE.md) 进行API调用
3. ✅ 查看 [PHASE1_TEST_REPORT.md](./document/PHASE1_TEST_REPORT.md) 了解测试情况

### 问题排查
1. 🔍 查询相关问题 → QUERY_OPTIMIZATION_GUIDE.md
2. 📊 嵌入相关问题 → EMBEDDING_FIX_GUIDE.md
3. 💬 生成相关问题 → GENERATION_FIX_SUMMARY.md
4. 📝 日志相关问题 → LOGGING_GUIDE.md

---

## 📊 文档状态

| 文档 | 状态 | 最后更新 |
|------|------|----------|
| document/* | ✅ 最新 | 2025-01-22 |
| EMBEDDING_CONFIG.md | ✅ 稳定 | - |
| EMBEDDING_FIX_GUIDE.md | ✅ 稳定 | - |
| LOGGING_GUIDE.md | ✅ 稳定 | - |
| QUERY_OPTIMIZATION_GUIDE.md | ✅ 稳定 | - |
| QUERY_IMPROVEMENTS.md | ✅ 稳定 | - |
| GENERATION_FIX_SUMMARY.md | ✅ 稳定 | - |

---

## 🔗 相关资源

### API文档
- **Swagger UI**: http://localhost:8800/docs
- **ReDoc**: http://localhost:8800/redoc

### 系统组件
- **后端服务**: FastAPI + PostgreSQL + pgvector
- **嵌入服务**: OpenAI / 自定义embedding模型
- **向量数据库**: pgvector
- **监控**: Prometheus + Grafana

---

## 📞 文档维护

如需更新文档或报告问题:
1. 确保文档格式统一(Markdown)
2. 遵循现有文档结构
3. 添加必要的代码示例
4. 更新本README的文档索引

---

**最后更新**: 2025-01-22
**维护者**: Development Team
