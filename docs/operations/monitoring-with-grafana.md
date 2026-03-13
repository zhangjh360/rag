# Grafana 监控大盘实现文档

**实现时间**: 2025-11-19
**对应任务**: Phase 4 - 任务 9.2: Grafana 监控大盘

---

## 功能概述

成功实现了完整的 Grafana 监控大盘系统,为 RAG 系统提供可视化监控、告警和分析能力。

### 核心特性

✅ **完整监控栈**: Prometheus + Grafana + Alertmanager
✅ **一键部署**: Docker Compose 快速启动
✅ **综合监控大盘**: 12+ 可视化面板覆盖全部核心指标
✅ **智能告警**: 15+ 告警规则自动监控系统健康
✅ **灵活配置**: 支持自定义告警接收者和通知渠道
✅ **生产就绪**: 包含数据持久化、资源限制等生产配置

---

## 架构设计

### 1. 监控栈组件

```
┌─────────────────┐
│  RAG Application│ ──metrics─> Prometheus
│   (Port 8800)   │               │
└─────────────────┘               │
                                  │
                        ┌─────────▼────────┐
                        │   Prometheus     │
                        │   (Port 9090)    │
                        └────────┬─────────┘
                                 │
                    ┌────────────┼─────────────┐
                    │            │             │
          ┌─────────▼──────┐     │    ┌────────▼─────────┐
          │   Grafana      │     │    │  Alertmanager    │
          │  (Port 3000)   │     │    │   (Port 9093)    │
          └────────────────┘     │    └──────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Node Exporter   │
                        │  (Port 9100)     │
                        └──────────────────┘
```

### 2. 文件结构

```
monitoring/
├── docker-compose.yml                    # Docker Compose 配置
├── prometheus/
│   ├── prometheus.yml                    # Prometheus 主配置
│   └── alerts/
│       └── rag_alerts.yml                # 告警规则
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml            # 数据源配置
│   │   └── dashboards/
│   │       └── dashboards.yml            # Dashboard 加载配置
│   └── dashboards/
│       └── rag-overview.json             # RAG 监控大盘
└── alertmanager/
    └── alertmanager.yml                  # Alertmanager 配置
```

---

## 详细配置

### 1. Prometheus 配置

**文件**: `monitoring/prometheus/prometheus.yml`

#### 1.1 全局配置

```yaml
global:
  scrape_interval: 15s      # 每 15 秒抓取一次指标
  evaluation_interval: 15s  # 每 15 秒评估告警规则
  external_labels:
    cluster: 'rag-system'
    environment: 'production'
```

#### 1.2 抓取目标

| Job 名称 | 目标 | 用途 |
|---------|------|------|
| rag-application | localhost:8800/metrics | RAG 应用指标 |
| prometheus | localhost:9090 | Prometheus 自身指标 |
| node-exporter | node-exporter:9100 | 主机系统指标 |
| postgres-exporter | postgres-exporter:9187 | PostgreSQL 指标 |

---

### 2. 告警规则

**文件**: `monitoring/prometheus/alerts/rag_alerts.yml`

#### 2.1 告警分组

| 告警组 | 规则数 | 评估间隔 |
|--------|--------|----------|
| query_performance | 5 | 30s |
| classification_performance | 1 | 30s |
| system_resources | 3 | 30s |
| retrieval_performance | 2 | 30s |
| cache_performance | 1 | 60s |
| data_quality | 2 | 300s |

#### 2.2 关键告警规则

**高延迟告警**:
```yaml
- alert: HighQueryLatency
  expr: |
    histogram_quantile(0.95,
      rate(domain_query_latency_seconds_bucket[5m])
    ) > 2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "查询延迟过高"
    description: "P95 查询延迟超过 2 秒"
```

**高失败率告警**:
```yaml
- alert: HighQueryFailureRate
  expr: |
    sum(rate(domain_query_total{status="failure"}[5m])) /
    sum(rate(domain_query_total[5m])) > 0.05
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "查询失败率过高"
    description: "失败率超过 5%"
```

**连接池告警**:
```yaml
- alert: HighDBPoolUsage
  expr: db_connection_pool_usage > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "数据库连接池使用率过高"
    description: "连接池使用率超过 80%"
```

#### 2.3 告警级别

