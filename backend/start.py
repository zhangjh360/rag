#!/usr/bin/env python3
"""
RAG后端服务启动脚本
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 加载环境变量
from app.config.settings import validate_config

def main():
    """主函数"""
    print("=== RAG后端服务启动 ===")
    
    # 验证配置
    if not validate_config():
        print("配置验证失败，请检查.env文件")
        return 1
    
    # 启动FastAPI应用
    print("启动FastAPI应用...")
    os.system("uvicorn app.main:app --reload --host 0.0.0.0 --port 8800")

if __name__ == "__main__":
    sys.exit(main())
