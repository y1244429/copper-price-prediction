#!/bin/bash
# 安装铜价预测系统所需的高级依赖包

echo "开始安装依赖包..."
echo "================================"

echo "1. 安装 PyTorch..."
pip install torch --index-url https://download.pytorch.org/whl/cpu

echo ""
echo "2. 安装 SHAP..."
pip install shap

echo ""
echo "3. 检查 AKShare..."
python -c "import akshare; print('AKShare 已安装,版本:', akshare.__version__)"

echo ""
echo "================================"
echo "安装完成!"
echo "请运行: python main.py --demo"
