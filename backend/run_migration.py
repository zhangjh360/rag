#!/usr/bin/env python3
"""
简单的迁移脚本执行器
直接读取并执行SQL文件
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config.settings import DB_URL

def run_sql_file(sql_file_path):
    """执行SQL文件"""
    print(f"开始执行SQL文件: {sql_file_path}")

    # 读取SQL文件
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 创建数据库连接
    engine = create_engine(DB_URL)

    # 执行SQL
    with engine.begin() as conn:
        # 按分号分割SQL语句
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

        for i, statement in enumerate(statements, 1):
            # 跳过注释行
            if statement.startswith('--'):
                continue

            try:
                print(f"\n执行语句 {i}/{len(statements)}...")
                result = conn.execute(text(statement))

                # 如果有返回结果,打印出来
                try:
                    rows = result.fetchall()
                    if rows:
                        for row in rows:
                            print(f"  {dict(row._mapping)}")
                except:
                    pass

                print(f"  ✓ 成功")

            except Exception as e:
                error_msg = str(e)
                # 忽略"已存在"类型的错误
                if 'already exists' in error_msg or '已存在' in error_msg:
                    print(f"  - 跳过 (已存在)")
                else:
                    print(f"  ✗ 错误: {e}")
                    # 继续执行下一条

    print("\n✅ SQL迁移执行完成!")

if __name__ == "__main__":
    sql_file = "backend/migrations_phase1.sql"
    if len(sys.argv) > 1:
        sql_file = sys.argv[1]

    run_sql_file(sql_file)
