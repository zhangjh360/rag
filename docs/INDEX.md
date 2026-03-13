# RAG 项目文档中心

欢迎来到 RAG 知识库项目的文档中心。本文档提供项目的完整技术文档和使用指南。

---

## 📖 文档导航

### 🚀 快速开始
*适合新用户和快速上手*

- [快速入门指南](getting-started/) - 快速了解项目和基本使用方法

### 🏗️ 架构设计
*系统设计、数据库架构和技术选型*

- **[系统设计](architecture/system-design.md)** - 整体系统架构和技术栈
- **[数据库设计](architecture/database-design.md)** - 数据库表结构和关系设计
- **[多领域知识库架构](architecture/multi-domain-knowledge-base.md)** - 多领域知识管理解决方案
- **[图片上传设计](architecture/image-upload-design.md)** - 图片上传功能的设计文档

### 📦 功能文档
*核心功能实现和使用指南*

#### 文档管理
- **[增量索引](features/incremental-indexing.md)** - 智能文档增量更新系统
- **[增量更新指南](features/incremental-update-guide.md)** - 增量更新的详细使用指南

#### 检索与排序
- **[Reranker 实现](features/reranker.md)** - 检索结果重排序功能
- **[路由规则实现](features/routing-rules-implementation.md)** - 智能路由规则系统
- **[路由规则前端](features/routing-rules-frontend.md)** - 路由规则前端界面

#### 用户界面
- **[认证系统实现](features/authentication-implementation.md)** - 用户认证和授权系统
- **[Dashboard 实现](features/dashboard-implementation.md)** - 管理控制台实现
- **[自动标题功能](features/auto-title-feature.md)** - 聊天自动生成标题
- **[动态模型选择](features/dynamic-model-selection.md)** - 动态选择AI模型
- **[动态状态栏](features/dynamic-statusbar.md)** - 状态栏动态更新

#### 多媒体支持
- **[图片上传](features/image-upload.md)** - 聊天中图片上传功能
- **[聊天 RAG 集成](features/chat-rag-integration.md)** - 聊天与检索增强生成集成

### 🔧 运维指南
*部署、配置、监控和优化*

#### 配置与部署
- **[认证指南](operations/authentication-guide.md)** - 认证系统配置和使用
- **[嵌入配置](operations/embedding-config.md)** - 向量嵌入服务配置
- **[日志指南](operations/logging-guide.md)** - 日志系统配置和使用

#### 性能优化
- **[性能优化](operations/performance-optimization.md)** - 系统性能优化最佳实践
- **[查询优化指南](operations/query-optimization-guide.md)** - 数据库查询优化
- **[查询改进](operations/query-improvements.md)** - 查询性能改进方案

#### 监控与诊断
- **[Grafana 监控](operations/monitoring-with-grafana.md)** - Grafana 监控面板配置
- **[Prometheus 指标](operations/prometheus-metrics.md)** - Prometheus 指标采集

### 💻 开发指南
*开发规范、贡献指南和测试*

- [开发指南](development/) - 开发环境搭建和代码规范

### 📂 历史文档
*归档的 Phase 报告和问题修复记录*

- [Phase 报告归档](archive/phase-reports/) - 各阶段开发报告和指南
- [问题修复记录](archive/fixes/) - 历史问题修复文档

---

## 🔍 快速查找

### 按主题分类

**文档增量更新**
- [增量索引](features/incremental-indexing.md)
- [增量更新指南](features/incremental-update-guide.md)

**性能与监控**
- [性能优化](operations/performance-optimization.md)
- [查询优化指南](operations/query-optimization-guide.md)
- [Grafana 监控](operations/monitoring-with-grafana.md)
- [Prometheus 指标](operations/prometheus-metrics.md)

**用户认证与授权**
- [认证系统实现](features/authentication-implementation.md)
- [认证指南](operations/authentication-guide.md)

**检索增强**
- [Reranker 实现](features/reranker.md)
- [路由规则实现](features/routing-rules-implementation.md)
- [多领域知识库架构](architecture/multi-domain-knowledge-base.md)

**用户界面**
- [Dashboard 实现](features/dashboard-implementation.md)
- [动态模型选择](features/dynamic-model-selection.md)
- [图片上传](features/image-upload.md)

### 按开发阶段

- **Phase 1-4**: 查看 [Phase 报告归档](archive/phase-reports/)
- **最新功能**: 查看 [功能文档](features/)
- **问题修复**: 查看 [问题修复记录](archive/fixes/)

---

## 📊 文档统计

- **架构设计**: 4 篇
- **功能文档**: 12 篇
- **运维指南**: 8 篇
- **历史归档**: 20+ 篇

---

## 🤝 贡献指南

如果您想为文档做出贡献，请参阅：
- [开发指南](development/)

---

## 📝 文档更新

**最后更新**: 2025-12-19
**文档版本**: v1.0
**整理状态**: ✅ 已完成全面重组

---

## 📞 获取帮助

- **问题追踪**: 查看 [问题修复记录](archive/fixes/)
- **开发历史**: 查看 [Phase 报告归档](archive/phase-reports/)
- **运维支持**: 查看 [运维指南](operations/)

---

*本文档中心提供项目的完整技术资料，如有疑问请参考对应章节或联系开发团队。*
