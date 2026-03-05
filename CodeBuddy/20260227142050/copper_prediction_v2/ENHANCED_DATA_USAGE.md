# 增强数据系统使用说明

## 📊 概述

增强数据系统为铜价预测系统添加了三个关键数据维度：

1. **实时宏观数据** - 美元指数、PMI、利率、VIX恐慌指数
2. **资金流向数据** - CFTC持仓报告、期货持仓量、成交量分布
3. **新闻情绪分析** - 财经新闻爬取、NLP情绪分析、突发事件检测

---

## 🚀 快速开始

### 1. 运行增强数据获取

```bash
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2

# 测试增强数据模块
python3 test_enhanced_data.py

# 运行增强预测
python3 run_enhanced_prediction.py
```

### 2. 输出示例

```
======================================================================
增强预测系统
======================================================================

当前价格: ¥102,100.00

【宏观数据】
  美元指数: 157.71
  PMI: 53.7
  联邦利率: 5.25%
  VIX: 19.6

【资金流向】
  商业净头寸: -47,248 手
  投机净头寸: 38,784 手
  总持仓量: 259,095 手

【新闻情绪】
  文章总数: 5
  情绪分布: 正面1 / 负面2 / 中性2
  整体情绪: negative (分数: -0.20)

【风险信号】
  1. 🔴 美元指数过强(157.71),对铜价形成压制
  2. 🟡 新闻情绪偏负面(分数: -0.20)

市场状态: bear

预测价格: ¥101,386.93 (-0.70%)
预测区间: ¥89,220.50 ~ ¥113,553.37
置信度: low

【投资建议】
操作方向: 🟡 观望
建议: 建议观望，但需谨慎控制仓位

⚠️  检测到 2 个风险信号
```

---

## 📁 文件结构

```
copper_prediction_v2/
├── data/
│   ├── enhanced_data_sources.py      # 增强数据源模块
│   ├── prediction_db.py             # 数据库（已增强）
│   └── real_data.py                # 真实数据源
├── models/
│   ├── enhanced_predictor.py         # 增强预测器
│   └── ...
├── test_enhanced_data.py            # 测试脚本
├── run_enhanced_prediction.py       # 运行脚本
└── outputs/                         # 输出目录
    ├── enhanced_data_*.json         # 增强数据
    └── enhanced_prediction_*.json    # 预测结果
```

---

## 🔧 模块说明

### 1. EnhancedMacroData (实时宏观数据)

**功能**:
- 获取实时美元指数
- 获取最新PMI数据
- 获取实时利率（联邦基金利率）
- 获取VIX恐慌指数

**数据源**:
- Alpha Vantage API (免费)
- FRED API (免费)
- Yahoo Finance (免费)

**使用示例**:
```python
from data.enhanced_data_sources import EnhancedMacroData

macro = EnhancedMacroData()

# 获取所有宏观数据
all_macro = macro.get_all_macro_data()

# 单独获取某项数据
dollar_index = macro.get_dollar_index_realtime()
pmi = macro.get_pmi_latest()
vix = macro.get_vix_realtime()
```

---

### 2. CapitalFlowData (资金流向数据)

**功能**:
- 获取CFTC持仓报告（周度）
- 获取期货持仓量数据（日度）
- 获取成交量分布（分时）

**数据源**:
- CFTC 官方网站
- 交易所API (SHFE, LME, COMEX)

**使用示例**:
```python
from data.enhanced_data_sources import CapitalFlowData

capital = CapitalFlowData()

# 获取所有资金流向数据
all_capital = capital.get_all_capital_flow_data()

# 单独获取某项数据
cftc_report = capital.get_cftc_report()
open_interest = capital.get_futures_open_interest(days=30)
volume_dist = capital.get_volume_distribution()
```

---

### 3. NewsSentimentAnalyzer (新闻情绪分析)

**功能**:
- 爬取财经新闻
- NLP情绪分析（正面/负面/中性）
- 突发事件检测

**新闻源**:
- Reuters
- CNBC
- Bloomberg
- 财经媒体

**使用示例**:
```python
from data.enhanced_data_sources import NewsSentimentAnalyzer

analyzer = NewsSentimentAnalyzer()

# 获取新闻情绪汇总
sentiment = analyzer.get_news_sentiment_summary()

# 单独获取新闻
news = analyzer.fetch_financial_news(num_articles=10)

# 分析单条新闻情绪
result = analyzer.analyze_sentiment("PMI超预期增长，市场乐观")

# 检测突发事件
emergencies = analyzer.detect_emergency_events(news_list)
```

---

### 4. EnhancedDataIntegration (数据整合)

