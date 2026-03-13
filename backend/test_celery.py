#!/usr/bin/env python3
"""
测试Celery配置和连接
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.celery_app import celery_app, test_task
from app.config.celery_config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_celery_connection():
    """测试Celery连接"""
    print("="*60)
    print("测试Celery配置")
    print("="*60)

    print(f"\n配置信息:")
    print(f"  Broker URL: {CELERY_BROKER_URL}")
    print(f"  Result Backend: {CELERY_RESULT_BACKEND}")

    # 测试1: 检查Celery实例
    print(f"\n✓ Celery实例已创建: {celery_app}")

    # 测试2: 检查任务注册
    print(f"\n注册的任务:")
    for task_name in sorted(celery_app.tasks.keys()):
        if not task_name.startswith('celery.'):
            print(f"  - {task_name}")

    # 测试3: 尝试连接Redis
    print(f"\n测试Redis连接...")
    try:
        from redis import Redis
        from app.config.settings import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

        if REDIS_PASSWORD:
            redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        else:
            redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

        redis_client.ping()
        print(f"  ✓ Redis连接成功!")

        # 测试队列状态
        queue_info = redis_client.info('server')
        print(f"  Redis版本: {queue_info.get('redis_version', 'N/A')}")

    except Exception as e:
        print(f"  ✗ Redis连接失败: {e}")
        print(f"  请确保Redis服务正在运行,并检查密码配置")
        return False

    # 测试4: 提交测试任务
    print(f"\n提交测试任务...")
    try:
        # 同步测试任务 (不需要Worker)
        result = test_task.delay(2, 3)
        print(f"  ✓ 任务已提交: task_id={result.id}")
        print(f"  任务状态: {result.state}")

        print(f"\n注意: 要执行任务,需要启动Celery Worker:")
        print(f"  ./start_celery_worker.sh")

    except Exception as e:
        print(f"  ✗ 提交任务失败: {e}")
        return False

    print("\n"+"="*60)
    print("✓ Celery配置测试完成!")
    print("="*60)
    return True


if __name__ == "__main__":
    success = test_celery_connection()
    sys.exit(0 if success else 1)
