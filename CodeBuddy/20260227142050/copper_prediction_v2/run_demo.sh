#!/bin/bash
# 铜价预测系统 v2 - 快速启动脚本

echo "============================================================"
echo "铜价预测系统 v2 - 快速启动"
echo "============================================================"
echo ""

# 检查环境
echo "检查环境..."
python check_env.py
echo ""

# 询问用户选择
echo "请选择运行模式:"
echo "1. 完整演示 (推荐)"
echo "2. 测试所有功能"
echo "3. 单独训练模型"
echo "4. 仅生成预测"
echo "5. 查看状态报告"
echo ""
read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo ""
        echo "运行完整演示..."
        python main.py --demo --data-source mock
        ;;
    2)
        echo ""
        echo "测试所有功能..."
        python test_all.py
        ;;
    3)
        echo ""
        echo "训练模型..."
        python main.py --train --data-source mock
        ;;
    4)
        echo ""
        echo "生成预测..."
        python main.py --predict --data-source mock
        ;;
    5)
        echo ""
        echo "查看状态报告..."
        if [ -f "FINAL_STATUS.md" ]; then
            cat FINAL_STATUS.md
        else
            echo "未找到状态报告,请先运行测试"
        fi
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo "运行完成!"
echo "============================================================"
