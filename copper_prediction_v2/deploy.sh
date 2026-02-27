#!/bin/bash
# 部署脚本 - 铜价预测系统 v2

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "铜价预测系统 v2 - 部署脚本"
echo "========================================"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装${NC}"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装${NC}"
    echo "请先安装Docker Compose"
    exit 1
fi

echo -e "${GREEN}✓ Docker检查通过${NC}"

# 创建必要目录
echo ""
echo "创建必要目录..."
mkdir -p data reports models logs deployment/grafana-dashboards

# 部署模式选择
echo ""
echo "选择部署模式:"
echo "1) 本地开发 (最小化)"
echo "2) 生产环境 (完整栈)"
echo "3) 仅API服务"
read -p "请输入选项 (1-3): " deploy_mode

case $deploy_mode in
    1)
        echo -e "${YELLOW}本地开发模式${NC}"
        docker-compose up -d copper-api
        echo -e "${GREEN}✓ API服务已启动${NC}"
        echo "访问: http://localhost:8000"
        ;;
    2)
        echo -e "${YELLOW}生产环境模式${NC}"
        
        # 创建Prometheus配置
        cat > deployment/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'copper-api'
    static_configs:
      - targets: ['copper-api:8000']
EOF
        
        # 构建并启动
        docker-compose build
        docker-compose up -d
        
        echo -e "${GREEN}✓ 所有服务已启动${NC}"
        echo ""
        echo "服务地址:"
        echo "  API: http://localhost:8000"
        echo "  Grafana: http://localhost:3000 (admin/admin)"
        echo "  Prometheus: http://localhost:9090"
        ;;
    3)
        echo -e "${YELLOW}仅API服务模式${NC}"
        docker-compose up -d copper-api
        docker-compose scale copper-api=3
        echo -e "${GREEN}✓ API服务已启动 (3实例)${NC}"
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "部署完成!"
echo "========================================"

# 显示状态
echo ""
echo "服务状态:"
docker-compose ps

echo ""
echo "日志查看:"
echo "  docker-compose logs -f copper-api"
echo ""
echo "停止服务:"
echo "  docker-compose down"
