#!/bin/bash
# 汉化工作台 - 启动脚本（Mac / Linux）

if [ ! -d ".venv" ]; then
  echo "❌ 虚拟环境不存在，请先运行：bash setup.sh"
  exit 1
fi

echo "🚀 启动汉化工作台..."
echo "🌐 访问地址：http://localhost:8000"
echo "   按 Ctrl+C 停止"
echo ""

.venv/bin/python server.py
