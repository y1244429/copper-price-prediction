# 铜价预测系统 - 定时任务配置完成

## ✅ 配置成功

铜价预测系统已配置为每天早上 **9:20** 自动运行！

---

## 📋 配置详情

| 项目 | 内容 |
|------|------|
| **运行时间** | 每天 09:20 |
| **项目目录** | `/Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2` |
| **运行脚本** | `run_scheduled_prediction.sh` |
| **日志目录** | `logs/` |
| **执行模型** | 技术分析 + 宏观因子 + 基本面（全部模型） |

---

## 🔄 定时任务内容

```cron
20 9 * * * cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2 && /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/run_scheduled_prediction.sh >> /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/logs/cron.log 2>&1
```

**说明**：
- 每天早上 9:20 运行一次
- 切换到项目目录
- 执行预测脚本
- 输出日志到 `logs/cron.log`

---

## 📊 运行内容

定时任务会自动执行以下内容：

1. **技术分析模型 (XGBoost)**
   - 短期预测（5天）
   - 基于价格、成交量、技术指标

2. **宏观因子模型 (ARDL)**
   - 中期预测（1-6个月）
   - 基于美元指数、通胀、PMI等

3. **基本面模型 (VAR)**
   - 长期预测（6个月+）
   - 基于供需、库存、产能等

4. **生成报告**
   - 文本报告 (`.txt`)
   - HTML报告 (`.html`)
   - PPT报告 (`.pptx`)

---

## 📁 查看日志

### 查看完整日志
```bash
tail -f /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/logs/cron.log
```

### 查看每日运行日志
```bash
# 列出所有日志文件
ls -lh /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/logs/

# 查看最新日志
cat /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/logs/scheduled_run_*.log | tail -100
```

### 查看定时任务状态
```bash
# 查看所有定时任务
crontab -l

# 查看铜价预测定时任务
crontab -l | grep copper
```

---

## 🔧 管理定时任务

### 修改运行时间
```bash
# 编辑定时任务
crontab -e

# 找到铜价预测那行，修改时间
# 格式: 分 时 日 月 周
# 例如改成早上8:30: "30 8 * * * ..."
```

### 暂停定时任务
```bash
# 方法1: 注释掉任务
crontab -e
# 在任务行前加 #
# #20 9 * * * ...

# 方法2: 删除任务
crontab -e
# 删除铜价预测那行
```

### 恢复定时任务
```bash
# 重新配置
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
./setup_cron_copper.sh
```

---

## 🚀 手动运行

如果需要立即运行预测（不等待定时任务）：

```bash
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
./run_scheduled_prediction.sh
```

或者直接运行 Python 脚本：

```bash
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
python main.py --demo --data-source auto
```

---

## 📱 访问预测结果

### Web界面
1. 启动 Web 服务器：
   ```bash
   cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
   python app.py
   ```

2. 访问地址：
   - 本地访问：http://localhost:8002
   - 局域网访问：http://<你的IP地址>:8002

### 查看生成的报告
```bash
# 查看报告列表
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
ls -lh report_*.txt report_*.html report_*.pptx

# 查看最新文本报告
cat report_*.txt | head -100
```

---

## 📅 时间安排建议

### 完整的自动化时间表

| 时间 | 任务 | 说明 |
|------|------|------|
| 09:15 | 抓取财经新闻 | 获取市场最新动态 |
| **09:20** | **铜价预测** | **运行多模型预测分析** |
| 09:30 | 查看结果 | 查看预测报告和新闻 |

这样安排可以让您在开盘前完成所有分析工作！

---

## ⚠️ 注意事项

1. **系统需保持运行**
   - 定时任务需要在 Mac 运行时才能执行
   - 确保电脑在 9:20 前已启动

2. **网络连接**
   - 确保网络连接正常
   - 如果使用真实数据源（AKShare），需要访问互联网

3. **磁盘空间**
   - 定期清理旧的日志文件
   - 定期清理旧的报告文件

4. **Python环境**
   - 确保依赖已安装：`pip install -r requirements.txt`
   - 如有虚拟环境，脚本会自动激活

---

## 🔍 故障排除

### 任务没有运行
```bash
# 1. 检查定时任务是否配置
crontab -l | grep copper

# 2. 检查日志文件
tail -100 /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/logs/cron.log

# 3. 检查脚本权限
ls -l /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/run_scheduled_prediction.sh
```

### 运行失败
```bash
# 1. 查看错误日志
tail -100 /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/logs/scheduled_run_*.log

# 2. 手动运行测试
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
./run_scheduled_prediction.sh
```

---

## 📞 快速命令参考

```bash
# 查看定时任务
crontab -l | grep copper

# 查看实时日志
tail -f /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/logs/cron.log

# 手动运行预测
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
./run_scheduled_prediction.sh

# 查看最新报告
ls -lt /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2/report_*.txt | head -1

# 启动Web服务器
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
python app.py
```

---

## 🎉 配置完成！

铜价预测系统现在会在每天早上 **9:20** 自动运行，生成最新的预测报告！

**下次运行时间：明天 09:20**