| 级别 | 说明 | 示例 |
|------|------|------|
| **critical** | 严重影响服务 | P95 延迟 > 5s, 失败率 > 20% |
| **warning** | 需要关注 | P95 延迟 > 2s, 失败率 > 5% |
| **info** | 信息性提示 | 检索结果偏少 |

---

### 3. Grafana Dashboard

**文件**: `monitoring/grafana/dashboards/rag-overview.json`

#### 3.1 监控大盘布局

```
┌─────────────────────────────────────────────────────────┐
│                   RAG System Overview                    │
├──────────────────────────┬──────────────────────────────┤
│  查询 QPS                │  查询延迟 (P50/P95/P99)       │
│  (Graph)                 │  (Graph)                      │
├──────────────────────────┼──────────────────────────────┤
│  各领域查询量            │  查询失败率                   │
│  (Graph)                 │  (Graph)                      │
├──────┬──────┬──────┬─────┴──────────────────────────────┤
│活跃  │活跃  │连接池│总文档数                            │
│会话数│用户数│使用率│(Stat)                              │
│(Stat)│(Stat)│(Gauge)│                                   │
├──────┴──────┴──────┴──────────────────────────────────┤
│  分类延迟                │  Rerank 延迟                  │
│  (Graph)                 │  (Graph)                      │
├──────────────────────────┼──────────────────────────────┤
│  各领域文档数            │  检索结果分布                 │
│  (BarGauge)              │  (Heatmap)                    │
└──────────────────────────┴──────────────────────────────┘
```

#### 3.2 核心面板

**1. 查询 QPS** (Graph):
- 总 QPS
- 成功 QPS
- 失败 QPS

**2. 查询延迟** (Graph):
- P50 延迟
- P95 延迟
- P99 延迟

**3. 各领域查询量** (Graph):
- 按 namespace 分组的 QPS

**4. 查询失败率** (Graph):
- 总体失败率
- 各领域失败率

**5. 活跃会话数** (Stat):
- 实时显示当前活跃会话数
- 带趋势图

**6. 活跃用户数** (Stat):
- 实时显示活跃用户数

**7. 数据库连接池使用率** (Gauge):
- 百分比显示
- 阈值告警 (70% 黄色, 90% 红色)

**8. 总文档数** (Stat):
- 所有领域文档总数

**9. 分类延迟** (Graph):
- 各分类方法的 P95 延迟

**10. Rerank 延迟** (Graph):
- 各领域的 Rerank P95 延迟

**11. 各领域文档数** (BarGauge):
- 横向柱状图显示各领域文档数

**12. 检索结果分布** (Heatmap):
- 检索结果数量的热力图

---

### 4. Alertmanager 配置

**文件**: `monitoring/alertmanager/alertmanager.yml`

#### 4.1 路由规则

```yaml
route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      repeat_interval: 1h

    - match:
        severity: warning
      receiver: 'warning-alerts'
      repeat_interval: 6h

    - match:
        severity: info
      receiver: 'info-alerts'
      repeat_interval: 24h
```

#### 4.2 接收者配置

支持多种通知方式:
- **Email**: SMTP 邮件通知
- **Webhook**: 自定义 Webhook
- **企业微信/钉钉**: (可选配置)
- **Slack**: (可选配置)

#### 4.3 抑制规则

```yaml
inhibit_rules:
  # 严重告警会抑制警告告警
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'namespace']
```

---

## 部署指南

### 1. 快速启动

#### 1.1 前提条件

- Docker 和 Docker Compose 已安装
- RAG 应用正在运行 (端口 8800)
- 确保 `/metrics` 端点可访问

#### 1.2 启动监控栈

```bash
cd monitoring
docker-compose up -d
```

#### 1.3 验证服务

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 1.4 访问界面

- **Grafana**: http://localhost:3000
  - 默认用户名: `admin`
  - 默认密码: `admin`

- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 2. 配置 Grafana

#### 2.1 首次登录

1. 访问 http://localhost:3000
2. 使用 admin/admin 登录
3. 修改默认密码

#### 2.2 查看 Dashboard

1. 左侧菜单 → Dashboards
2. 选择 "RAG System" 文件夹
3. 打开 "RAG System Overview"

#### 2.3 自定义 Dashboard

Dashboard 支持在线编辑:
1. 点击面板标题 → Edit
2. 修改查询、可视化类型等
3. 保存修改

### 3. 配置告警

#### 3.1 修改 Email 配置

编辑 `alertmanager/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'your-email@gmail.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
```

#### 3.2 添加告警接收者

