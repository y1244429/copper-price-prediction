# 真实数据接入完成报告

## ✅ 完成内容

### 1. 新增数据源模块 (`data/real_data.py`)

#### 支持的数据源

| 数据源 | 类型 | 状态 | 说明 |
|--------|------|------|------|
| **AKShare** | 国内期货 | ✅ 可用 | 沪铜连续(CU0)、库存、PMI |
| **Yahoo Finance** | 国际期货 | ✅ 可用 | 美铜期货(HG=F)、美元指数 |
| **Web Scraping** | 备用 | ⚠️ 需维护 | SMM现货价格(需适配) |

#### 数据源管理器 (`RealDataManager`)
- 多源数据整合
- 自动故障切换 (AKShare → Yahoo → 模拟)
- 1小时数据缓存
- 实时价格获取

### 2. 使用真实数据

```python
from main import CopperPredictionSystem

# 自动检测可用数据源
system = CopperPredictionSystem(data_source='auto')
# 或指定数据源
system = CopperPredictionSystem(data_source='akshare')
system = CopperPredictionSystem(data_source='yahoo')

# 加载真实数据
data = system.load_data(days=365)
```

### 3. 数据字段

真实数据包含：
```
价格数据: open, high, low, close, volume
持仓数据: hold, settle
宏观数据: china_pmi, dollar_index (可选)
库存数据: shfe_inventory (可选)
```

## 📊 测试结果

### 最新真实数据
```
日期: 2026-02-26
沪铜价格: ¥102,670.00/吨
数据来源: AKShare (上海期货交易所)
```

### 预测结果
```
短期 (5天):  ¥102,742.71 (+0.07%)
中期 (30天): ¥103,106.23 (+0.42%)
```

## 🔧 数据源API

### AKShare 支持的数据
```python
# 期货价格
df = ak.futures_zh_daily_sina(symbol="CU0")  # 沪铜连续

# 库存数据
df = ak.futures_inventory_99(symbol="cu")

# 宏观数据
df = ak.macro_china_pmi()  # 制造业PMI
df = ak.macro_china_cpi()  # CPI数据

# 汇率
df = ak.currency_boc_safe(symbol='USD')  # 美元兑人民币
```

### Yahoo Finance 支持的数据
```python
# 美铜期货
df = yf.Ticker("HG=F").history(period="1y")

# 美元指数
df = yf.Ticker("DX-Y.NYB").history(period="1y")

# 黄金(铜金比)
df = yf.Ticker("GC=F").history(period="1y")

# 铜ETF (投资情绪)
df = yf.Ticker("CPER").history(period="1y")
```

## ⚠️ 注意事项

### 1. 数据限制
- AKShare: 国内期货数据，无需翻墙
- Yahoo Finance: 国际数据，可能需要翻墙
- API限流: Yahoo有请求频率限制

### 2. 数据缺失处理
系统会自动处理缺失数据：
- 前向填充 (ffill)
- 后向填充 (bfill)
- 多源数据互补

### 3. 网络问题
如果数据源不可用，系统会：
1. 尝试其他数据源
2. 回退到模拟数据
3. 记录错误日志

## 📦 安装依赖

```bash
# 国内数据源
pip install akshare

# 国际数据源  
pip install yfinance

# 网页抓取 (可选)
pip install requests beautifulsoup4

# 完整安装
pip install akshare yfinance requests beautifulsoup4
```

## 🚀 使用示例

### 获取实时价格
```python
from data.real_data import RealDataManager

manager = RealDataManager()
price = manager.get_realtime_price()
print(price)
# {'sources': {'akshare': {'price': 102670.0, ...}}}
```

### 获取历史数据
```python
# 获取最近90天数据
data = manager.get_full_data(days=90)

# 清除缓存
data = manager.get_full_data(days=90, use_cache=False)
```

### 命令行使用
```bash
# 使用真实数据运行演示
python main.py --demo --data-source=auto

# 指定AKShare
python main.py --demo --data-source=akshare

# 指定Yahoo Finance
python main.py --demo --data-source=yahoo
```

## 📈 数据质量

| 指标 | 真实数据 | 模拟数据 |
|------|----------|----------|
| 价格精度 | ✅ 实际成交 | 模拟生成 |
| 实时性 | ✅ T+0 | 历史回溯 |
| 宏观指标 | ✅ 官方发布 | 随机生成 |
| 库存数据 | ✅ 交易所公布 | 模拟生成 |
| 可用性 | 依赖网络 | 本地可用 |

## 🎯 下一步建议

1. **添加更多数据源**
   - Wind API (付费)
   - Bloomberg API (付费)
   - 交易所直连

2. **数据持久化**
   - 数据库存储 (PostgreSQL/InfluxDB)
   - 增量更新机制
   - 数据质量监控

3. **实时数据流**
   - WebSocket接入
   - 分钟级数据
   - 实时预警系统
