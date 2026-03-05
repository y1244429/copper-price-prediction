# 铜价预测系统 - 腾讯云部署指南

## 📋 部署方案概览

### 推荐方案：腾讯云轻量应用服务器 (Lighthouse)

| 特性 | 说明 |
|------|------|
| **服务器规格** | 2核 4GB（推荐）或 2核 2GB |
| **操作系统** | Ubuntu 22.04 LTS |
| **带宽** | 5Mbps 或 10Mbps |
| **价格** | 约 ¥50-100/月 |
| **适合场景** | Web应用、定时任务、数据分析 |

### 优势
- ✅ 一键部署，操作简单
- ✅ 内置防火墙和安全组
- ✅ 支持SSH远程访问
- ✅ 可以配置定时任务
- ✅ 可以持久化存储数据

---

## 🚀 快速部署步骤

### 步骤1: 购买轻量应用服务器

1. 访问：https://cloud.tencent.com/product/lighthouse

2. 选择配置：
   - **镜像**: Ubuntu 22.04 LTS
   - **规格**: 2核 4GB（或 2核 2GB）
   - **带宽**: 5Mbps
   - **数据盘**: 40GB（可选）

3. 设置服务器信息：
   - **服务器名称**: copper-prediction
   - **登录方式**: 密码（设置一个强密码）

4. 购买并等待服务器创建完成（约5-10分钟）

5. 获取服务器IP地址（在控制台查看）

---

### 步骤2: 连接服务器

#### 方法1: 使用SSH（推荐）
```bash
ssh root@<服务器IP地址>
# 输入密码
```

#### 方法2: 使用腾讯云控制台
在"轻量应用服务器"控制台，点击"登录"

#### 方法3: 使用SSH密钥（更安全）
```bash
# 在本地生成SSH密钥
ssh-keygen -t rsa -b 4096

# 上传公钥到服务器
ssh-copy-id root@<服务器IP地址>

# 之后可以直接登录，无需密码
ssh root@<服务器IP地址>
```

---

### 步骤3: 安装基础环境

连接到服务器后，执行以下命令：

```bash
# 1. 更新系统
apt update && apt upgrade -y

# 2. 安装必要工具
apt install -y python3 python3-pip python3-venv git curl wget vim

# 3. 安装Nginx（Web服务器）
apt install -y nginx

# 4. 安装Supervisor（进程管理）
apt install -y supervisor

# 5. 安装PM2（可选，用于Node.js应用）
# npm install -g pm2

# 6. 检查安装
python3 --version
pip3 --version
nginx -v
supervisord --version
```

---

### 步骤4: 创建项目目录

```bash
# 创建项目目录
mkdir -p /opt/copper-prediction
cd /opt/copper-prediction

# 创建必要的子目录
mkdir -p logs outputs reports
```

---

### 步骤5: 上传项目文件

#### 方法1: 使用SCP上传（推荐）

**在本地电脑执行**：
```bash
# 压缩项目文件
cd /Users/ydy/CodeBuddy/20260227142050
tar -czf copper-prediction.tar.gz copper_prediction_v2/

# 上传到服务器
scp copper-prediction.tar.gz root@<服务器IP地址>:/opt/

# 或上传整个目录
scp -r copper_prediction_v2/ root@<服务器IP地址>:/opt/copper-prediction/
```

#### 方法2: 使用Git（如果有Git仓库）

```bash
# 在服务器上执行
cd /opt/copper-prediction
git clone <你的Git仓库地址>
```

#### 方法3: 手动复制

在本地电脑：
1. 将项目文件打包成 `copper-prediction.tar.gz`
2. 在腾讯云控制台"文件上传"功能上传
3. 在服务器上解压

---

### 步骤6: 配置Python环境

```bash
# 进入项目目录
cd /opt/copper-prediction

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖（如果requirements.txt存在）
pip install -r requirements.txt

# 或手动安装核心依赖
pip install flask pandas numpy scikit-learn statsmodels akshare yfinance matplotlib seaborn python-pptx

# 安装额外的依赖
pip install gunicorn

# 验证安装
python -c "import flask; print('Flask OK')"
python -c "import pandas; print('Pandas OK')"
```

