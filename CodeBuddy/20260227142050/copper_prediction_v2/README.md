# 铜价预测系统 v2

基于机器学习的铜价预测系统,使用 XGBoost 和 LSTM 等多种算法进行价格预测。

## 🎯 核心功能

- **数据来源**: 支持模拟数据、AKShare 等多种数据源
- **预测算法**: XGBoost + LSTM 混合模型
- **技术指标**: RSI、MACD、布林带、移动平均等
- **模型解释**: SHAP 可解释性分析
- **回测验证**: 完整的策略回测功能

## 📦 安装依赖

### 基础依赖
```bash
pip install numpy pandas scikit-learn xgboost
```

### 高级依赖 (可选但推荐)

详细安装指南请查看 [INSTALL.md](INSTALL.md)

```bash
# PyTorch (用于LSTM模型)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# SHAP (用于模型解释)
pip install shap

# AKShare (用于真实数据,已安装)
pip install akshare
```

### 一键安装
```bash
pip install -r requirements.txt
```

### 验证安装
```bash
# 检查PyTorch
python -c "import torch; print('PyTorch:', torch.__version__)"

# 检查SHAP
python -c "import shap; print('SHAP:', shap.__version__)"

# 检查AKShare
python -c "import akshare as ak; print('AKShare:', ak.__version__)"
```

## 🚀 快速开始

### 1. 运行演示

```bash
python main.py --demo
```

### 2. 使用真实数据

```bash
# 使用AKShare获取真实铜价数据
python main.py --demo --data-source akshare

# 使用模拟数据
python main.py --demo --data-source mock
```

### 3. 单独功能

```bash
# 生成预测
python main.py --predict

# 训练模型
python main.py --train

# 运行回测
python main.py --backtest

# 生成报告
python main.py --report
```

## 💻 Python API 使用

```python
from main import CopperPredictionSystem

# 初始化系统
system = CopperPredictionSystem(data_source='mock')

# 快速演示
system.quick_demo()

# 自定义流程
system.load_data(days=365)
system.train_xgboost()
system.predict(horizon=5)
system.backtest()
system.generate_report()
```

## 📊 项目结构

```
copper_prediction_v2/
├── main.py                    # 主程序入口
├── models/
│   ├── copper_model_v2.py    # XGBoost + 技术指标
│   ├── lstm_model.py         # LSTM/GRU 深度学习
│   └── model_explainer.py    # SHAP 模型解释
├── data/
│   ├── data_sources.py       # 数据源管理
│   ├── real_data.py          # 实时数据获取
│   └── scheduler.py          # 任务调度
├── features/
│   └── technical_indicators.py # 技术指标计算
├── demo.py                   # 演示脚本
├── requirements.txt          # 依赖包
└── README.md                 # 项目文档
```

## 🎨 特征说明

### 价格特征
- 日收益率 (1天, 5天, 20天)
- 移动平均线 (5, 10, 20, 30, 60日)
- 价格波动率
- 价格动量

### 技术指标
- **RSI**: 相对强弱指数 (14日)
- **MACD**: 指数平滑异同移动平均线
- **布林带**: 价格通道和宽度
- **成交量比**: 成交量动量

## 📈 模型性能

### XGBoost
- 500 棵决策树
- 37 个技术特征
- 支持 GPU 加速
- 高精度预测

### LSTM
- 双向 LSTM + Attention
- 输入窗口: 30-60 天
- 隐藏层维度: 128
- GPU 加速训练

## ⚠️ 注意事项

1. 本系统仅供学习和研究使用
2. 预测结果不构成投资建议
3. 实际应用需要更复杂的数据和模型

## 📄 许可证

MIT License
