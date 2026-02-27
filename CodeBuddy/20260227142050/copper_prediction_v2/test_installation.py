"""
测试脚本 - 验证所有依赖包是否正确安装
"""

import sys

def test_import(module_name, package_name=None):
    """测试模块导入"""
    package_name = package_name or module_name
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name}: 已安装 (版本: {version})")
        return True
    except ImportError:
        print(f"❌ {package_name}: 未安装")
        return False

def test_torch_features():
    """测试PyTorch特性"""
    try:
        import torch
        print(f"   - PyTorch CUDA可用: {torch.cuda.is_available()}")
        print(f"   - PyTorch设备: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")
        return True
    except:
        return False

def test_akshare_data():
    """测试AKShare数据获取"""
    try:
        import akshare as ak
        print("   - AKShare数据功能: 可用")
        return True
    except:
        return False

if __name__ == '__main__':
    print("="*60)
    print("铜价预测系统 - 依赖检查")
    print("="*60)
    print()

    # 基础依赖
    print("【基础依赖】")
    numpy_ok = test_import('numpy')
    pandas_ok = test_import('pandas')
    sklearn_ok = test_import('sklearn', 'scikit-learn')
    xgboost_ok = test_import('xgboost')

    # 高级依赖
    print()
    print("【高级依赖】")
    torch_ok = test_import('torch', 'PyTorch')
    if torch_ok:
        test_torch_features()

    shap_ok = test_import('shap', 'SHAP')
    akshare_ok = test_import('akshare', 'AKShare')
    if akshare_ok:
        test_akshare_data()

    # 可视化
    print()
    print("【可视化】")
    test_import('matplotlib')
    test_import('plotly')

    print()
    print("="*60)

    # 总结
    all_basic = numpy_ok and pandas_ok and sklearn_ok and xgboost_ok
    all_advanced = torch_ok and shap_ok and akshare_ok

    if all_basic and all_advanced:
        print("✅ 所有依赖已安装,系统可以完整运行!")
        print()
        print("运行演示:")
        print("  python main.py --demo --data-source akshare")
        sys.exit(0)
    elif all_basic:
        print("⚠️  基础依赖已安装,可以使用XGBoost模型")
        print()
        print("运行演示:")
        print("  python main.py --demo --data-source mock")
        print()
        print("安装高级依赖:")
        print("  pip install torch shap")
        sys.exit(0)
    else:
        print("❌ 缺少必要依赖,请先安装:")
        print("  pip install numpy pandas scikit-learn xgboost")
        sys.exit(1)
