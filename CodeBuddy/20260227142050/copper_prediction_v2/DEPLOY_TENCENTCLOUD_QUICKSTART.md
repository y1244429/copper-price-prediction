# 铜价预测系统 - 腾讯云快速部署指南

## 🚀 三步完成部署

### 第1步：购买服务器

1. 访问：https://cloud.tencent.com/product/lighthouse
2. 选择配置：
   - **镜像**: Ubuntu 22.04 LTS
   - **规格**: 2核4GB（推荐）
   - **带宽**: 5Mbps
3. 购买并获取服务器IP地址

### 第2步：运行一键部署脚本

**在本地电脑执行**：

```bash
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2

# 运行部署脚本
./deploy_to_tencentcloud.sh <服务器IP>

# 示例：
./deploy_to_tencentcloud.sh 123.45.67.89
```

### 第3步：访问应用

部署完成后，在浏览器访问：
```
http://<服务器IP>
```

---

## 📋 详细步骤

### 准备工作

1. **购买腾讯云轻量应用服务器**
   - 访问：https://cloud.tencent.com/product/lighthouse
   - 选择：Ubuntu 22.04 LTS + 2核4GB + 5Mbps
   - 记录服务器IP地址和密码

2. **在本地电脑准备**
   - 确保已安装SSH客户端
   - 确保网络连接正常

### 运行部署脚本

```bash
# 进入项目目录
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2

# 运行部署脚本
./deploy_to_tencentcloud.sh <服务器IP>

# 按照提示操作：
# 1. 确认部署 - 输入 y
# 2. 上传文件 - 输入 y（可选）
# 3. 启动应用 - 输入 y（可选）
```

### 访问应用

部署成功后，访问：
```
http://<服务器IP>
```

例如：`http://123.45.67.89`

---

## 🔧 手动部署（可选）

如果一键部署脚本失败，可以按照以下步骤手动部署：

### 步骤1: 连接服务器

```bash
ssh root@<服务器IP>
# 输入密码
```

### 步骤2: 安装基础环境

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx supervisor
pip3 install flask pandas numpy scikit-learn
```

### 步骤3: 上传项目文件

**在本地电脑**：
```bash
scp -r copper_prediction_v2/ root@<服务器IP>:/opt/copper-prediction/
```

**或使用压缩包**：
```bash
tar -czf copper-prediction.tar.gz copper_prediction_v2/
scp copper-prediction.tar.gz root@<服务器IP>:/opt/
```

**在服务器上**：
```bash
cd /opt
tar -xzf copper-prediction.tar.gz --strip-components=1 -C /opt/copper-prediction/
```

### 步骤4: 配置并启动

```bash
cd /opt/copper-prediction
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动应用
python app.py
```

---

## 📊 部署后验证

### 1. 测试Web访问

在浏览器访问：
```
http://<服务器IP>
```

### 2. 查看应用状态

```bash
ssh root@<服务器IP>
supervisorctl status copper-prediction
```

### 3. 查看日志

```bash
ssh root@<服务器_IP>
tail -f /opt/copper-prediction/logs/supervisor_stdout.log
```

---

## 🔄 日常运维

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

### 更新代码

**在本地**：
```bash
# 修改代码后，重新上传
scp -r copper_prediction_v2/ root@<服务器_IP>:/opt/copper-prediction/
```

**在服务器**：
```bash
ssh root@<服务器_IP>
supervisorctl restart copper-prediction
```

### 查看定时任务

```bash
ssh root@<服务器_IP>
crontab -l | grep copper
```

---

## ⚠️ 常见问题

### 问题1: SSH连接失败

**解决方案**：
1. 检查服务器IP是否正确
2. 检查服务器是否正在运行
3. 检查SSH端口(22)是否开放
4. 检查用户名和密码是否正确

### 问题2: 端口无法访问

**解决方案**：
1. 检查防火墙：`ufw status`
2. 检查Nginx：`nginx -t`
3. 在腾讯云控制台检查安全组，确保端口80已开放

### 问题3: 应用无法启动

**解决方案**：
```bash
ssh root@<服务器_IP>
supervisorctl tail -f copper-prediction stderr
cd /opt/copper-prediction
source venv/bin/activate
python app.py
```

### 问题4: 定时任务不运行

**解决方案**：
```bash
ssh root@<服务器_IP>
crontab -l
grep CRON /var/log/syslog
```

---

## 💰 成本说明

| 项目 | 价格 |
|------|------|
| 轻量服务器 (2核4GB + 5Mbps) | ~¥50-100/月 |
| 流量 | 免费额度内 |
| SSL证书 (Let's Encrypt) | 免费 |

**月成本**: 约 ¥50-100

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
```

---

## 📚 详细文档

完整部署文档：`deploy_tencentcloud.md`

---

## 🎉 开始部署

```bash
cd /Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2
./deploy_to_tencentcloud.sh <服务器IP>
```

按照提示操作，几分钟内完成部署！
