"""
演示脚本 - 简化版铜价预测演示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from main import CopperPredictionSystem

def main():
    print("="*60)
    print("铜价预测系统 v2 - 简化演示")
    print("="*60)

    # 创建系统 (使用模拟数据)
    system = CopperPredictionSystem(data_source='mock')

    # 1. 加载数据
    print("\n步骤 1: 加载数据")
    system.load_data(days=365)

    # 2. 生成预测 (使用简单趋势预测)
    print("\n步骤 2: 生成预测")
    short_pred = system.predict(horizon=5)
    medium_pred = system.predict(horizon=30)

    # 3. 回测
    print("\n步骤 3: 运行回测")
    system.backtest()

    # 4. 生成报告
    print("\n步骤 4: 生成报告")
    system.generate_report()

    print("\n" + "="*60)
    print("演示完成!")
    print("="*60)

if __name__ == '__main__':
    main()
