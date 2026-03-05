# 铜价预测系统 - 数据库存储功能总结

## ✅ 已完成功能

### 1. 数据库模块 (`data/prediction_db.py`)
- ✅ SQLite数据库管理
- ✅ 5张表设计（预测结果、技术指标、宏观因子、模型性能、详情JSON）
- ✅ 完整的CRUD操作
- ✅ 支持按日期查询、导出CSV

### 2. 自动保存功能
- ✅ 运行预测后自动保存到数据库
- ✅ 以日期为主键，避免重复
- ✅ 支持更新已有日期的预测

### 3. Web界面功能
- ✅ "💾 保存预测结果到数据库" 按钮
- ✅ 实时显示保存状态
- ✅ 友好的成功/失败提示

### 4. Web API接口
- ✅ `/db/save-latest` - 保存最新预测
- ✅ `/db/history` - 获取历史记录
- ✅ `/db/latest` - 获取最新预测
- ✅ `/db/export` - 导出CSV
- ✅ `/db/statistics` - 获取统计信息

### 5. 文档和测试
- ✅ 完整使用指南 (`DATABASE_GUIDE.md`)
- ✅ 测试脚本 (`test_database.py`)
- ✅ 功能总结文档

---

## 📁 文件清单

### 新增文件
```
copper_prediction_v2/
├── data/
│   └── prediction_db.py           # 数据库模块
├── test_database.py               # 数据库测试脚本
├── DATABASE_GUIDE.md              # 使用指南
└── DATABASE_FEATURE_SUMMARY.md    # 功能总结
```

### 修改文件
```
copper_prediction_v2/
├── main.py                        # 添加自动保存功能
└── app.py                         # 添加保存按钮和API接口
```

### 数据库文件（运行后生成）
```
copper_prediction_v2/
├── data/
│   ├── predictions.db             # SQLite数据库文件
│   └── exports/                   # CSV导出目录
│       └── predictions_export_*.csv
```

---

## 🚀 使用方法

### 方法1: 自动保存（推荐）

```bash
# 运行预测，自动保存
python main.py --demo --data-source real
```

预测完成后，结果会自动保存到数据库。

### 方法2: Web界面保存

```bash
# 1. 启动Web服务器
python app.py

# 2. 访问 http://localhost:8001

# 3. 运行预测后，点击"💾 保存预测结果到数据库"按钮
```

### 方法3: Python API

```python
from data.prediction_db import PredictionDatabase

db = PredictionDatabase()

# 查询历史预测
predictions = db.get_all_predictions(limit=10)

# 获取最新预测
latest = db.get_latest_prediction()

# 导出为CSV
db.export_to_csv()
```

---

## 📊 数据库结构

### 主表: predictions

| 字段 | 说明 |
|------|------|
| prediction_date | 预测日期（主键） |
| current_price | 当前价格 |
| xgboost_5day/10day/20day | XGBoost预测 |
| macro_1month/3month/6month | 宏观模型预测 |
| fundamental_6month | 基本面预测 |
| overall_trend | 总体趋势 |
| confidence | 置信度 |
| risk_level | 风险等级 |

### 辅助表
- **technical_indicators** - 技术指标
- **macro_factors** - 宏观因子
- **model_performance** - 模型性能
- **prediction_details** - 详细预测数据（JSON）

---

## 🎯 关键特性

### 1. 自动去重
- 同一天多次预测会更新记录，不会重复
- 使用 `prediction_date` 作为唯一键

### 2. 数据完整性
- 保存完整预测结果
- 包含技术指标、宏观因子、模型性能
- JSON格式存储详细数据

### 3. 查询灵活
```sql
-- 查询最近7天
SELECT * FROM predictions
WHERE prediction_date >= date('now', '-7 days');

-- 查询特定日期
SELECT * FROM predictions
WHERE prediction_date = '2026-03-03';

-- 统计预测次数
SELECT COUNT(*) FROM predictions;
```

### 4. 导出方便
```bash
# Web API导出
curl "http://localhost:8001/db/export" -o predictions.csv

# Python导出
db.export_to_csv()

# SQLite导出
sqlite3 data/predictions.db ".dump" > backup.sql
```

---

## 🔍 测试结果

运行测试脚本：
```bash
python test_database.py
```

**测试结果:**
- ✅ 数据库初始化成功
- ✅ 保存测试数据成功
- ✅ 查询测试数据成功
- ✅ 获取最新预测成功
- ✅ 导出CSV成功

---

## 📈 应用场景

### 1. 每日定时预测保存
```bash
# cron任务（每天9:20运行）
20 9 * * * cd /path/to/copper_prediction_v2 && \
    ./run_scheduled_prediction.sh
```

每次运行后自动保存到数据库。

### 2. 历史数据分析
```python
# 查询最近30次预测
db = PredictionDatabase()
predictions = db.get_all_predictions(limit=30)

# 分析趋势
for pred in predictions:
    print(f"{pred['prediction_date']}: {pred['overall_trend']}")
```

### 3. 预测准确率评估
```sql
-- 计算平均误差
SELECT
    AVG(ABS((xgboost_5day - current_price) / current_price * 100))
    as avg_error_pct
FROM predictions
WHERE xgboost_5day IS NOT NULL;
```

---

## ⚠️ 注意事项

1. **数据库位置**
   - 默认路径: `data/predictions.db`
   - 建议定期备份数据库文件

2. **权限问题**
   - 确保有 `data/` 目录的写入权限
   - 如遇权限问题，运行 `chmod +x data/`

3. **并发问题**
   - SQLite不支持高并发写入
   - 定时任务之间保持合理间隔

4. **数据清理**
   - 建议定期清理6个月以上旧数据
   - 定期执行 `VACUUM` 命令压缩数据库

---

## 🎉 总结

**数据库存储功能已完全实现并测试通过！**

**主要特点:**
- ✅ 完全自动保存，无需手动操作
- ✅ Web界面一键保存
- ✅ 完整的历史数据查询
- ✅ 支持CSV导出
- ✅ 详细的文档和测试

**下一步建议:**
1. 运行一次预测，验证自动保存功能
2. 查看数据库内容，确认数据完整性
3. 根据需求调整查询和导出功能

---

**配置完成！每次运行预测后，结果会自动保存到数据库。** 🎉
