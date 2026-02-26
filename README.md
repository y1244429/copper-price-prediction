# 铜价格预测模型

基于技术指标、基本面因素和市场情绪的综合铜价格预测模型。

## 功能特点

- 📊 **多维度分析**: 整合库存、技术面、基本面、情绪和宏观五大因子
- ⏱️ **多周期预测**: 支持短期(1-30天)、中期(1-6个月)、长期(1-3年)预测
- 🎯 **精准价位**: 提供支撑位、阻力位和价格区间
- 💡 **投资建议**: 基于模型结果给出交易策略建议
- 🌐 **Web界面**: 友好的可视化界面,支持API调用

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行Web应用

```bash
python copper_app.py
```

访问 http://localhost:5000 查看Web界面。

### 3. 使用Python库

```python
from copper_price_model import CopperPriceModel

# 初始化模型
model = CopperPriceModel()

# 短期预测(5天)
result = model.predict_short_term(days=5)
print(result)

# 中期预测(3个月)
result = model.predict_medium_term(months=3)
print(result)

# 长期预测(1年)
result = model.predict_long_term(years=1)
print(result)

# 市场评估
assessment = model.get_market_assessment()
print(assessment)
```

## API接口

### 短期预测

```
GET /api/short?days=5
```

**参数**:
- `days`: 预测天数,可选值: 5, 10, 15, 20, 30

**返回示例**:
```json
{
  "period": "5天",
  "current_price": 103040,
  "predicted_price": 102815.5,
  "predicted_change": -0.22,
  "trend": "下跌",
  "support": {
    "支撑1": 100979.2,
    "支撑2": 98918.4
  },
  "resistance": {
    "阻力1": 105100.8,
    "阻力2": 107161.6
  },
  "recommendation": "区间操作"
}
```

### 中期预测

```
GET /api/medium?months=3
```

**参数**:
- `months`: 预测月数,可选值: 1, 3, 6

### 长期预测

```
GET /api/long?years=1
```

**参数**:
- `years`: 预测年数,可选值: 1, 2, 3

### 市场评估

```
GET /api/assessment
```

### 综合预测

```
GET /api/all
```

返回所有预测结果和市场评估。

## 模型说明

### 评分系统

模型使用五大因子进行综合评分:

1. **库存得分** (30%): 库存变化率,增加为负分,减少为正分
2. **技术面得分** (25%): 均线排列、价格位置等技术指标
3. **基本面得分** (25%): 供需关系、季节性因素、新兴需求
4. **情绪得分** (10%): 机构观点、交易员情绪、持仓情况
5. **宏观得分** (10%): 货币政策、关税政策、经济增速

### 预测逻辑

- **短期**: 以技术面和库存为主,关注区间震荡
- **中期**: 以基本面为主,考虑季节性(Q2旺季)
- **长期**: 以结构性因素为主,能源转型+AI基建驱动

## 使用示例

### 使用curl调用API

```bash
# 短期预测
curl http://localhost:5000/api/short?days=5

# 中期预测
curl http://localhost:5000/api/medium?months=3

# 长期预测
curl http://localhost:5000/api/long?years=1

# 市场评估
curl http://localhost:5000/api/assessment

# 综合预测
curl http://localhost:5000/api/all
```

### 使用Python调用API

```python
import requests

# 短期预测
response = requests.get('http://localhost:5000/api/short?days=5')
result = response.json()
print(result)

# 综合预测
response = requests.get('http://localhost:5000/api/all')
result = response.json()
print(result)
```

### 使用JavaScript调用API

```javascript
// 短期预测
fetch('http://localhost:5000/api/short?days=5')
  .then(response => response.json())
  .then(data => console.log(data));

// 综合预测
fetch('http://localhost:5000/api/all')
  .then(response => response.json())
  .then(data => console.log(data));
```

## 风险提示

⚠️ **重要提示**:
1. 本模型仅供参考,不构成投资建议
2. 实际市场波动可能超出模型预测范围
3. 请结合市场实际情况做出投资决策
4. 投资有风险,入市需谨慎

## 技术支持

如有问题或建议,请通过以下方式联系:
- 提交Issue
- 发送邮件反馈

## 更新日志

### v1.0.0 (2026-02-26)
- 初始版本发布
- 支持短期、中期、长期预测
- 提供Web界面和API接口
