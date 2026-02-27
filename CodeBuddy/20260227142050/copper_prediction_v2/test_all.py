#!/usr/bin/env python3
"""
完整功能测试脚本 - 测试所有已安装的功能
"""

from main import CopperPredictionSystem
import sys

def test_basic_features():
    """测试基础功能"""
    print("="*60)
    print("测试 1: 基础功能 (XGBoost)")
    print("="*60)

    system = CopperPredictionSystem(data_source='mock')

    # 数据加载
    system.load_data(days=365)

    # XGBoost训练
    print("\n训练 XGBoost 模型...")
    metrics = system.train_xgboost()
    print(f"✅ XGBoost 训练成功 - RMSE: {metrics.get('rmse', 'N/A')}")

    # 预测
    pred = system.predict(horizon=5, model_type='xgboost')
    print(f"✅ 预测成功 - 当前: ¥{pred['current_price']}, 预测: ¥{pred['predicted_price']}")

    # 回测
    results = system.backtest()
    print(f"✅ 回测成功 - 收益: {results['total_return_pct']:.2f}%")

    # 生成报告
    report = system.generate_report()
    print(f"✅ 报告生成成功")

    print("\n" + "="*60)
    return True

def test_lstm():
    """测试LSTM模型"""
    print("\n测试 2: LSTM深度学习模型")
    print("="*60)

    try:
        import torch
        print(f"✅ PyTorch 已安装 (版本: {torch.__version__})")

        from main import CopperPredictionSystem
        system = CopperPredictionSystem(data_source='mock')
        system.load_data(days=365)

        print("\n训练 LSTM 模型...")
        history = system.train_lstm(epochs=5)

        print(f"✅ LSTM 训练成功 - 最佳验证损失: {history['best_val_loss']:.6f}")

        # LSTM预测
        pred = system.predict(horizon=5, model_type='lstm')
        print(f"✅ LSTM 预测成功 - 当前: ¥{pred['current_price']}, 预测: ¥{pred['predicted_price']}")

        return True

    except ImportError as e:
        print(f"❌ PyTorch 未安装: {e}")
        return False
    except Exception as e:
        print(f"❌ LSTM 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_shap():
    """测试SHAP模型解释"""
    print("\n测试 3: SHAP 模型解释")
    print("="*60)

    try:
        import shap
        print(f"✅ SHAP 已安装 (版本: {shap.__version__})")

        # 需要先训练模型
        from main import CopperPredictionSystem
        system = CopperPredictionSystem(data_source='mock')
        system.load_data(days=365)
        system.train_xgboost()

        print("\n生成模型解释...")
        explanation = system.explain_prediction()
        print(f"✅ 模型解释成功")

        if 'top_positive_features' in explanation:
            print("\n正向驱动因素:")
            for feat in explanation['top_positive_features'][:3]:
                print(f"  - {feat['feature']}: {feat.get('shap_value', 0):+.4f}")

        return True

    except ImportError as e:
        print(f"❌ SHAP 未安装: {e}")
        return False
    except Exception as e:
        print(f"❌ SHAP 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_akshare():
    """测试AKShare真实数据"""
    print("\n测试 4: AKShare 真实数据源")
    print("="*60)

    try:
        import akshare as ak
        print(f"✅ AKShare 已安装 (版本: {ak.__version__})")

        from main import CopperPredictionSystem

        # 尝试使用真实数据源
        print("\n尝试连接 AKShare...")
        system = CopperPredictionSystem(data_source='akshare')
        data = system.load_data(days=100)

        if not data.empty:
            print(f"✅ AKShare 数据获取成功 - {len(data)} 条记录")
            return True
        else:
            print("⚠️  AKShare 数据为空,使用模拟数据")
            return False

    except ImportError as e:
        print(f"❌ AKShare 未安装: {e}")
        return False
    except Exception as e:
        print(f"❌ AKShare 测试失败: {e}")
        print("⚠️  这可能是网络或API问题,不影响其他功能")
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("铜价预测系统 - 完整功能测试")
    print("="*60)

    results = {}

    # 测试1: 基础功能
    results['basic'] = test_basic_features()

    # 测试2: LSTM
    results['lstm'] = test_lstm()

    # 测试3: SHAP
    results['shap'] = test_shap()

    # 测试4: AKShare
    results['akshare'] = test_akshare()

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    summary = {
        'XGBoost基础功能': results['basic'],
        'LSTM深度学习': results['lstm'],
        'SHAP模型解释': results['shap'],
        'AKShare真实数据': results['akshare']
    }

    for feature, passed in summary.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{feature}: {status}")

    print("\n" + "="*60)

    # 退出码
    all_passed = all(results.values())
    if all_passed:
        print("🎉 所有功能测试通过!")
        sys.exit(0)
    elif results['basic']:
        print("✅ 基础功能可用,核心系统正常")
        sys.exit(0)
    else:
        print("❌ 基础功能测试失败,请检查安装")
        sys.exit(1)
