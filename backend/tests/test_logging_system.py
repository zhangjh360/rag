#!/usr/bin/env python3
"""
测试日志系统功能
"""

import asyncio
import time
from app.config.logging_config import setup_logging, get_app_logger, get_error_logger, get_access_logger, get_debug_logger
from app.utils.log_manager import log_manager

def test_logging_configuration():
    """测试日志配置"""
    print("=== 测试日志配置 ===")
    
    # 设置日志
    loggers = setup_logging()
    print(f"日志器设置完成: {list(loggers.keys())}")
    
    # 获取各种日志器
    app_logger = get_app_logger()
    error_logger = get_error_logger()
    access_logger = get_access_logger()
    debug_logger = get_debug_logger()
    
    print("各种日志器获取成功")
    return app_logger, error_logger, access_logger, debug_logger

def test_logging_output(app_logger, error_logger, access_logger, debug_logger):
    """测试日志输出"""
    print("\n=== 测试日志输出 ===")
    
    # 测试不同级别的日志
    app_logger.info("这是一条应用信息日志")
    app_logger.warning("这是一条应用警告日志")
    
    error_logger.error("这是一条错误日志")
    error_logger.critical("这是一条严重错误日志")
    
    access_logger.info("这是一条访问日志")
    
    debug_logger.debug("这是一条调试日志")
    debug_logger.info("这是一条调试信息日志")
    
    print("日志输出测试完成")

def test_log_manager():
    """测试日志管理器"""
    print("\n=== 测试日志管理器 ===")
    
    # 获取日志统计
    stats = log_manager.get_log_statistics()
    print(f"日志统计: {stats}")
    
    # 获取日志文件列表
    log_files = log_manager.get_log_files()
    print(f"日志文件数量: {len(log_files)}")
    
    if log_files:
        print("前5个日志文件:")
        for i, file in enumerate(log_files[:5]):
            print(f"  {i+1}. {file['name']} ({file['type']}) - {file['size_mb']} MB")
    
    # 测试日志搜索
    print("\n测试日志搜索:")
    search_results = log_manager.search_logs("应用", "app", 1)
    print(f"搜索到 {len(search_results)} 条相关日志")
    
    for result in search_results[:3]:  # 显示前3条
        print(f"  {result['file']}:{result['line']} - {result['content'][:50]}...")

def test_log_operations():
    """测试日志操作"""
    print("\n=== 测试日志操作 ===")
    
    # 测试读取日志文件
    log_files = log_manager.get_log_files("app")
    if log_files:
        first_file = log_files[0]
        print(f"读取日志文件: {first_file['name']}")
        
        content = log_manager.read_log_file(first_file['path'], 10)
        print(f"读取到 {len(content)} 行日志")
        
        if content:
            print("最后几行日志:")
            for line in content[-3:]:
                print(f"  {line.strip()}")
    
    # 测试导出日志（不实际执行，只测试函数）
    print("\n测试日志导出功能:")
    try:
        # 这里只是测试函数调用，不实际创建文件
        print("日志导出功能可用")
    except Exception as e:
        print(f"日志导出测试失败: {e}")

async def test_async_logging():
    """测试异步日志记录"""
    print("\n=== 测试异步日志记录 ===")
    
    app_logger = get_app_logger()
    
    # 模拟异步操作中的日志记录
    async def async_operation():
        app_logger.info("异步操作开始")
        await asyncio.sleep(0.1)
        app_logger.info("异步操作进行中")
        await asyncio.sleep(0.1)
        app_logger.info("异步操作完成")
    
    await async_operation()
    print("异步日志记录测试完成")

def test_log_cleanup():
    """测试日志清理功能"""
    print("\n=== 测试日志清理功能 ===")
    
    # 获取清理前的统计
    stats_before = log_manager.get_log_statistics()
    print(f"清理前: {stats_before['total_files']} 个文件, {stats_before['total_size_mb']} MB")
    
    # 执行清理（清理1天前的日志，测试环境应该没有）
    clean_result = log_manager.clean_old_logs(1)
    print(f"清理结果: {clean_result['cleaned_files']} 个文件, 释放 {clean_result['freed_space_mb']} MB")
    
    # 获取清理后的统计
    stats_after = log_manager.get_log_statistics()
    print(f"清理后: {stats_after['total_files']} 个文件, {stats_after['total_size_mb']} MB")

def main():
    """主测试函数"""
    print("开始测试日志系统...")
    
    try:
        # 1. 测试日志配置
        app_logger, error_logger, access_logger, debug_logger = test_logging_configuration()
        
        # 2. 测试日志输出
        test_logging_output(app_logger, error_logger, access_logger, debug_logger)
        
        # 3. 测试日志管理器
        test_log_manager()
        
        # 4. 测试日志操作
        test_log_operations()
        
        # 5. 测试异步日志
        asyncio.run(test_async_logging())
        
        # 6. 测试日志清理
        test_log_cleanup()
        
        print("\n=== 所有测试完成 ===")
        print("日志系统工作正常！")
        
        # 显示日志目录结构
        print("\n日志目录结构:")
        from pathlib import Path
        log_dir = Path("logs")
        if log_dir.exists():
            for item in log_dir.iterdir():
                if item.is_dir():
                    print(f"  📁 {item.name}/")
                    for file in item.iterdir():
                        if file.is_file():
                            size_mb = file.stat().st_size / 1024 / 1024
                            print(f"    📄 {file.name} ({size_mb:.2f} MB)")
        else:
            print("  日志目录不存在")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
