#!/usr/bin/env python3
"""
快速演示 - 铜价预测v2
"""

import sys
sys.path.insert(0, '.')

from models.copper_model_v2 import CopperPriceModel

def demo():
    """快速演示"""
    print("\n" + "="*60)
    print("🚀 铜价预测系统 v2 - 快速演示")
    print("="*60)
    
    # 创建模型
    model = CopperPriceModel()
    
    print("\n📊 当前市场数据:")
    print(f"   沪铜价格: ¥{model.data['close'].iloc[-1]:,.2f}/吨")
    print(f"   美元指数: {model.data['dollar_index'].iloc[-1]:.2f}")
    print(f"   LME库存: {model.data['lme_inventory'].iloc[-1]:,.0f}吨")
    
    print("\n🔮 价格预测:")
    
    # 短期预测
    short = model.predict_short_term(5)
    print(f"\n   短期 (5天):")
    print(f"      预测价格: ¥{short['predicted_price']:,.2f}")
    print(f"      预期变化: {short['predicted_change']:+.2f}%")
    print(f"      趋势: {short['trend']}")
    
    # 中期预测
    medium = model.predict_medium_term(3)
    print(f"\n   中期 (3个月):")
    print(f"      预测价格: ¥{medium['predicted_price']:,.2f}")
    print(f"      预期变化: {medium['predicted_change']:+.2f}%")
    
    # 长期预测
    long = model.predict_long_term(1)
    print(f"\n   长期 (1年):")
    print(f"      预测价格: ¥{long['predicted_price']:,.2f}")
    print(f"      趋势: {long['trend']}")
    
    print("\n" + "="*60)
    print("✅ 演示完成!")
    print("="*60)
    print("\n提示: 安装ML库后可以获得更准确的预测结果")
    print("   pip install xgboost scikit-learn")
    print("\n启动Web服务:")
    print("   cd api && python main.py")
    print("="*60 + "\n")

if __name__ == '__main__':
    demo()
