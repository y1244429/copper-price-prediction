#!/usr/bin/env python3
"""
模型验证与风险管理演示脚本
"""

from main import CopperPredictionSystem
from datetime import datetime

def main():
    print("="*80)
    print("模型验证与风险管理 - 完整演示")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 创建系统
    print("[步骤1] 初始化系统...")
    system = CopperPredictionSystem(data_source='auto')
    print()
    
    # 2. 加载数据
    print("[步骤2] 加载数据...")
    system.load_data(days=365)
    print()
    
    # 3. 训练XGBoost模型
    print("[步骤3] 训练XGBoost模型...")
    try:
        system.train_xgboost()
    except Exception as e:
        print(f"  XGBoost训练失败: {e}")
    print()
    
    # 4. 训练宏观因子模型
    print("[步骤4] 训练宏观因子模型...")
    try:
        system.train_macro()
    except Exception as e:
        print(f"  宏观因子模型训练失败: {e}")
    print()
    
    # 5. 训练基本面模型
    print("[步骤5] 训练基本面模型...")
    try:
        system.train_fundamental()
    except Exception as e:
        print(f"  基本面模型训练失败: {e}")
    print()
    
    # 6. 验证XGBoost模型
    print("[步骤6] 验证XGBoost模型...")
    if system.xgb_model:
        try:
            xgb_results = system.validate_model('xgboost')
            print("\n✓ XGBoost模型验证完成")
        except Exception as e:
            print(f"  XGBoost模型验证失败: {e}")
    else:
        print("  XGBoost模型未训练，跳过验证")
    print()
    
    # 7. 验证宏观因子模型
    print("[步骤7] 验证宏观因子模型...")
    if system.macro_model:
        try:
            macro_results = system.validate_model('macro')
            print("\n✓ 宏观因子模型验证完成")
        except Exception as e:
            print(f"  宏观因子模型验证失败: {e}")
    else:
        print("  宏观因子模型未训练，跳过验证")
    print()
    
    # 8. 生成完整报告
    print("[步骤8] 生成完整分析报告...")
    try:
        system.generate_report(include_xgb=True)
        print("\n✓ 文本和HTML报告生成完成")
    except Exception as e:
        print(f"  报告生成失败: {e}")
    print()
    
    # 9. 生成PPT报告
    print("[步骤9] 生成PPT报告...")
    try:
        system.generate_ppt_report(include_xgb=True)
        print("\n✓ PPT报告生成完成")
    except Exception as e:
        print(f"  PPT生成失败: {e}")
    print()
    
    print("="*80)
    print("演示完成!")
    print("="*80)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("生成文件:")
    print("  - validation_report_*.txt (模型验证报告)")
    print("  - report_*.txt (文本报告)")
    print("  - report_*.html (HTML报告)")
    print("  - report_*.pptx (PPT报告)")


if __name__ == '__main__':
    main()
