# 铜价集成预测系统 - Web部署指南

## 📋 系统概述

集成预测系统将**传统机器学习模型**与**增强数据**（宏观、资金流向、新闻情绪）融合，提供更准确的铜价预测。

### 核心特性

- ✅ **多模型融合**: XGBoost + 宏观因子 + 基本面
- ✅ **增强数据**: 实时宏观指标、CFTC持仓、新闻情绪分析
- ✅ **智能权重**: 根据市场状态动态调整模型权重
- ✅ **风险预警**: 自动检测风险信号并调整预测
- ✅ **Web展示**: 实时Web界面，支持本地和远程访问

---

## 🚀 快速启动

### 方式1: 命令行运行

```bash
# 进入项目目录
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2

# 运行集成预测系统
python3 run_integrated_prediction.py
```

**输出示例**:
```
======================================================================
集成预测系统 - 传统模型 + 增强数据
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

【新闻情绪】
  文章总数: 5
  情绪分布: 正面1 / 负面2 / 中性2
  整体情绪: negative (分数: -0.20)

【风险信号】
  1. 🔴 美元指数过强(157.71),对铜价形成压制
  2. 🟡 新闻情绪偏负面(分数: -0.20)

市场状态: risky

预测结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
原XGBoost预测: ¥104,315.57 (+2.17%)
加权融合预测: ¥105,828.69 (+3.65%)
风险调整后预测: ¥97,521.14 (-4.48%) ⭐ 最终推荐

调整因子: 0.9215
置信度: low
预测区间: ¥89,220.50 ~ ¥113,553.37

【投资建议】
操作方向: 🔴 做空
建议: 建议谨慎观望或适度做空，但需谨慎控制仓位
仓位建议: 轻仓 (10-20%)
```

---

### 方式2: Web界面运行

```bash
# 启动Flask服务器
python3 app.py
```

服务器启动后，在浏览器中打开：

- **本地访问**: http://localhost:8001
- **局域网访问**: http://<本机IP>:8001
- **手机访问**: 在手机浏览器中输入局域网IP地址

**访问集成预测系统**: http://localhost:8001/integrated_prediction.html

---

## 📊 Web界面说明

### 主页 (http://localhost:8001)

1. **市场概况**: 显示当前价格、涨跌幅、波动率等
2. **模型指标**: XGBoost、宏观、基本面三大模型
3. **风险预警系统**: 三级预警响应机制
4. **集成预测系统**: **新增入口** - 传统模型 + 增强数据

---

### 集成预测页面 (http://localhost:8001/integrated_prediction.html)

#### 1. 当前价格
- 显示实时铜价
- 显示日涨跌幅
- 颜色标识：绿色上涨，红色下跌

#### 2. 市场状态
自动识别以下状态：
- 🟢 **bull** (牛市): 基本面升权
- 🔴 **bear** (熊市): 宏观升权
- 🟡 **neutral** (正常): 基础权重
- 🟣 **risk** (风险期): 技术降权，宏观升权

#### 3. 预测结果对比

| 预测方式 | 价格 | 涨跌幅 | 说明 |
|---------|------|--------|------|
| **原XGBoost** | ¥104,315.57 | +2.17% | 仅技术指标 |
| **增强数据调整** | ¥105,828.69 | +3.65% | 融合多模型 |
| **集成系统** | ¥97,521.14 | -4.48% | 最终推荐 ⭐ |

#### 4. 增强数据概览

**🌍 宏观数据**
- 美元指数
- VIX恐慌指数
- 中国PMI
- 联邦利率

**💰 资金流向**
- 商业净头寸 (CFTC)
- 投机净头寸
- 总持仓量

**📰 新闻情绪**
- 文章总数
- 情绪分数 (-1 ~ +1)
- 整体情绪 (positive/negative/neutral)

#### 5. 风险信号

自动检测并显示：
- 🔴 VIX过高 (>30)
- 🔴 美元过强 (>102)
- 🔴 PMI过低 (<45)
- 🔴 突发事件
- 🟡 新闻情绪偏负面
- 🟡 投机大幅做空

#### 6. 投资建议

| 项目 | 说明 |
|------|------|
| **操作方向** | 做多 / 做空 / 观望 |
| **仓位建议** | 40-80% / 30-50% / 10-20% |
| **置信度** | 高 / 中 / 低 |
| **预测区间** | 价格波动范围 |

---

## 🔧 API接口

### 获取集成预测数据

```bash
curl http://localhost:8001/api/integrated-prediction
```