---

### 步骤7: 配置Flask应用

#### 创建生产配置文件

```bash
cd /opt/copper-prediction

# 创建配置文件
cat > config.py << 'EOF'
import os

class Config:
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

    # 允许外部访问
    HOST = '0.0.0.0'
    PORT = 8002

    # 调试模式（生产环境关闭）
    DEBUG = False

    # 日志配置
    LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
    LOG_LEVEL = 'INFO'
EOF
```

#### 修改app.py以支持生产环境

```bash
# 备份原文件
cp app.py app.py.bak

# 修改app.py的最后一部分（if __name__ == '__main__':）
cat >> app.py << 'EOF'

# 生产环境配置
if __name__ == '__main__':
    # 从环境变量读取配置
    config = Config()

    print("🚀 铜价预测系统 v3 - 生产环境启动")
    print("📱 访问地址: http://0.0.0.0:8002")
    print("📡 使用Gunicorn运行: gunicorn -w 4 -b 0.0.0.0:8002 app:app")
    print()

    # 生产环境建议使用Gunicorn
    # 开发环境可直接使用Flask
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
EOF
```

---

### 步骤8: 配置Gunicorn（生产服务器）

```bash
cd /opt/copper-prediction

# 创建Gunicorn配置文件
cat > gunicorn_config.py << 'EOF'
import multiprocessing

# 服务器配置
bind = "0.0.0.0:8002"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 5

# 日志配置
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# 进程命名
proc_name = "copper-prediction"
EOF

# 测试Gunicorn
source venv/bin/activate
gunicorn -c gunicorn_config.py app:app &
```

---

### 步骤9: 配置Supervisor（进程管理）

```bash
# 创建Supervisor配置文件
cat > /etc/supervisor/conf.d/copper-prediction.conf << 'EOF'
[program:copper-prediction]
command=/opt/copper-prediction/venv/bin/gunicorn -c /opt/copper-prediction/gunicorn_config.py app:app
directory=/opt/copper-prediction
user=root
autostart=true
autorestart=true
startsecs=10
startretries=3
stderr_logfile=/opt/copper-prediction/logs/supervisor_stderr.log
stdout_logfile=/opt/copper-prediction/logs/supervisor_stdout.log
environment=PATH="/opt/copper-prediction/venv/bin"
EOF

# 重新加载Supervisor
supervisorctl reread
supervisorctl update

# 启动应用
supervisorctl start copper-prediction

# 查看状态
supervisorctl status
```

---

### 步骤10: 配置Nginx（反向代理）

```bash
# 创建Nginx配置文件
cat > /etc/nginx/sites-available/copper-prediction << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    # 静态文件缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        proxy_pass http://127.0.0.1:8002;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/copper-prediction /etc/nginx/sites-enabled/

# 删除默认配置（可选）
rm -f /etc/nginx/sites-enabled/default

# 测试配置
nginx -t

# 重启Nginx
systemctl restart nginx
systemctl enable nginx

# 检查状态
systemctl status nginx
```

---

### 步骤11: 配置防火墙

```bash
# 配置UFW防火墙
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

# 检查防火墙状态
ufw status

# 如果是腾讯云轻量服务器，还需要在控制台配置防火墙规则
# 添加规则：允许端口 80 和 443
```

---

### 步骤12: 配置定时任务（Cron）

