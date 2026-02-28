#!/usr/bin/env python3
"""
测试新增的预测模型
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.advanced_models import (
    FundamentalModel, FundamentalConfig,
    MacroFactorModel, MacroConfig
)
from data.data_sources import MockDataSource

print("="*70)
print("测试新增预测模型")
print("="*70)

# 生成测试数据
print("\n[1] 生成测试数据...")
mock_source = MockDataSource()
base_data = mock_source.fetch_copper_price(
    start_date="2023-01-01",
    end_date="2024-12-31"
)

print(f"✓ 数据生成完成")
print(f"  数据形状: {base_data.shape}")
print(f"  日期范围: {base_data.index[0]} ~ {base_data.index[-1]}")
print(f"  最新价格: ¥{base_data['close'].iloc[-1]:,.2f}")

# 测试基本面模型
print("\n" + "="*70)
print("【基本面模型】长期趋势预测（6个月+）")
print("="*70)
print("\n核心变量:")
print("  - 供需平衡表：全球精铜产量、中国表观消费量、显性库存变化率")
print("  - 成本曲线支撑：C1成本90分位线、完全成本75分位线")
print("  - 矿山干扰率：智利、秘鲁等主要产区的罢工、品位下滑、政策风险")
print("\n建模方法：向量自回归（VAR）或结构方程模型")

try:
    fundamental_config = FundamentalConfig()
    fundamental_model = FundamentalModel(fundamental_config)
    
    print("\n[训练基本面模型...]")
    fundamental_metrics = fundamental_model.train(base_data)
    
    print("\n[生成180天预测...]")
    fundamental_pred = fundamental_model.predict(base_data, horizon=180)
    
    print("\n✓ 基本面模型预测结果:")
    print(f"  适用场景：6个月以上战略配置")
    print(f"  当前价格: ¥{fundamental_pred['current_price']:,.2f}")
    print(f"  预测价格: ¥{fundamental_pred['predicted_price']:,.2f}")
    print(f"  预测收益: {fundamental_pred['predicted_return']:+.2f}%")
    print(f"  预测周期: {fundamental_pred['horizon_days']}天")
    print(f"  预测趋势: {fundamental_pred['trend']}")
    print(f"  信心水平: {fundamental_pred['confidence']}")
    
except Exception as e:
    print(f"\n✗ 基本面模型测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试宏观因子模型
print("\n" + "="*70)
print("【宏观因子模型】中期波动预测（1-6个月）")
print("="*70)
print("\n核心变量:")
print("  - 美元指数：负相关性极强（系数通常-0.7以上）")
print("  - 中国PMI/信贷脉冲：铜被称为'铜博士'，对全球制造业景气度极度敏感")
print("  - 实际利率：10Y TIPS收益率反映持有机会成本")
print("  - 期限结构：LME升贴水（Contango/Backwardation）反映即期供需紧张度")
print("\n建模方法：动态因子模型（DFM）或ARDL（自回归分布滞后模型）")

try:
    macro_config = MacroConfig()
    macro_model = MacroFactorModel(macro_config)
    
    print("\n[训练宏观因子模型...]")
    macro_metrics = macro_model.train(base_data)
    
    print("\n[生成90天预测...]")
    macro_pred = macro_model.predict(base_data, horizon=90)
    
    print("\n✓ 宏观因子模型预测结果:")
    print(f"  适用场景：1-6个月战术调整")
    print(f"  当前价格: ¥{macro_pred['current_price']:,.2f}")
    print(f"  预测价格: ¥{macro_pred['predicted_price']:,.2f}")
    print(f"  预测收益: {macro_pred['predicted_return']:+.2f}%")
    print(f"  预测周期: {macro_pred['horizon_days']}天")
    print(f"  预测趋势: {macro_pred['trend']}")
    print(f"  信心水平: {macro_pred['confidence']}")
    
except Exception as e:
    print(f"\n✗ 宏观因子模型测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("测试完成!")
print("="*70)
print("\n📊 总结:")
print("  ✅ 基本面模型：适合长期战略配置（6个月+）")
print("  ✅ 宏观因子模型：适合中期战术调整（1-6个月）")
print("  ✅ 技术分析模型（原有）：适合短期交易（天/周级别）")
print("\n多模型组合使用可以获得更全面的预测视角！")
print("="*70)