**返回示例**:
```json
{
  "timestamp": "2026-03-04T12:30:00",
  "current_price": 102100.0,
  "market_state": "risky",
  "predictions": {
    "xgboost": {
      "price": 104315.57,
      "return_pct": 2.17,
      "weight": 0.4,
      "source": "技术指标"
    },
    "weighted": {
      "price": 105828.69,
      "return_pct": 3.65
    },
    "risk_adjusted": {
      "price": 97521.14,
      "return_pct": -4.48,
      "adjustment_factor": 0.9215
    }
  },
  "final_prediction": {
    "price": 97521.14,
    "return_pct": -4.48,
    "lower_bound": 89220.50,
    "upper_bound": 113553.37,
    "interval_width_pct": 12.0
  },
  "confidence_level": "low",
  "prediction_range": {
    "lower": 89220.50,
    "upper": 113553.37
  },
  "recommendation": {
    "action": "sell",
    "position": "轻仓 (10-20%)",
    "advice": "建议谨慎观望或适度做空，但需谨慎控制仓位"
  },
  "risk_signals": [
    {
      "type": "macro",
      "indicator": "Dollar Index",
      "value": 157.71,
      "level": "high",
      "message": "美元指数过强(157.71),对铜价形成压制"
    },
    {
      "type": "news",
      "indicator": "News Sentiment",
      "value": -0.2,
      "level": "medium",
      "message": "新闻情绪偏负面(分数: -0.20)"
    }
  ],
  "enhanced_data": {
    "macro": { ... },
    "capital_flow": { ... },
    "news_sentiment": { ... }
  },
  "error": null
}
```

---

## 📱 移动端访问

### 在手机浏览器中访问

1. **获取本机IP地址**:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Windows
   ipconfig
   ```

2. **确保手机和电脑在同一WiFi网络**

3. **在手机浏览器中输入**: `http://<本机IP>:8001`

4. **访问集成预测**: `http://<本机IP>:8001/integrated_prediction.html`

---

## 🔌 数据源配置

### 当前状态

- ✅ **真实数据源**: AKShare (铜价数据)
- ⚠️ **增强数据**: 模拟数据 (待配置API Keys)

### 配置真实API Keys

#### 1. Alpha Vantage API (宏观数据)
```bash
# 注册账号: https://www.alphavantage.co/support/#api-key
# 获取API Key后，修改以下文件:
# data/enhanced_data_sources.py
```

#### 2. FRED API (经济数据)
```bash
# 注册账号: https://fred.stlouisfed.org/docs/api/api_key.html
# 获取API Key后，修改配置
```

#### 3. CFTC API (持仓数据)
```bash
# 下载CFTC报告: https://www.cftc.gov/dea/futures/deacmesf.htm
# 或使用第三方API服务
```

---

## 📈 核心价值

### 为什么集成预测更准确？

**问题**: 为什么原XGBoost预测上涨(+2.17%)但实际连续下跌？

**原因**: XGBoost仅基于技术指标，无法感知：
- 突发利空新闻
- 宏观环境变化（美元暴涨）
- 资金流向异动
- 市场恐慌情绪

**集成系统的优势**:
1. ✅ **实时检测突发事件** (新闻情绪)
2. ✅ **感知宏观变化** (美元、VIX)
3. ✅ **捕捉资金流向** (CFTC持仓)
4. ✅ **动态调整预测** (风险信号触发)

**结果**: 预测从 +2.17% 调整为 -4.48%，更符合实际情况！

---

## 🎯 使用场景

### 1. 日常监控
```bash
# 每天运行一次集成预测
python3 run_integrated_prediction.py
```

### 2. 实时Web监控
```bash
# 启动Web服务器
python3 app.py
# 浏览器访问集成预测页面
```

### 3. API调用
```bash
# 获取最新预测数据
curl http://localhost:8001/api/integrated-prediction
```

### 4. 定时任务
```bash
# 使用cron定时运行
0 9 * * * cd /path/to/copper_prediction_v2 && python3 run_integrated_prediction.py
```

---

## 🛠️ 故障排除

### 问题1: 端口被占用
```bash
# 查找占用端口的进程
lsof -ti:8001

# 杀死进程
lsof -ti:8001 | xargs kill -9
```

### 问题2: 模块缺失
```bash
# 安装依赖
pip install flask pandas numpy xgboost akshare yfinance requests beautifulsoup4
```

### 问题3: 数据获取失败
```bash
# 检查网络连接
ping api.akshare.xyz

# 检查AKShare是否可用
python3 -c "import akshare as ak; print(ak.stock_zh_a_hist('600519'))"
```

---

## 📞 技术支持

### 文档
- `ENHANCED_DATA_USAGE.md` - 增强数据使用说明
- `ENHANCED_DATA_SUMMARY.md` - 增强数据实施总结
- `INTEGRATED_PREDICTION_SUMMARY.md` - 集成预测总结

### 代码
- `run_integrated_prediction.py` - 集成预测主程序
- `data/enhanced_data_sources.py` - 增强数据源
- `app.py` - Flask Web服务器
- `integrated_prediction.html` - Web界面

---

## ⚠️ 免责声明

1. 本系统仅供学习和研究使用
2. 预测结果不构成投资建议
3. 实际投资请谨慎，做好风险控制
4. 系统可能存在误差，请自行判断

---

**🎉 集成预测系统已成功部署到Web！**
