# 财经资讯报告平台

一个自动生成财经热点资讯HTML报告的系统，支持科技新闻、贵金属（黄金、白银、铜）和石油等大宗商品的热点事件扫描和报告生成。

## 项目功能

### 📊 报告类型

1. **科技资讯报告** (`tech-news-report.html`)
   - 扫描国内外权威媒体和社交平台
   - 聚焦AI芯片、自动驾驶、量子计算等前沿科技
   - 过去24小时科技热点事件

2. **贵金属和石油报告** (`commodities-news-report.html`)
   - 覆盖黄金、白银、铜、石油四大品类
   - 国内国际权威财经媒体
   - 实时价格走势、市场动态、投资需求

### 🎨 报告特点

- 响应式设计，支持手机和电脑访问
- 现代化渐变色主题
- 分类标签（科技/媒体、黄金/白银/铜/石油）
- 直接链接到原文
- 统计数据和摘要

## 技能包

### tech-news-scanner.zip
科技新闻扫描技能，用于自动化生成科技资讯报告。

### commodities-news-scanner.zip
贵金属和石油新闻扫描技能，用于自动化生成财经商品报告。

## 在线访问

### EdgeOne Pages 部署
- **预览链接**: https://technenews-5l2pym9u2d.edgeone.dev?eo_token=402312a2c3c9d3202988cbbbdc51c3ab&eo_time=1771994620
- **控制台**: https://console.cloud.tencent.com/edgeone/pages/project/pages-cqdh3adlrcst/index

### CloudStudio 部署
- **访问链接**: http://bad8b3dc46b64c06b4222f0c46dd2e11.codebuddy.cloudstudio.run

## 本地运行

### 启动静态服务器
```bash
python3 -m http.server 8080
```

然后在浏览器中访问：
- 科技资讯: http://localhost:8080/tech-news-report.html
- 贵金属和石油: http://localhost:8080/commodities-news-report.html

## 数据文件

- `news.json` - 科技新闻数据源
- `commodities_news.json` - 贵金属和石油新闻数据源

## 技术栈

- HTML5 + CSS3
- Python 3 (报告生成脚本)
- 静态网站托管（EdgeOne Pages / CloudStudio）

## 更新日志

### 2026-02-25
- ✅ 创建科技新闻扫描技能
- ✅ 创建贵金属和石油新闻扫描技能
- ✅ 生成首个科技资讯报告（15条热点）
- ✅ 生成首个贵金属和石油报告（16条热点）
- ✅ 部署到 EdgeOne Pages 和 CloudStudio

## 许可证

MIT License
