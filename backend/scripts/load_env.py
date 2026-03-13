#!/usr/bin/env python3
"""
环境变量加载脚本
用于在VSCode调试时正确加载.env文件
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """
    加载环境变量
    优先从.env文件加载，然后从系统环境变量加载
    """
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent
    
    # .env文件路径
    env_file = current_dir / '.env'
    
    # 如果.env文件存在，则加载它
    if env_file.exists():
        print(f"加载环境变量文件: {env_file}")
        load_dotenv(env_file)
    else:
        print(f"警告: .env文件不存在: {env_file}")
    
    # 打印加载的环境变量（不包含敏感信息）
    env_vars = {
        'OPENAI_API_URL': os.getenv('OPENAI_API_URL'),
        'DB_URL': os.getenv('DB_URL'),
        'EMBEDDING_MODEL': os.getenv('EMBEDDING_MODEL'),
        'CHAT_MODEL': os.getenv('CHAT_MODEL'),
        'OPENAI_API_KEY': '***' if os.getenv('OPENAI_API_KEY') else None
    }
    
    print("环境变量配置:")
    for key, value in env_vars.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    load_environment()
