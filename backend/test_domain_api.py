#!/usr/bin/env python3
"""
测试知识领域 API 端点
快速验证 API 是否正常工作
"""
import requests
import json

BASE_URL = "http://localhost:8800/api"

# 测试用的认证token (需要先登录获取)
# 如果没有token,需要先调用 /api/login 接口
TOKEN = None

def set_token(token):
    """设置认证token"""
    global TOKEN
    TOKEN = token

def get_headers():
    """获取请求头"""
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    return headers

def test_get_all_domains():
    """测试获取所有领域"""
    print("\n=== 测试: 获取所有领域 ===")
    try:
        response = requests.get(
            f"{BASE_URL}/knowledge-domains",
            headers=get_headers()
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"总数: {data['total']}")
            print("领域列表:")
            for domain in data['domains']:
                print(f"  - {domain['namespace']}: {domain['display_name']}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"异常: {e}")

def test_get_domain_by_namespace(namespace):
    """测试获取单个领域"""
    print(f"\n=== 测试: 获取领域 '{namespace}' ===")
    try:
        response = requests.get(
            f"{BASE_URL}/knowledge-domains/{namespace}",
            headers=get_headers()
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            domain = response.json()
            print(json.dumps(domain, indent=2, ensure_ascii=False))
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"异常: {e}")

def test_get_domain_stats(namespace):
    """测试获取领域统计"""
    print(f"\n=== 测试: 获取领域 '{namespace}' 统计 ===")
    try:
        response = requests.get(
            f"{BASE_URL}/knowledge-domains/{namespace}/stats",
            headers=get_headers()
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"异常: {e}")

def test_create_domain():
    """测试创建新领域"""
    print("\n=== 测试: 创建新领域 ===")
    domain_data = {
        "namespace": "test_domain",
        "display_name": "测试领域",
        "description": "这是一个测试领域",
        "keywords": ["测试", "示例"],
        "icon": "test",
        "color": "#FF5733",
        "is_active": True,
        "priority": 5,
        "permissions": {},
        "metadata": {}
    }

    try:
        response = requests.post(
            f"{BASE_URL}/knowledge-domains",
            headers=get_headers(),
            json=domain_data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 201:
            domain = response.json()
            print("创建成功:")
            print(json.dumps(domain, indent=2, ensure_ascii=False))
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"异常: {e}")

def main():
    """主测试函数"""
    print("开始测试知识领域 API...")
    print(f"API Base URL: {BASE_URL}")

    # 注意: 这些测试需要认证,如果没有token会返回401
    # 可以先运行 test_get_all_domains() 来检查API是否正常响应

    test_get_all_domains()
    test_get_domain_by_namespace("default")
    test_get_domain_by_namespace("technical_docs")
    test_get_domain_stats("default")

    # 创建操作需要管理员权限
    # test_create_domain()

    print("\n=== 测试完成 ===")
    print("注意: 如果看到 401 错误,说明需要认证。请先获取token。")

if __name__ == "__main__":
    main()