```bash
# 创建定时任务脚本
cat > /opt/copper-prediction/run_scheduled_prediction.sh << 'EOF'
#!/bin/bash
#
# 铜价预测系统定时运行脚本
#

PROJECT_DIR="/opt/copper-prediction"
LOG_FILE="$PROJECT_DIR/logs/scheduled_run_$(date +%Y%m%d_%H%M%S).log"

cd "$PROJECT_DIR" || exit 1

# 激活虚拟环境
source venv/bin/activate

echo "========================================" | tee -a "$LOG_FILE"
echo "铜价预测系统 - 定时任务启动" | tee -a "$LOG_FILE"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 运行预测
python main.py --demo --data-source auto 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo "" | tee -a "$LOG_FILE"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

exit $EXIT_CODE
EOF

# 添加执行权限
chmod +x /opt/copper-prediction/run_scheduled_prediction.sh

# 添加到Cron（每天9:20运行）
(crontab -l 2>/dev/null; echo "20 9 * * * cd /opt/copper-prediction && /opt/copper-prediction/run_scheduled_prediction.sh >> /opt/copper-prediction/logs/cron.log 2>&1") | crontab -

# 查看定时任务
crontab -l
```

---

### 步骤13: 配置HTTPS（可选，推荐）

#### 使用Let's Encrypt免费证书

```bash
# 安装Certbot
apt install -y certbot python3-certbot-nginx

# 自动配置HTTPS
certbot --nginx -d your-domain.com

# 或使用服务器IP
certbot --nginx -d <服务器IP>

# 自动续期
certbot renew --dry-run
```

#### 配置自动续期
```bash
# 添加到Cron
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && systemctl reload nginx") | crontab -
```

---

## 🔍 验证部署

### 1. 测试Web应用

在浏览器访问：
```
http://<服务器IP>
```

或
```
http://<你的域名>
```

### 2. 查看应用状态

```bash
# 查看Supervisor状态
supervisorctl status copper-prediction

# 查看应用日志
tail -f /opt/copper-prediction/logs/supervisor_stdout.log

# 查看Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 3. 测试定时任务

```bash
# 手动运行
cd /opt/copper-prediction
./run_scheduled_prediction.sh

# 查看定时任务日志
tail -f /opt/copper-prediction/logs/cron.log
```

---

## 📊 日常运维

### 查看应用状态
```bash
supervisorctl status
systemctl status nginx
```

### 重启应用
```bash
supervisorctl restart copper-prediction
systemctl restart nginx
```

### 查看日志
```bash
# 应用日志
tail -f /opt/copper-prediction/logs/supervisor_stdout.log

# Nginx日志
tail -f /var/log/nginx/access.log

# 定时任务日志
tail -f /opt/copper-prediction/logs/cron.log
```

### 更新代码
```bash
cd /opt/copper-prediction
# 上传新文件
supervisorctl restart copper-prediction
```

---

## 🔧 故障排除

### 应用无法启动
```bash
# 查看详细错误
supervisorctl tail -f copper-prediction stderr

# 检查端口占用
netstat -tulpn | grep 8002

# 手动测试
cd /opt/copper-prediction
source venv/bin/activate
python app.py
```

### 端口无法访问
```bash
# 检查防火墙
ufw status

# 检查Nginx
nginx -t
systemctl status nginx

# 检查腾讯云安全组（在控制台）
# 确保端口80和443已开放
```

### 定时任务不运行
```bash
# 查看Cron日志
grep CRON /var/log/syslog

# 手动运行测试
cd /opt/copper-prediction
./run_scheduled_prediction.sh
```

---

## 💰 成本估算

| 资源 | 规格 | 价格 |
|------|------|------|
| 服务器 | 2核4GB + 5Mbps + 40GB | ~¥50-100/月 |
| 流量 | 免费额度内 | 免费 |
| 域名 | .com | ~¥50-年 |
| SSL证书 | Let's Encrypt | 免费 |

**月成本估算**: 约 ¥50-100

---

## 📞 快速命令参考

```bash
# SSH登录
ssh root@<服务器IP>

# 查看应用状态
supervisorctl status copper-prediction

# 重启应用
supervisorctl restart copper-prediction

# 查看日志
tail -f /opt/copper-prediction/logs/supervisor_stdout.log

# 查看定时任务
crontab -l

# 测试Web访问
curl http://localhost:8002
```

---

## 🎉 部署完成！

现在您可以通过浏览器访问：
```
http://<服务器IP>
```

铜价预测系统已在腾讯云上成功部署！
