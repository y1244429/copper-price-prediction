#!/usr/bin/env python3
"""
测试单独模型生成PPT功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from main import CopperPredictionSystem

print("="*60)
print("测试：单独模型生成PPT报告")
print("="*60)

# 测试1: 仅宏观因子模型
print("\n[测试1] 仅运行宏观因子模型...")
print("-"*60)

system = CopperPredictionSystem(data_source='auto')
system.load_data(days=365)

try:
    system.train_macro()
    print("\n[生成报告和PPT]")
    system.generate_report(include_xgb=False)
    system.generate_ppt_report(include_xgb=False)
    print("✅ 宏观因子模型报告和PPT生成完成！")
except Exception as e:
    print(f"❌ 宏观因子模型测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)

# 测试2: 仅基本面模型
print("\n[测试2] 仅运行基本面模型...")
print("-"*60)

system2 = CopperPredictionSystem(data_source='auto')
system2.load_data(days=365)

try:
    system2.train_fundamental()
    print("\n[生成报告和PPT]")
    system2.generate_report(include_xgb=False)
    system2.generate_ppt_report(include_xgb=False)
    print("✅ 基本面模型报告和PPT生成完成！")
except Exception as e:
    print(f"❌ 基本面模型测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("测试完成！")
print("="*60)
