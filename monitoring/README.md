# RAG 系统监控栈

完整的 Prometheus + Grafana + Alertmanager 监控解决方案

## 快速开始

### 1. 启动监控栈

```bash
./start-monitoring.sh
```

或手动启动:

```bash
docker-compose up -d
```

### 2. 访问界面

- **Grafana**: http://localhost:3000
  - 用户名: `admin`
  - 密码: `admin` (首次登录后需修改)

- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 3. 查看 Dashboard

1. 登录 Grafana
2. 进入 Dashboards → RAG System 文件夹
3. 打开 "RAG System Overview"

## 目录结构

```
monitoring/
├── docker-compose.yml           # Docker Compose 配置
├── start-monitoring.sh          # 启动脚本
├── README.md                    # 本文件
├── prometheus/
│   ├── prometheus.yml          # Prometheus 配置
│   └── alerts/
│       └── rag_alerts.yml      # 告警规则
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/        # 数据源自动配置
│   │   └── dashboards/         # Dashboard 自动加载
│   └── dashboards/
│       └── rag-overview.json   # RAG 监控大盘
└── alertmanager/
    └── alertmanager.yml        # Alertmanager 配置
```

## 服务说明

| 服务 | 端口 | 用途 |
|------|------|------|
| Prometheus | 9090 | 指标采集和存储 |
| Grafana | 3000 | 监控大盘可视化 |
| Alertmanager | 9093 | 告警管理 |
| Node Exporter | 9100 | 主机系统指标 |

## 常用命令

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart prometheus
```

### 停止服务

```bash
docker-compose down
```

### 停止并删除数据

```bash
docker-compose down -v
```

## 配置修改

### 修改 Prometheus 配置

1. 编辑 `prometheus/prometheus.yml`
2. 重启 Prometheus:
   ```bash
   docker-compose restart prometheus
   ```

### 修改告警规则

1. 编辑 `prometheus/alerts/rag_alerts.yml`
2. 重新加载配置:
   ```bash
   curl -X POST http://localhost:9090/-/reload
   ```

### 修改 Alertmanager 配置

1. 编辑 `alertmanager/alertmanager.yml`
2. 重启 Alertmanager:
   ```bash
   docker-compose restart alertmanager
   ```

## 告警配置

### 配置 Email 告警

编辑 `alertmanager/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'your-email@gmail.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'

receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@example.com'
```

### 配置 Webhook 告警

```yaml
receivers:
  - name: 'webhook-alerts'
    webhook_configs:
      - url: 'http://your-webhook-url'
        send_resolved: true
```

## 数据持久化

数据存储在 Docker 命名卷中:

- `prometheus-data`: Prometheus 指标数据
- `grafana-data`: Grafana 配置和数据
- `alertmanager-data`: Alertmanager 数据

### 备份数据

```bash
# 备份 Prometheus
docker run --rm -v prometheus-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-backup.tar.gz /data

# 备份 Grafana
docker run --rm -v grafana-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup.tar.gz /data
```

### 恢复数据

```bash
# 恢复 Prometheus
docker run --rm -v prometheus-data:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/prometheus-backup.tar.gz --strip 1"
```

## 故障排查

### Grafana 无法连接 Prometheus

1. 检查服务状态: `docker-compose ps`
2. 测试网络连接:
   ```bash
   docker-compose exec grafana ping prometheus
   ```
3. 查看 Prometheus 日志:
   ```bash
   docker-compose logs prometheus
   ```

### 告警未触发

1. 检查告警规则: 访问 http://localhost:9090/alerts
2. 查看 Alertmanager 状态: http://localhost:9093
3. 查看日志:
   ```bash
   docker-compose logs alertmanager
   ```

### Dashboard 加载慢

1. 减少时间范围 (如从 24h 改为 1h)
2. 简化复杂查询
3. 增加 Prometheus 资源配置

## 更多文档

详细文档请参考:
- [Grafana 监控大盘实现文档](../GRAFANA_MONITORING_IMPLEMENTATION.md)
- [Prometheus 指标采集系统文档](../PROMETHEUS_METRICS_IMPLEMENTATION.md)

## 许可证

MIT
