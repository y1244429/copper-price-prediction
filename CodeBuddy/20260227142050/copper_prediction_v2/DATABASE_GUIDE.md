# 铜价预测系统 - 数据库存储功能

## 📋 功能概述

铜价预测系统现在支持将预测结果自动保存到SQLite数据库，方便历史数据查询和分析。

**主要功能:**
- ✅ 自动保存每次预测结果到数据库
- ✅ 支持按日期查询历史预测
- ✅ Web界面一键保存最新预测
- ✅ 支持导出为CSV格式
- ✅ 数据库统计信息查询

---

## 🚀 快速开始

### 1. 自动保存（推荐）

系统在运行预测时会**自动保存**结果到数据库，无需额外操作。

```bash
# 运行预测（自动保存）
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
python main.py --demo --data-source real
```

预测完成后，结果会自动保存到 `data/predictions.db`。

### 2. Web界面一键保存

如果您已经运行过预测，可以通过Web界面保存最新结果：

1. 启动Web服务器：
```bash
python app.py
```

2. 访问 http://localhost:8001

3. 点击 **"💾 保存预测结果到数据库"** 按钮

---

## 📊 数据库结构

### 表1: predictions (预测结果主表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键ID |
| prediction_date | TEXT | 预测日期（唯一索引） |
| run_time | TEXT | 运行时间 |
| current_price | REAL | 当前价格 |
| xgboost_5day | REAL | XGBoost 5天预测 |
| xgboost_10day | REAL | XGBoost 10天预测 |
| xgboost_20day | REAL | XGBoost 20天预测 |
| macro_1month | REAL | 宏观模型1个月预测 |
| macro_3month | REAL | 宏观模型3个月预测 |
| macro_6month | REAL | 宏观模型6个月预测 |
| fundamental_6month | REAL | 基本面模型6个月预测 |
| lstm_5day | REAL | LSTM 5天预测 |
| lstm_10day | REAL | LSTM 10天预测 |
| overall_trend | TEXT | 总体趋势 |
| confidence | REAL | 置信度 |
| risk_level | TEXT | 风险等级 |
| notes | TEXT | 备注 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### 表2: technical_indicators (技术指标)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键ID |
| prediction_date | TEXT | 预测日期（外键） |
| ma5, ma10, ma20, ma60 | REAL | 移动平均线 |
| rsi | REAL | 相对强弱指标 |
| macd, macd_signal | REAL | MACD指标 |
| volume_ratio | REAL | 量比 |
| support_level | REAL | 支撑位 |
| resistance_level | REAL | 压力位 |

### 表3: macro_factors (宏观因子)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键ID |
| prediction_date | TEXT | 预测日期（外键） |
| usd_index | REAL | 美元指数 |
| vix | REAL | 波动率指数 |
| china_pmi, us_pmi | REAL | PMI指数 |
| oil_price, gold_price | REAL | 油价、金价 |
| global_demand | TEXT | 全球需求 |

### 表4: model_performance (模型性能)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键ID |
| prediction_date | TEXT | 预测日期（外键） |
| model_name | TEXT | 模型名称 |
| accuracy | REAL | 准确率 |
| mae, rmse | REAL | 误差指标 |
| r2_score | REAL | R²分数 |

### 表5: prediction_details (预测详情JSON)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键ID |
| prediction_date | TEXT | 预测日期（外键） |
| detail_type | TEXT | 详情类型 |
| detail_json | TEXT | JSON格式详情 |

---

## 🔧 使用方法

### Python API

```python
from data.prediction_db import PredictionDatabase

# 初始化数据库
db = PredictionDatabase()

# 保存预测结果
prediction_data = {
    'prediction_date': '2026-03-03',
    'run_time': '2026-03-03 10:30:00',
    'current_price': 85000.0,
    'xgboost_5day': 85500.0,
    'overall_trend': '上涨',
    'confidence': 0.75,
    'risk_level': '中风险',
    # ... 更多字段
}
success = db.save_prediction(prediction_data)

# 获取指定日期的预测
prediction = db.get_prediction('2026-03-03')

# 获取所有预测（最近30条）
all_predictions = db.get_all_predictions(limit=30)

# 获取最新预测
latest = db.get_latest_prediction()

# 导出为CSV
csv_path = db.export_to_csv()
```

