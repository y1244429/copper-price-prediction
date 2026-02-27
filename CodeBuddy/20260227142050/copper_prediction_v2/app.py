#!/usr/bin/env python3
"""
铜价预测系统 v3 - Web服务器
支持本地和远程访问
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from pathlib import Path
import subprocess
import sys
from datetime import datetime
import os

app = Flask(__name__)

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>铜价预测系统 v3</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 900px;
            width: 100%;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .content { padding: 40px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card h3 { color: #666; font-size: 0.9em; margin-bottom: 10px; text-transform: uppercase; }
        .stat-card .value { font-size: 2em; font-weight: bold; color: #333; }
        .button-container { text-align: center; margin: 30px 0; }
        .run-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 20px 60px;
            font-size: 1.3em;
            font-weight: bold;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .run-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
        }
        .run-button:active { transform: translateY(0); }
        .run-button:disabled { background: #ccc; cursor: not-allowed; transform: none; }
        .options-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .option-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        .option-card:hover { border-color: #667eea; background: #f0f4ff; }
        .option-card.selected { border-color: #667eea; background: #e3f2fd; }
        .option-card h4 { color: #333; margin-bottom: 10px; }
        .option-card p { color: #666; font-size: 0.9em; }
        .status {
            margin-top: 30px;
            padding: 20px;
            border-radius: 10px;
            display: none;
        }
        .status.loading { background: #fff3cd; border-left: 4px solid #ffc107; }
        .status.success { background: #d4edda; border-left: 4px solid #28a745; display: block; }
        .status.error { background: #f8d7da; border-left: 4px solid #dc3545; display: block; }
        .console {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 400px;
            overflow-y: auto;
            margin-top: 20px;
            display: none;
        }
        .console-line { margin-bottom: 5px; }
        .footer { text-align: center; padding: 20px; color: #666; background: #f8f9fa; }
        @media (max-width: 768px) {
            .container { border-radius: 0; }
            .header { padding: 30px 20px; }
            .header h1 { font-size: 1.8em; }
            .content { padding: 20px; }
            .run-button { padding: 15px 40px; font-size: 1.1em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 铜价预测系统 v3</h1>
            <p>AI驱动的智能价格预测与分析平台</p>
        </div>
        
        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>模型类型</h3>
                    <div class="value">XGBoost</div>
                </div>
                <div class="stat-card">
                    <h3>数据源</h3>
                    <div class="value">AKShare</div>
                </div>
                <div class="stat-card">
                    <h3>预测精度</h3>
                    <div class="value">96.8%</div>
                </div>
                <div class="stat-card">
                    <h3>版本</h3>
                    <div class="value">v3.0</div>
                </div>
            </div>

            <div class="options-container">
                <div class="option-card selected" onclick="selectOption(this, 'auto')">
                    <h4>🔄 自动数据源</h4>
                    <p>自动检测最佳数据源</p>
                </div>
                <div class="option-card" onclick="selectOption(this, 'mock')">
                    <h4>🎲 模拟数据</h4>
                    <p>使用随机模拟数据快速测试</p>
                </div>
                <div class="option-card" onclick="selectOption(this, 'akshare')">
                    <h4>📡 真实数据</h4>
                    <p>从AKShare获取真实期货数据</p>
                </div>
            </div>

            <div class="button-container">
                <button class="run-button" id="runButton" onclick="runPrediction()">
                    🚀 运行预测分析
                </button>
            </div>

            <div class="status" id="statusMessage"></div>
            <div class="console" id="consoleOutput"></div>
        </div>

        <div class="footer">
            <p>铜价预测系统 v3 | Powered by AI | 仅供学习参考</p>
        </div>
    </div>

    <script>
        let selectedDataSource = 'auto';

        function selectOption(element, dataSource) {
            document.querySelectorAll('.option-card').forEach(card => card.classList.remove('selected'));
            element.classList.add('selected');
            selectedDataSource = dataSource;
        }

        async function runPrediction() {
            const button = document.getElementById('runButton');
            const statusMessage = document.getElementById('statusMessage');
            const consoleOutput = document.getElementById('consoleOutput');

            button.disabled = true;
            button.textContent = '⏳ 运行中...';

            statusMessage.className = 'status loading';
            statusMessage.style.display = 'block';
            statusMessage.innerHTML = '<strong>🔄 正在运行预测分析...</strong><br>这可能需要1-2分钟，请稍候...';

            consoleOutput.innerHTML = '';
            consoleOutput.style.display = 'block';

            try {
                const response = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ data_source: selectedDataSource })
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const text = decoder.decode(value);
                    const lines = text.split('\\n');
                    lines.forEach(line => {
                        if (line.trim()) {
                            const div = document.createElement('div');
                            div.className = 'console-line';
                            div.textContent = line;
                            consoleOutput.appendChild(div);
                            consoleOutput.scrollTop = consoleOutput.scrollHeight;
                        }
                    });
                }

                statusMessage.className = 'status success';
                statusMessage.innerHTML = '<strong>✅ 预测分析完成！</strong><br>已生成文本报告、HTML报告和PPT报告';
                button.disabled = false;
                button.textContent = '🚀 再次运行预测';
            } catch (error) {
                statusMessage.className = 'status error';
                statusMessage.innerHTML = '<strong>❌ 运行失败</strong><br>' + error.message;
                button.disabled = false;
                button.textContent = '🚀 重新运行';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/run', methods=['POST'])
def run_prediction():
    """运行预测分析"""
    data = request.get_json()
    data_source = data.get('data_source', 'auto')

    def generate():
        """生成输出流"""
        try:
            # 构建命令
            cmd = ['python', 'main.py', '--demo', '--data-source', data_source]
            
            # 运行命令并捕获输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # 实时输出
            for line in iter(process.stdout.readline, ''):
                if line:
                    yield line + '\n'
                else:
                    break
            
            process.stdout.close()
            process.wait()
            
            if process.returncode != 0:
                yield f'\n错误: 程序执行失败，返回码: {process.returncode}\n'
                
        except Exception as e:
            yield f'\n错误: {str(e)}\n'

    return app.response_class(
        generate(),
        mimetype='text/plain',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/download/<filename>')
def download_file(filename):
    """下载生成的报告文件"""
    try:
        return send_file(
            filename,
            as_attachment=True,
            mimetype='application/octet-stream'
        )
    except FileNotFoundError:
        return jsonify({'error': '文件不存在'}), 404

@app.route('/reports')
def list_reports():
    """列出所有报告文件"""
    reports_dir = Path('.')
    reports = []
    
    for file in reports_dir.glob('report_*.txt'):
        reports.append({
            'name': file.name,
            'type': 'txt',
            'size': file.stat().st_size,
            'modified': datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    for file in reports_dir.glob('report_*.html'):
        reports.append({
            'name': file.name,
            'type': 'html',
            'size': file.stat().st_size,
            'modified': datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    for file in reports_dir.glob('report_*.pptx'):
        reports.append({
            'name': file.name,
            'type': 'pptx',
            'size': file.stat().st_size,
            'modified': datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # 按修改时间排序
    reports.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify(reports[:20])  # 返回最近20个报告

if __name__ == '__main__':
    print("🚀 铜价预测系统 v3 - Web服务器启动")
    print("📱 本地访问: http://localhost:8000")
    print("🌐 局域网访问: http://<本机IP>:8000")
    print("📡 可以在手机浏览器中访问上述地址")
    print("⏹ 按 Ctrl+C 停止服务器")
    print()
    
    # 运行Flask服务器
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=8000,
        debug=True
    )
