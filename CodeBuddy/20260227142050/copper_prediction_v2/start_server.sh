#!/bin/bash

echo "🚀 铜价预测系统 v3 - Web服务器"
echo "======================================"
echo ""

# 获取本机IP
LOCAL_IP=$(ipconfig getifaddr en0 | grep "inet " | awk '{print $2}')

if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="localhost"
fi

echo "📱 本地访问: http://localhost:8000"
echo "🌐 局域网访问: http://$LOCAL_IP:8000"
echo "📡 可以在手机浏览器中访问上述地址"
echo ""
echo "📋 如需互联网访问，建议使用云服务部署"
echo "⏹ 按 Ctrl+C 停止服务器"
echo ""
echo "======================================"
echo ""

# 启动服务器
cd "$(dirname "$0")"
python3 app.py
