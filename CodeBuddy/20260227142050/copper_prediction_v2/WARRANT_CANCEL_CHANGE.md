# LME 注销仓单占比变化功能

## 功能概述

已实现 LME 注销仓单占比变化的监控和分析功能，包括：
- 历史趋势分析
- 变化幅度计算
- 趋势判断（稳定/上升/下降）
- 风险预警集成
- RESTful API 接口

## 实现内容

### 1. 数据层 (`data/inventory_data.py`)

#### 新增方法

**`InventoryManager.get_warrant_cancel_change(days=7)`**

获取注销仓单占比变化情况，返回数据包括：

- `current_value`: 当前值 (%)
- `previous_value`: 过去值 (%)
- `absolute_change`: 绝对变化
- `percentage_change`: 百分比变化 (%)
- `trend`: 趋势描述（稳定/上升/下降）
- `trend_emoji`: 趋势图标
- `change_level`: 变化等级（平稳/小幅波动/显著变化/大幅变化/极端波动）
- `days_ago`: 对比天数
- `ma5`: 5日均线 (%)
- `ma5_change`: 5日均线变化 (%)
- `history_data`: 最近N天历史数据数组
- `date_range`: 日期范围

**`InventoryManager.get_historical_data(days=30, force_refresh=False)`**

获取历史库存数据（包含注销仓单占比），增加了缓存机制。

### 2. 预警系统 (`models/risk_alert_system.py`)

#### 更新预警逻辑

在 `calculate_inventory_alerts` 方法中增加了基于注销仓单占比变化的预警：

- **三级预警（紧急级）**：
  - 注销仓单占比7天内上升超过10%且当前值>40%
  - 触发条件：挤仓风险快速上升

- **二级预警（警戒级）**：
  - 注销仓单占比7天内上升超过5%且当前值>30%
  - 5日均线快速上升超过5%且当前值>35%
  - 触发条件：交割压力增加，短期趋势恶化

- **一级预警（关注级）**：
  - 注销仓单占比7天内小幅上升超过2%且当前值>阈值
  - 注销仓单占比大幅下降超过15%（可能意味着缓解）

### 3. API 层 (`app.py`)

#### 新增路由

**`GET /warrant-cancel/change?days=7`**

获取注销仓单占比变化情况。

参数：
- `days`: 对比天数，默认7天

返回示例：
```json
{
  "available": true,
  "indicator_name": "LME注销仓单占比",
  "current_value": 58.12,
  "previous_value": 45.0,
  "absolute_change": 13.12,
  "percentage_change": 29.16,
  "trend": "上升",
  "trend_emoji": "📈",
  "change_level": "极端波动",
  "days_ago": 7,
  "ma5": 34.46,
  "ma5_change": 68.67,
  "history_data": [
    {
      "date": "2026-02-21",
      "value": 45.0,
      "days_ago": 7
    },
    ...
  ],
  "date_range": {
    "from": "2026-02-21",
    "to": "2026-02-28"
  }
}
```

#### 更新路由

**`GET /risk-alerts`**
- 添加了注销仓单占比变化数据到库存数据中

**`GET /checklists`**
- 添加了注销仓单占比变化数据到库存信息中

## 风险预警规则

### 预警级别判定

1. **三级预警（紧急级）**：
   - 注销仓单占比 > 70%（绝对值）
   - 或 7天变化 > 10% 且当前值 > 40%

2. **二级预警（警戒级）**：
   - 注销仓单占比 > 50%（绝对值）
   - 或 7天变化 > 5% 且当前值 > 30%
   - 或 5日均线变化 > 5% 且当前值 > 35%

3. **一级预警（关注级）**：
   - 7天变化 > 2% 且当前值 > 阈值
   - 或 大幅下降 > 15%（缓解信号）

### 变化等级划分

- **平稳**：< 2%
- **小幅波动**：2-5%
- **显著变化**：5-10%
- **大幅变化**：10-20%
- **极端波动**：> 20%

## 测试

### 运行测试脚本

```bash
python test_warrant_cancel.py
```

测试内容：
1. 获取7天注销仓单占比变化
2. 获取30天注销仓单占比变化
3. 查看历史数据点
4. 测试风险预警集成

### 测试 API

```bash
# 启动服务器
python app.py

# 在另一个终端测试
python test_warrant_api.py
```

或直接使用 curl：
```bash
# 获取7天变化
curl "http://localhost:5000/warrant-cancel/change?days=7"

# 获取30天变化
curl "http://localhost:5000/warrant-cancel/change?days=30"
```

## 使用示例

### Python 代码

```python
from data.inventory_data import InventoryManager

# 创建库存管理器
inventory_mgr = InventoryManager('auto')

# 获取7天注销仓单占比变化
change_data = inventory_mgr.get_warrant_cancel_change(days=7)

if change_data['available']:
    print(f"当前值: {change_data['current_value']}%")
    print(f"变化: {change_data['percentage_change']}%")
    print(f"趋势: {change_data['trend']}")
    print(f"变化等级: {change_data['change_level']}")
```

### 风险预警

```python
from models.risk_alert_system import CopperRiskMonitor

# 创建监控器
monitor = CopperRiskMonitor()

# 创建库存数据（包含注销仓单变化）
inventory_dict = {
    'lme_inventory': 260000,
    'comex_inventory': 80000,
    'shfe_inventory': 150000,
    'lme_warrant_cancel_ratio': 58.12,
    'warrant_cancel_change': warrant_change_data
}

# 计算库存预警
alerts = monitor.calculate_inventory_alerts(inventory_dict)

for alert in alerts:
    print(f"{alert.alert_level.get_label()}: {alert.message}")
```

## 数据说明

### 历史数据生成

当前实现使用模拟历史数据，具有以下特点：
- 注销仓单占比呈正弦波动趋势（15-75%之间）
- 5日均线反映短期趋势
- 支持缓存（1小时TTL）

### 真实数据接入

如需接入真实 LME 数据，需要：
1. 申请 LME Select API 访问权限
2. 实现 `LMEInventorySource.fetch_inventory_data()` 方法
3. 从 LME API 获取真实的注销仓单数据

## 注意事项

1. **数据可用性**：当 AKShare 未安装时，系统自动使用模拟数据
2. **缓存机制**：历史数据缓存1小时，提高性能
3. **异常处理**：当数据不可用时返回 `available: False`
4. **多数据结构兼容**：支持 `summary` 和 `data` 两种数据结构

## 后续改进

1. 接入真实的 LME 注销仓单数据源
2. 增加更细粒度的预警规则
3. 添加图表可视化
4. 增加实时推送功能
5. 历史数据持久化存储
