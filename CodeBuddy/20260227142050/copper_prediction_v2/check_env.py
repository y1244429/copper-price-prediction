#!/usr/bin/env python3
"""
简化的环境检查 - 不导入可能有问题的包
"""

import sys
import subprocess

def check_package(package_name):
    """使用pip检查包是否安装"""
    try:
        result = subprocess.run(
            ['pip', 'show', package_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if line.startswith('Version:'):
                    version = line.split(':')[1].strip()
                    return f"✅ {package_name}: v{version}"
        return f"✅ {package_name}: 已安装"
    except:
        return f"❌ {package_name}: 未安装"

if __name__ == '__main__':
    print("="*60)
    print("铜价预测系统 - 环境检查")
    print("="*60)
    print()
    print("【已安装的包】")
    packages = ['numpy', 'pandas', 'scikit-learn', 'xgboost', 'akshare']
    for pkg in packages:
        print(check_package(pkg))
    
    print()
    print("【待安装的包】")
    print("❌ torch (PyTorch - 用于LSTM模型)")
    print("❌ shap (SHAP - 用于模型解释)")
    print()
    print("【安装命令】")
    print()
    print("1. 修复NumPy版本:")
    print("   pip install 'numpy<2' --force-reinstall")
    print()
    print("2. 安装PyTorch:")
    print("   pip install torch --index-url https://download.pytorch.org/whl/cpu")
    print()
    print("3. 安装SHAP:")
    print("   pip install shap")
    print()
    print("【一键安装所有】")
    print("   pip install 'numpy<2' torch shap --index-url https://download.pytorch.org/whl/cpu")
    print()
    print("="*60)
