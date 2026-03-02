#!/bin/bash

# RAG系统服务启动脚本

echo "=== RAG系统服务启动 ==="

# 检查后端服务是否已运行
if pgrep -f "uvicorn.*8800" > /dev/null; then
    echo "✅ 后端服务已在运行 (端口 8800)"
else
    echo "🚀 启动后端服务..."
    cd /home/zhangjh/work/code/python/rag/backend
    source /home/zhangjh/work/code/python/rag/venv/bin/activate
    nohup uvicorn app.main:app --reload --host 127.0.0.1 --port 8800 > backend.log 2>&1 &
    echo "✅ 后端服务已启动 (端口 8800)"
fi

# 等待后端服务启动
sleep 3

# 检查前端服务是否已运行
if pgrep -f "vite.*3000" > /dev/null; then
    echo "✅ 前端服务已在运行 (端口 3000)"
else
    echo "🚀 启动前端服务..."
    cd /home/zhangjh/work/code/python/rag/frontend
    nohup yarn dev --port 3000 > frontend.log 2>&1 &
    echo "✅ 前端服务已启动 (端口 3000)"
fi

# 等待前端服务启动
sleep 5

echo ""
echo "=== 服务状态检查 ==="

# 检查后端服务
if curl -s http://127.0.0.1:8800/ > /dev/null; then
    echo "✅ 后端API正常: http://127.0.0.1:8800"
    echo "   📖 API文档: http://127.0.0.1:8800/docs"
else
    echo "❌ 后端API异常"
fi

# 检查前端服务
if curl -s http://localhost:3000/ > /dev/null; then
    echo "✅ 前端服务正常: http://localhost:3000"
else
    echo "❌ 前端服务异常"
fi

# 检查代理
if curl -s http://localhost:3000/api/documents > /dev/null; then
    echo "✅ 前端代理正常"
else
    echo "❌ 前端代理异常"
fi

echo ""
echo "=== 系统就绪 ==="
echo "🌐 前端地址: http://localhost:3000"
echo "🔧 后端API: http://127.0.0.1:8800"
echo "📚 API文档: http://127.0.0.1:8800/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap 'echo "正在停止服务..."; pkill -f "uvicorn.*8800"; pkill -f "vite.*3000"; exit 0' INT
wait