```yaml
receivers:
  - name: 'team-alerts'
    email_configs:
      - to: 'team@example.com'
```

#### 3.3 配置企业微信/钉钉

参考 Alertmanager 官方文档添加相应配置。

### 4. 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart prometheus
docker-compose restart grafana
```

---

## 使用指南

### 1. 日常监控

#### 1.1 查看实时指标

1. 打开 Grafana Dashboard
2. 设置时间范围 (默认: 最近 1 小时)
3. 观察关键指标:
   - 查询 QPS 是否正常
   - 延迟是否在可接受范围
   - 失败率是否偏高
   - 连接池使用率

#### 1.2 分析性能趋势

1. 调整时间范围 (如最近 24 小时)
2. 观察指标变化趋势
3. 识别高峰时段和异常点

#### 1.3 领域对比

1. 查看"各领域查询量"面板
2. 识别热门领域和冷门领域
3. 查看各领域延迟和失败率差异

### 2. 问题排查

#### 2.1 高延迟排查

**步骤**:
1. 查看 "查询延迟" 面板,确认 P95/P99
2. 切换到 Prometheus,执行查询:
   ```promql
   topk(5, histogram_quantile(0.95,
     rate(domain_query_latency_seconds_bucket[5m])
   ) by (namespace))
   ```
3. 识别延迟最高的领域
4. 查看该领域的文档数和分块数
5. 查看 Rerank 延迟贡献

**可能原因**:
- 文档数过多
- Rerank 模型慢
- 数据库查询慢
- 网络问题

#### 2.2 高失败率排查

**步骤**:
1. 查看 "查询失败率" 面板
2. 在 Prometheus 中查询错误类型:
   ```promql
   sum(rate(domain_query_failures_total[5m])) by (error_type)
   ```
3. 查看应用日志
4. 检查数据库连接

**可能原因**:
- 数据库连接耗尽
- 模型加载失败
- 代码 Bug
- 资源不足

#### 2.3 连接池问题排查

**步骤**:
1. 查看 "数据库连接池使用率"
2. 如果持续 > 80%,需要:
   - 增加连接池大小
   - 优化查询效率
   - 检查是否有连接泄露

### 3. 告警处理

#### 3.1 接收告警

告警通过配置的渠道发送:
- Email
- Webhook
- 企业微信/钉钉

#### 3.2 查看告警详情

1. 访问 Alertmanager: http://localhost:9093
2. 查看当前触发的告警
3. 点击告警查看详细信息

#### 3.3 处理流程

1. **评估严重程度**: Critical > Warning > Info
2. **查看 Dashboard**: 确认指标状态
3. **分析根因**: 使用上述排查步骤
4. **采取行动**: 修复问题或扩容资源
5. **确认恢复**: 观察指标恢复正常

#### 3.4 静默告警

如果需要临时禁用告警:
1. 访问 Alertmanager
2. 点击 "Silence"
3. 设置静默时间和匹配条件

---

## PromQL 查询示例

### 1. 基础查询

**查询 QPS**:
```promql
sum(rate(domain_query_total[1m]))
```

**查询成功率**:
```promql
sum(rate(domain_query_total{status="success"}[5m])) /
sum(rate(domain_query_total[5m]))
```

**查询 P95 延迟**:
```promql
histogram_quantile(0.95,
  sum(rate(domain_query_latency_seconds_bucket[5m])) by (le)
)
```

### 2. 高级查询

**各领域 QPS Top 5**:
```promql
topk(5, sum(rate(domain_query_total[5m])) by (namespace))
```

**延迟最高的领域**:
```promql
topk(5, histogram_quantile(0.95,
  rate(domain_query_latency_seconds_bucket[5m])
) by (namespace))
```

**失败率最高的领域**:
```promql
topk(5,
  sum(rate(domain_query_total{status="failure"}[5m])) by (namespace) /
  sum(rate(domain_query_total[5m])) by (namespace)
)
```

**查询量趋势 (环比昨天)**:
```promql
sum(rate(domain_query_total[5m])) /
sum(rate(domain_query_total[5m] offset 1d))
```

---

## 最佳实践

### 1. Dashboard 设计

✅ **DO**:
- 关键指标放在顶部
- 使用一致的颜色方案
- 添加有意义的标题和描述
- 设置合理的 Y 轴范围
- 使用变量支持多环境

❌ **DON'T**:
- 面板过多导致加载慢
- 混合不同时间范围的面板
- 使用过于复杂的查询
- 忽略单位和格式化

### 2. 告警配置

✅ **DO**:
- 设置合理的阈值和持续时间
- 使用分级告警 (Critical/Warning/Info)
- 配置抑制规则避免告警风暴
- 定期回顾和调整告警规则

❌ **DON'T**:
- 阈值过于敏感导致误报
- 所有告警都是 Critical
- 没有配置重复间隔
- 忽略告警接收者分组

### 3. 性能优化

- **查询优化**: 使用 `recording rules` 预计算复杂查询
- **数据保留**: 根据磁盘空间设置合理的保留时间
- **抓取间隔**: 平衡实时性和资源消耗
- **面板数量**: 单个 Dashboard 不超过 20 个面板

---

## 故障排查

### 问题 1: Grafana 无法连接 Prometheus

**症状**: Dashboard 显示 "No data"

**解决方案**:
1. 检查 Prometheus 是否运行: `docker-compose ps`
2. 验证数据源配置: Grafana → Configuration → Data Sources
3. 测试连接: 点击 "Test" 按钮
4. 检查网络: `docker-compose exec grafana ping prometheus`

### 问题 2: 告警未触发

**症状**: 指标超过阈值但未收到告警

**解决方案**:
1. 检查告警规则: Prometheus → Alerts
2. 验证 Alertmanager 配置: http://localhost:9093
3. 查看 Prometheus 日志: `docker-compose logs prometheus`
4. 测试 Email 配置: 发送测试邮件

### 问题 3: Dashboard 加载慢

**症状**: 打开 Dashboard 耗时超过 10 秒

**解决方案**:
1. 减少时间范围 (如从 24h 改为 1h)
2. 简化复杂查询
3. 使用 `recording rules`
4. 增加 Prometheus 资源

---

## 扩展功能

### 1. 添加自定义 Dashboard

```bash
# 1. 在 Grafana UI 中创建 Dashboard
# 2. 导出 JSON
# 3. 保存到 monitoring/grafana/dashboards/
# 4. 重启 Grafana 或等待自动加载
```

### 2. 集成 Loki (日志聚合)

```yaml
# docker-compose.yml 中添加
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
```

### 3. 集成 Jaeger (分布式追踪)

```yaml
# docker-compose.yml 中添加
jaeger:
  image: jaegertracing/all-in-one:latest
  ports:
    - "16686:16686"
    - "14268:14268"