### Web API

```bash
# 保存最新预测到数据库
curl -X POST http://localhost:8001/db/save-latest

# 获取预测历史
curl "http://localhost:8001/db/history?limit=30"

# 获取最新预测
curl http://localhost:8001/db/latest

# 获取数据库统计
curl http://localhost:8001/db/statistics

# 导出为CSV
curl "http://localhost:8001/db/export?start_date=2026-03-01&end_date=2026-03-31" -o predictions.csv
```

### 数据库管理工具

```bash
# 进入SQLite数据库
sqlite3 data/predictions.db

# 查看所有表
.tables

# 查看预测结果
SELECT * FROM predictions ORDER BY prediction_date DESC LIMIT 10;

# 查询特定日期的预测
SELECT * FROM predictions WHERE prediction_date = '2026-03-03';

# 统计预测次数
SELECT COUNT(*) FROM predictions;

# 退出SQLite
.quit
```

---

## 📈 数据分析示例

### 查询最近7天的预测趋势

```sql
SELECT
    prediction_date,
    current_price,
    xgboost_5day,
    macro_3month,
    fundamental_6month,
    overall_trend
FROM predictions
WHERE prediction_date >= date('now', '-7 days')
ORDER BY prediction_date;
```

### 计算预测准确率（假设有实际价格）

```sql
SELECT
    AVG(ABS((current_price - xgboost_5day) / current_price * 100)) as avg_error_pct
FROM predictions
WHERE xgboost_5day IS NOT NULL;
```

### 查看风险等级分布

```sql
SELECT
    risk_level,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM predictions
GROUP BY risk_level;
```

---

## 🔍 故障排除

### 问题1: 数据库文件不存在

**症状:** 提示"数据库文件不存在"

**解决方案:**
```bash
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/data
ls -la predictions.db

# 如果不存在，运行一次预测会自动创建
python main.py --demo --data-source mock
```

### 问题2: 保存失败

**症状:** 点击保存按钮提示"保存失败"

**解决方案:**
1. 检查是否有最新的预测报告文件（report_*.txt）
2. 查看浏览器控制台的错误信息
3. 检查文件权限

### 问题3: 数据库锁定

**症状:** 提示"database is locked"

**解决方案:**
```bash
# 关闭所有数据库连接
# 等待几秒钟后重试
# 或重启Flask服务器
```

---

## 📝 最佳实践

### 1. 定期备份

```bash
# 备份数据库
cp data/predictions.db data/predictions_backup_$(date +%Y%m%d).db

# 导出CSV备份
python3 -c "
from data.prediction_db import PredictionDatabase
db = PredictionDatabase()
db.export_to_csv()
"
```

### 2. 定期清理旧数据

```sql
-- 删除6个月前的数据
DELETE FROM predictions WHERE prediction_date < date('now', '-6 months');

-- 压缩数据库
VACUUM;
```

### 3. 性能优化

```sql
-- 创建索引（已自动创建）
CREATE INDEX IF NOT EXISTS idx_prediction_date ON predictions(prediction_date);
CREATE INDEX IF NOT EXISTS idx_run_time ON predictions(run_time);

-- 分析查询计划
EXPLAIN QUERY PLAN SELECT * FROM predictions WHERE prediction_date = '2026-03-03';
```

---

## 🎯 使用场景

### 场景1: 每日自动保存

在定时任务中，每天早上9:20自动运行预测并保存：

```bash
# cron任务配置
20 9 * * * cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2 && \
    /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/run_scheduled_prediction.sh
```

预测结果会自动保存到数据库。

### 场景2: 手动运行预测并保存

通过Web界面运行预测，完成后点击"保存到数据库"按钮。

### 场景3: 查询历史预测

```python
from data.prediction_db import PredictionDatabase

db = PredictionDatabase()

# 查询最近10次预测
predictions = db.get_all_predictions(limit=10)

for pred in predictions:
    print(f"日期: {pred['prediction_date']}, 价格: {pred['current_price']}")
```

---

## 📞 获取帮助

如有问题，请检查：
1. 日志文件: `logs/scheduled_run_*.log`
2. 数据库文件: `data/predictions.db`
3. Web界面控制台错误信息

---

**配置完成！每次运行预测后，结果会自动保存到数据库。** 🎉
