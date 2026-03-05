# 铜价预测系统 - 腾讯云部署完成

## ✅ 部署准备完成

我已经为您准备好了完整的腾讯云部署方案！

---

## 📦 创建的文件

| 文件 | 说明 |
|------|------|
| `deploy_to_tencentcloud.sh` | **一键部署脚本**（推荐使用） |
| `deploy_tencentcloud.md` | 详细部署指南（包含所有步骤） |
| `DEPLOY_TENCENTCLOUD_QUICKSTART.md` | 快速开始指南 |

---

## 🚀 快速部署（3步）

### 步骤1: 购买服务器

1. 访问：https://cloud.tencent.com/product/lighthouse
2. 选择配置：
   - **镜像**: Ubuntu 22.04 LTS
   - **规格**: 2核4GB（推荐）
   - **带宽**: 5Mbps
3. 购买并记录服务器IP地址

### 步骤2: 运行一键部署脚本

**在本地电脑执行**：

```bash
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
./deploy_to_tencentcloud.sh <服务器IP>
```

**示例**：
```bash
./deploy_to_tencentcloud.sh 123.45.67.89
```

### 步骤3: 访问应用

部署完成后，在浏览器访问：
```
http://<服务器IP>
```

---

## 📋 一键部署脚本功能

`deploy_to_tencentcloud.sh` 脚本会自动完成：

✅ **环境配置**
- 更新系统
- 安装Python、pip、virtualenv
- 安装Nginx（Web服务器）
- 安装Supervisor（进程管理）

✅ **项目部署**
- 创建项目目录
- 配置Python虚拟环境
- 安装所有依赖包
- 上传项目文件

✅ **服务配置**
- 配置Gunicorn（生产服务器）
- 配置Supervisor（进程守护）
- 配置Nginx（反向代理）
- 配置防火墙（UFW）

✅ **定时任务**
- 配置每天9:20自动运行
- 创建日志目录
- 配置日志轮转

---

## 🎯 推荐配置

### 服务器配置

| 项目 | 配置 |
|------|------|
| **镜像** | Ubuntu 22.04 LTS |
| **规格** | 2核4GB |
| **带宽** | 5Mbps |
| **数据盘** | 40GB（可选） |
| **价格** | 约 ¥50-100/月 |

### 定时任务配置

| 任务 | 时间 |
|------|------|
| **财经新闻抓取** | 每天 09:15 |
| **铜价预测** | 每天 09:20 |

---

## 📱 访问地址

部署成功后，可以通过以下方式访问：

### Web界面
```
http://<服务器IP>
```

### API接口
```
http://<服务器IP>/run
http://<服务器_IP>/risk-alerts
```

---

## 🔧 部署后管理

### 查看应用状态

```bash
ssh root@<服务器_IP>
supervisorctl status copper-prediction
```

### 重启应用

```bash
ssh root@<服务器_IP>
supervisorctl restart copper-prediction
```

### 查看日志

```bash
ssh root@<服务器_IP>
tail -f /opt/copper-prediction/logs/supervisor_stdout.log
```

### 查看定时任务

```bash
ssh root@<服务器_IP>
crontab -l
```

---

## 📊 定时任务说明

### 铜价预测任务

- **运行时间**: 每天 09:20
- **执行内容**: 技术分析 + 宏观因子 + 基本面模型
- **生成报告**: 文本 + HTML + PPT
- **日志位置**: `/opt/copper-prediction/logs/`

### 查看定时任务日志

```bash
ssh root@<服务器_IP>
tail -f /opt/copper-prediction/logs/scheduled_run_*.log
```

---

## ⚠️ 重要提示

### 1. 安全组配置

在腾讯云控制台，确保开放以下端口：
- **22**: SSH（必须）
- **80**: HTTP（Web访问）
- **443**: HTTPS（可选，用于SSL）

### 2. 防火墙配置

脚本会自动配置UFW防火墙，开放必要的端口。

### 3. 定时任务时间

当前配置为早上9:20运行。如需修改，可编辑服务器上的定时任务：
```bash
ssh root@<服务器_IP>
crontab -e
```

### 4. 数据备份

建议定期备份重要数据：
```bash
ssh root@<服务器_IP>
tar -czf /backup/copper-prediction-$(date +%Y%m%d).tar.gz /opt/copper-prediction
```

---

## 💰 成本估算

| 项目 | 价格 |
|------|------|
| 轻量服务器 (2核4GB) | ~¥50-100/月 |
| 流量 | 免费额度内 |
| SSL证书 | 免费（Let's Encrypt） |
| 域名（可选） | ~¥50/年 |

**月成本**: 约 ¥50-100

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| `deploy_to_tencentcloud.sh` | 一键部署脚本 |
| `DEPLOY_TENCENTCLOUD_QUICKSTART.md` | 快速开始指南 |
| `deploy_tencentcloud.md` | 详细部署文档 |
| `COPPER_SCHEDULE_GUIDE.md` | 定时任务指南 |

---

## 🔍 故障排除

### SSH连接失败

1. 检查服务器IP是否正确
2. 检查服务器是否正在运行
3. 检查SSH端口(22)是否开放
4. 检查防火墙设置

### 应用无法启动

```bash
ssh root@<服务器_IP>
supervisorctl tail -f copper-prediction stderr
```

### 端口无法访问

1. 检查UFW防火墙：`ufw status`
2. 检查Nginx状态：`systemctl status nginx`
3. 在腾讯云控制台检查安全组

### 定时任务不运行

```bash
ssh root@<服务器_IP>
grep CRON /var/log/syslog
```

---

## 📞 快速命令参考

```bash
# SSH登录
ssh root@<服务器_IP>

# 查看应用状态
ssh root@<服务器_IP> "supervisorctl status copper-prediction"

# 重启应用
ssh root@<服务器_IP> "supervisorctl restart copper-prediction"

# 查看日志
ssh root@<服务器_IP> "tail -f /opt/copper-prediction/logs/supervisor_stdout.log"

# 查看定时任务
ssh root@<服务器_IP> "crontab -l"

# 查看定时任务日志
ssh root@<服务器_IP> "tail -f /opt/copper-prediction/logs/cron.log"
```

---

## 🎉 开始部署

### 方法1: 一键部署（推荐）

```bash
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
./deploy_to_tencentcloud.sh <服务器IP>
```

### 方法2: 手动部署

查看详细文档：
```bash
cat DEPLOY_TENCENTCLOUD_QUICKSTART.md
```

---

## 🎯 部署清单

- [ ] 购买腾讯云轻量应用服务器
- [ ] 获取服务器IP地址和密码
- [ ] 运行一键部署脚本
- [ ] 访问Web界面测试
- [ ] 查看定时任务状态
- [ ] 配置SSL证书（可选）
- [ ] 设置域名（可选）

---

## 📈 部署后架构

```
用户浏览器
    ↓
Nginx (端口80)
    ↓
Supervisor
    ↓
Gunicorn (4个工作进程)
    ↓
Flask应用 (端口8002)
    ↓
铜价预测系统 (技术+宏观+基本面)
```

---

## 🚀 部署成功标志

部署成功后，您将能够：

✅ 在浏览器中访问铜价预测系统
✅ 运行多模型预测分析
✅ 生成预测报告（文本、HTML、PPT）
✅ 每天9:20自动运行预测
✅ 查看实时日志和状态
✅ 远程管理应用

---

**部署准备完成！按照上述步骤，几分钟内即可完成部署！** 🎉
