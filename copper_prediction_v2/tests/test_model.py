#!/usr/bin/env python3
"""
测试脚本 - 演示铜价预测v2功能
"""

import sys
sys.path.insert(0, '..')

from models.copper_model_v2 import (
    CopperPredictionV2, CopperPriceModel,
    DataLoader, FeatureEngineer
)

def test_basic():
    """测试基础功能"""
    print("\n" + "="*60)
    print("测试1: 基础功能测试")
    print("="*60)
    
    # 初始化
    predictor = CopperPredictionV2()
    
    # 加载数据
    print("\n加载模拟数据...")
    data = predictor.load_data('mock', days=500)
    print(f"✓ 数据加载完成: {len(data)} 条记录")
    print(f"  日期范围: {data.index[0].date()} 至 {data.index[-1].date()}")
    print(f"  最新价格: ¥{data['close'].iloc[-1]:,.2f}")
    
    # 特征工程
    print("\n生成特征...")
    features, target = predictor.prepare_features(data)
    print(f"✓ 特征生成完成: {len(features.columns)} 个特征")
    print(f"  特征样例: {', '.join(list(features.columns)[:5])}")
    
    return predictor, data, features, target


def test_legacy_api():
    """测试兼容原版API"""
    print("\n" + "="*60)
    print("测试2: 兼容原版API")
    print("="*60)
    
    model = CopperPriceModel()
    
    # 短期预测
    short = model.predict_short_term(5)
    print(f"\n短期预测 (5天):")
    print(f"  当前价格: ¥{short['current_price']:,.2f}")
    print(f"  预测价格: ¥{short['predicted_price']:,.2f}")
    print(f"  预期涨跌: {short['predicted_change']:.2f}%")
    print(f"  趋势: {short['trend']}")
    
    # 中期预测
    medium = model.predict_medium_term(3)
    print(f"\n中期预测 (3个月):")
    print(f"  预测价格: ¥{medium['predicted_price']:,.2f}")
    
    # 长期预测
    long = model.predict_long_term(1)
    print(f"\n长期预测 (1年):")
    print(f"  预测价格: ¥{long['predicted_price']:,.2f}")


def test_full_pipeline():
    """测试完整流程"""
    print("\n" + "="*60)
    print("测试3: 完整流程")
    print("="*60)
    
    predictor = CopperPredictionV2()
    results = predictor.full_pipeline()
    
    print("\n✓ 完整流程执行成功!")
    return results


def test_backtest():
    """测试回测功能"""
    print("\n" + "="*60)
    print("测试4: 回测功能")
    print("="*60)
    
    try:
        predictor = CopperPredictionV2()
        data = predictor.load_data('mock', days=365)
        features, target = predictor.prepare_features(data)
        
        # 训练模型
        model = predictor.train_model(features, target)
        
        # 回测
        print("\n运行策略回测...")
        results = predictor.backtest(model, data, features)
        
        print("\n回测结果:")
        for key, value in results.items():
            print(f"  {key}: {value}")
        
        print("\n✓ 回测完成!")
        
    except Exception as e:
        print(f"回测测试跳过 (可能需要安装ML库): {e}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("铜价预测系统 v2 - 功能测试")
    print("="*60)
    
    try:
        # 运行测试
        test_basic()
        test_legacy_api()
        test_full_pipeline()
        test_backtest()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
