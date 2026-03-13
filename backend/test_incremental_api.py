#!/usr/bin/env python3
"""
测试增量更新API接口
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8800/api/index"

# 测试token (需要先登录获取)
# 这里使用admin用户的token,实际使用时需要先调用登录接口获取
TOKEN = None

def get_headers():
    """获取请求头"""
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    return headers

def test_detect_changes():
    """测试变更检测接口"""
    print("\n" + "="*60)
    print("测试1: 检测文档变更")
    print("="*60)

    url = f"{BASE_URL}/detect-changes"
    payload = {
        "namespace": "default",
        "since_hours": 24
    }

    try:
        response = requests.post(url, json=payload, headers=get_headers())
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ 响应成功:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"✗ 请求失败:")
            print(response.text)
    except Exception as e:
        print(f"✗ 异常: {e}")

def test_index_status():
    """测试获取索引状态"""
    print("\n" + "="*60)
    print("测试2: 获取索引状态")
    print("="*60)

    url = f"{BASE_URL}/status"
    params = {"namespace": "default"}

    try:
        response = requests.get(url, params=params, headers=get_headers())
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ 响应成功:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"✗ 请求失败:")
            print(response.text)
    except Exception as e:
        print(f"✗ 异常: {e}")

def test_auto_update():
    """测试自动更新接口"""
    print("\n" + "="*60)
    print("测试3: 自动更新")
    print("="*60)

    url = f"{BASE_URL}/auto-update"
    params = {"namespace": "default"}

    try:
        response = requests.post(url, params=params, headers=get_headers())
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ 响应成功:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"✗ 请求失败:")
            print(response.text)
    except Exception as e:
        print(f"✗ 异常: {e}")

def test_database_tables():
    """测试数据库表是否存在"""
    print("\n" + "="*60)
    print("测试0: 验证数据库表结构")
    print("="*60)

    from app.database.connection import get_engine
    from sqlalchemy import text

    engine = get_engine()

    tables_to_check = [
        'document_index_records',
        'index_tasks',
        'index_change_history',
        'index_statistics',
        'documents'
    ]

    with engine.connect() as conn:
        for table in tables_to_check:
            result = conn.execute(text(f"""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_name = '{table}'
            """))
            count = result.fetchone()[0]

            if count > 0:
                print(f"  ✓ 表 {table} 存在")

                # 检查documents表的新字段
                if table == 'documents':
                    result = conn.execute(text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'documents'
                        AND column_name IN ('content_hash', 'last_indexed_at', 'index_status', 'file_modified_at', 'file_size')
                        ORDER BY column_name
                    """))
                    columns = [row[0] for row in result.fetchall()]
                    print(f"    新增字段: {', '.join(columns)}")
            else:
                print(f"  ✗ 表 {table} 不存在")

if __name__ == "__main__":
    print("增量更新API接口测试")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"目标服务: {BASE_URL}")

    # 测试数据库表
    test_database_tables()

    # 测试API接口
    test_index_status()
    test_detect_changes()
    # test_auto_update()  # 暂时不测试自动更新,避免触发实际索引操作

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
