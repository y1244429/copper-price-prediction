# 铜价预测系统 v2

基于机器学习的铜价预测系统，集成XGBoost、LSTM深度学习、模型解释性分析和自动任务调度。

## 🚀 新特性

| 特性 | 描述 |
|------|------|
| 🔋 **多源数据** | AKShare、Yahoo Finance、Wind、模拟数据 |
| 🧠 **双模型** | XGBoost + LSTM深度学习 |
| 🔍 **可解释AI** | SHAP特征重要性分析 |
| ⏰ **自动调度** | 定时更新数据和模型 |
| 📊 **完整回测** | 多策略回测引擎 |
| 🌐 **API服务** | FastAPI + Web界面 |
| 📈 **技术指标** | MACD、KDJ、RSI、布林带、一目均衡表 |
| 🚨 **实时预警** | 价格/指标/波动率预警 |
| ☁️ **云端部署** | Docker + K8s + AWS支持 |

## 📁 项目结构

```
copper_prediction_v2/
├── main.py                    # 统一入口
├── models/
│   ├── copper_model_v2.py    # XGBoost + 特征工程 + 回测
│   ├── lstm_model.py         # LSTM/GRU深度学习
│   └── model_explainer.py    # SHAP解释性分析
├── data/
│   ├── data_sources.py       # 基础数据源
│   ├── real_data.py          # AKShare/Yahoo真实数据
│   ├── wind_data.py          # Wind金融终端数据
│   └── scheduler.py          # 任务调度
├── features/
│   └── technical_indicators.py  # 高级技术指标
├── alerts/
│   └── alert_system.py       # 实时预警系统
├── api/
│   └── main.py               # FastAPI服务
├── deployment/
│   ├── Dockerfile            # Docker配置
│   ├── docker-compose.yml    # Docker Compose
│   ├── k8s-deployment.yaml   # Kubernetes配置
│   └── ecs-params.yml        # AWS ECS配置
├── .github/
│   └── workflows/
│       └── ci-cd.yml         # GitHub Actions CI/CD
├── tests/
│   └── test_model.py         # 测试脚本
├── demo.py                   # 快速演示
├── requirements.txt          # 依赖列表
├── deploy.sh                 # 部署脚本
└── README.md                 # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd copper_prediction_v2
pip install -r requirements.txt
```

### 2. 运行演示

```bash
# 完整演示
python main.py --demo

# 或分步
python main.py --predict      # 生成预测
python main.py --train        # 训练模型
python main.py --backtest     # 运行回测
python main.py --report       # 生成报告
```

### 3. 启动API服务

```bash
cd api
python main.py

# 访问 http://localhost:8000/ui
```

### 4. 启动自动调度

```bash
python main.py --scheduler
```

## 💻 Python API

```python
from main import CopperPredictionSystem

# 创建系统
system = CopperPredictionSystem(data_source='mock')

# 完整流程
system.quick_demo()

# 或分步使用
system.load_data(days=365)
system.train_xgboost()
system.train_lstm()

# 生成预测
short = system.predict(horizon=5, model_type='xgboost')
medium = system.predict(horizon=30, model_type='lstm')

# 解释预测
explanation = system.explain_prediction()

# 策略回测
results = system.backtest(strategy='trend_following')

# 生成报告
report = system.generate_report()
```

## 🧠 模型算法

### XGBoost
- 500棵决策树
- 37个工程特征
- 时序交叉验证
- 早停机制

### LSTM
- 双向LSTM + Attention
- 序列长度: 60天
- 隐藏维度: 128
- 支持GPU加速

### 特征工程
```
价格特征: 收益率、波动率、价格位置
技术指标: RSI、MACD、布林带、OBV
宏观特征: 美元指数、PMI、库存
统计特征: 偏度、峰度、动量
交互特征: 价格×美元、库存²
```

## 📊 回测指标

- 总收益率
- 年化收益率
- 夏普比率
- 最大回撤
- Calmar比率
- 胜率

## 🔍 模型解释

使用SHAP分析每个预测的特征贡献：

```python
explanation = system.explain_prediction()
# 返回:
# - 基础值 (base value)
# - 各特征贡献度
# - 正向/负向驱动因素
```

## ⏰ 任务调度

自动定时任务：

| 任务 | 频率 | 时间 |
|------|------|------|
| 更新价格数据 | 每日 | 09:00 |
| 更新库存数据 | 每日 | 09:30 |
| 重训练模型 | 每周 | 周日 02:00 |
| 生成报告 | 每日 | 08:00 |
| 清理旧数据 | 每周 | 周六 03:00 |

## 🔧 配置

### 数据源切换

```python
# 使用AKShare真实数据
system = CopperPredictionSystem(data_source='akshare')

# 使用模拟数据
system = CopperPredictionSystem(data_source='mock')
```

### 模型参数

编辑 `models/copper_model_v2.py` 中的 `ModelConfig`：

```python
@dataclass
class ModelConfig:
    xgb_n_estimators: int = 500
    xgb_max_depth: int = 6
    lstm_hidden_dim: int = 128
    lstm_num_layers: int = 2
```

## 📈 API端点

启动服务后访问 http://localhost:8000/docs

| 端点 | 描述 |
|------|------|
| `GET /api/predict` | 铜价预测 |
| `GET /api/backtest` | 策略回测 |
| `GET /api/features` | 特征重要性 |
| `GET /api/price/history` | 历史价格 |
| `GET /ui` | Web界面 |

## 🧪 测试

```bash
cd tests
python test_model.py
```

## 📦 依赖

核心依赖：
- numpy, pandas
- scikit-learn, xgboost
- torch (可选，用于LSTM)
- fastapi, uvicorn
- shap (可选，用于模型解释)
- akshare (可选，用于真实数据)
- schedule (用于任务调度)

## ⚠️ 免责声明

本系统仅供学习和研究使用，不构成投资建议。预测结果仅供参考，实际交易风险自负。

## 📄 许可

MIT License