**功能**:
- 整合所有增强数据
- 生成风险信号
- 综合分析

**使用示例**:
```python
from data.enhanced_data_sources import EnhancedDataIntegration

integration = EnhancedDataIntegration()

# 获取综合增强数据
data = integration.get_comprehensive_data()

# 打印摘要
integration.print_summary(data)

# 保存到文件
integration.save_to_file(data, "enhanced_data.json")
```

---

### 5. SimpleEnhancedPredictor (增强预测器)

**功能**:
- 结合增强数据进行预测
- 动态权重调整
- 风险调整
- 生成投资建议

**使用示例**:
```python
from run_enhanced_prediction import SimpleEnhancedPredictor

predictor = SimpleEnhancedPredictor()

# 执行预测
result = predictor.predict(horizon=5)

# 访问结果
print(f"预测价格: {result['predicted_price']}")
print(f"市场状态: {result['market_state']}")
print(f"投资建议: {result['recommendation']['advice']}")
```

---

## 🎯 风险信号系统

系统会自动检测以下风险信号：

| 信号类型 | 触发条件 | 等级 |
|---------|---------|------|
| VIX过高 | VIX > 30 | 高 |
| VIX偏高 | VIX > 25 | 中 |
| 美元过强 | 美元指数 > 102 | 高 |
| PMI过低 | PMI < 45 | 高 |
| PMI收缩 | PMI < 50 | 中 |
| 新闻情绪负面 | 整体情绪 = negative | 中 |
| 突发事件 | 检测到突发事件 | 高/中 |
| 投机大幅做空 | 投机净头寸 < -50,000 | 高 |

---

## 📊 市场状态判断

系统根据风险信号和情绪判断市场状态：

| 市场状态 | 判断条件 | 模型权重调整 |
|---------|---------|-------------|
| **Normal** | 无高风险信号，情绪中性 | 基础权重 |
| **Bull** | 整体情绪正面 | 基本面升权 |
| **Bear** | 整体情绪负面 | 宏观升权 |
| **Crisis** | 高风险信号≥2个 | 技术降权，宏观升权 |

---

## 🎨 置信度分级

系统根据风险信号数量确定置信度：

| 置信度 | 条件 | 预测区间宽度 | 仓位建议 |
|-------|------|-------------|---------|
| **High** | 无高风险信号 | ±5% | 40-80% |
| **Medium** | 有1-2个中风险信号 | ±8% | 30-50% |
| **Low** | 有高风险信号或≥3个信号 | ±12% | 10-20% |

---

## 💡 与传统预测的区别

### 传统预测
- 仅基于历史价格和技术指标
- 固定模型权重
- 无法感知突发事件
- 不考虑市场情绪

### 增强预测
- 整合实时宏观、资金、情绪数据
- 动态模型权重
- 突发事件预警
- 风险调整机制

---

## 🔌 API配置

目前使用模拟数据，如需使用真实API：

### 1. Alpha Vantage API
```python
# 在 enhanced_data_sources.py 中配置
self.api_key = "YOUR_ALPHA_VANTAGE_API_KEY"
```

### 2. FRED API
```python
# 在 enhanced_data_sources.py 中配置
self.api_key = "YOUR_FRED_API_KEY"
```

### 3. CFTC API
```python
# 需要从CFTC官网下载或使用第三方数据服务
```

---

## 📈 扩展建议

### 1. 实时数据源接入
- Wind API（国内，付费）
- Bloomberg API（全球，付费）
- TradingView Webhook（免费）
- Yahoo Finance Real-time（免费）

### 2. 高频数据
- 分钟级价格数据
- Tick级数据
- 分时成交量

### 3. 更多情绪指标
- 社交媒体情绪（Twitter, 微博）
- 谷歌搜索趋势
- 新闻情绪更精细分类

### 4. 高级NLP
- BERT模型情感分析
- 事件抽取
- 因果关系分析

---

## 🚨 风险提示

1. **模拟数据**: 当前部分数据为模拟值，需接入真实API才能用于实盘
2. **模型局限性**: 增强数据仍无法预测所有黑天鹅事件
3. **决策辅助**: 系统仅供参考，不构成投资建议
4. **止损设置**: 永远设置止损位控制风险
5. **多维度验证**: 结合多种分析工具，不依赖单一模型

---

## 📝 更新日志

### v1.0 (2026-03-04)
- ✅ 实现实时宏观数据获取
- ✅ 实现资金流向数据获取
- ✅ 实现新闻情绪分析
- ✅ 实现风险信号检测
- ✅ 实现动态市场状态判断
- ✅ 实现增强预测功能

---

## 📞 支持

如有问题或建议，请联系开发团队。
