#!/bin/bash
# 汉化工作台 - 环境初始化脚本（Mac / Linux）

set -e

echo "🔧 创建虚拟环境..."
python3 -m venv .venv

echo "📦 安装依赖..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo ""
echo "✅ 环境初始化完成！"
echo ""
echo "启动服务："
echo "  ./start.sh"
echo "  或手动：.venv/bin/python server.py"
