#!/bin/bash
# 通过Docker执行数据库迁移

echo "开始执行数据库迁移..."

# 将SQL文件复制到容器中
sudo docker cp /home/zhangjh/code/python/rag/backend/migrations_phase1.sql postgresql:/tmp/migrations_phase1.sql

# 在容器中执行SQL
sudo docker exec postgresql psql -U postgres -d ragdb -f /tmp/migrations_phase1.sql

# 清理临时文件
sudo docker exec postgresql rm /tmp/migrations_phase1.sql

echo "迁移执行完成!"
