#!/usr/bin/env python3
"""
RAG系统测试脚本
测试前端和后端的连接
"""

import requests
import json

def test_backend_api():
    """测试后端API"""
    print("=== 测试后端API ===")
    
    base_url = "http://127.0.0.1:8800"
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ 根路径: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 根路径失败: {e}")
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ 健康检查: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
    
    # 测试文档列表
    try:
        response = requests.get(f"{base_url}/api/documents")
        print(f"✅ 文档列表: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 文档列表失败: {e}")

def test_frontend_proxy():
    """测试前端代理"""
    print("\n=== 测试前端代理 ===")
    
    base_url = "http://localhost:3000"
    
    # 测试前端页面
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ 前端页面: {response.status_code}")
    except Exception as e:
        print(f"❌ 前端页面失败: {e}")
    
    # 测试代理API
    try:
        response = requests.get(f"{base_url}/api/documents")
        print(f"✅ 代理API: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 代理API失败: {e}")

def test_query_api():
    """测试查询API"""
    print("\n=== 测试查询API ===")
    
    base_url = "http://127.0.0.1:8800"
    
    # 测试查询接口
    try:
        query_data = {
            "query": "测试查询"
        }
        response = requests.post(f"{base_url}/api/query", json=query_data)
        print(f"✅ 查询API: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 查询API失败: {e}")

if __name__ == "__main__":
    test_backend_api()
    test_frontend_proxy()
    test_query_api()
    print("\n=== 测试完成 ===")
