# 快速开始指南

## 当前状态

✅ 已安装:
- AKShare v1.16.50

⚠️ 需要处理:
- NumPy 2.x 兼容性问题
- PyTorch 未安装
- SHAP 未安装

## 解决方案

### 步骤1: 降级NumPy(必须)

NumPy 2.0与某些包不兼容,需要降级:

```bash
pip install "numpy<2"
```

### 步骤2: 安装PyTorch(用于LSTM)

```bash
# CPU版本
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 或者使用conda
conda install pytorch -c pytorch
```

### 步骤3: 安装SHAP(用于模型解释)

```bash
pip install shap
```

## 一键安装命令

```bash
# 修复NumPy并安装所有依赖
pip install "numpy<2" torch shap --index-url https://download.pytorch.org/whl/cpu
```

## 验证安装

运行测试脚本:

```bash
python test_installation.py
```

## 运行程序

### 使用模拟数据(无需真实数据)

```bash
python main.py --demo --data-source mock
```

### 使用真实数据(AKShare)

```bash
python main.py --demo --data-source akshare
```

## 功能说明

### 数据源选择

- `mock`: 使用模拟数据,快速测试
- `akshare`: 从AKShare获取真实铜价数据
- `auto`: 自动检测可用数据源

### 主要命令

```bash
# 完整演示
python main.py --demo --data-source mock

# 仅训练模型
python main.py --train --data-source mock

# 仅生成预测
python main.py --predict --data-source mock

# 运行回测
python main.py --backtest --data-source mock

# 生成报告
python main.py --report --data-source mock
```

## 特性说明

### 已启用功能(基础版本)
- ✅ XGBoost模型训练和预测
- ✅ 技术指标生成(RSI, MACD, 布林带等)
- ✅ 特征工程(40+特征)
- ✅ 策略回测
- ✅ 报告生成

### 可选功能(需要额外安装)
- 🔶 LSTM深度学习模型(需要PyTorch)
- 🔶 模型解释(SHAP分析)
- 🔶 真实数据(AKShare,已安装✅)

## 常见问题

### Q1: numpy版本冲突
```bash
pip install "numpy<2" --force-reinstall
```

### Q2: PyTorch安装失败
尝试不同的安装源:
```bash
# 方法1: pip
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 方法2: conda
conda install pytorch -c pytorch

# 方法3: 本地安装
# 从 https://pytorch.org/get-started/locally/ 下载whl文件
pip install /path/to/torch.whl
```

### Q3: SHAP安装慢
```bash
# 使用国内镜像
pip install shap -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q4: AKShare数据获取失败
```bash
# 更新AKShare
pip install --upgrade akshare

# 使用模拟数据
python main.py --demo --data-source mock
```

## 下一步

1. 运行测试: `python test_installation.py`
2. 运行演示: `python main.py --demo`
3. 查看报告: `cat report_*.txt`

## 技术支持

详细文档:
- INSTALL.md - 完整安装指南
- README.md - 项目说明