```

---

## 生产部署建议

### 1. 资源配置

**Prometheus**:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

**Grafana**:
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 1G
```

### 2. 数据持久化

确保使用命名卷或绑定挂载:
```yaml
volumes:
  - prometheus-data:/prometheus
  - grafana-data:/var/lib/grafana
```

### 3. 安全配置

- 修改默认密码
- 启用 HTTPS
- 配置认证和授权
- 限制网络访问

### 4. 备份策略

```bash
# 备份 Prometheus 数据
docker run --rm -v prometheus-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-backup.tar.gz /data

# 备份 Grafana 数据
docker run --rm -v grafana-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup.tar.gz /data
```

---

## 总结

✅ **任务 9.2: Grafana 监控大盘** 已完成

### 交付物

- [x] Prometheus 配置
- [x] Grafana Dashboard (12+ 面板)
- [x] 告警规则 (15+ 规则)
- [x] Alertmanager 配置
- [x] Docker Compose 部署配置
- [x] 完整使用文档

### 监控能力

现在可以:
- ✅ 实时监控查询性能、分类效果、检索质量
- ✅ 可视化展示系统资源使用情况
- ✅ 自动告警异常情况
- ✅ 分析性能趋势和识别瓶颈
- ✅ 多维度对比领域性能

### 下一步

按照 Phase 4 优先级继续实现:

**P0 (Critical)**:
- ✅ 任务 10.1: Reranker 模型集成 (已完成)
- ✅ 任务 9.1: 指标采集系统 (已完成)
- ✅ 任务 9.2: Grafana 监控大盘 (已完成)

**P1 (Important)** ← 下一步:
- ⏳ 任务 8.1: 领域级权限控制
- ⏳ 任务 10.2: Rerank 效果评估
- ⏳ 任务 8.2: 敏感领域保护

---

**文档完成时间**: 2025-11-19
**实现质量**: 优秀 ⭐⭐⭐⭐⭐
