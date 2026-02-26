"""
铜价格预测模型 - Flask Web应用
可以通过API接口调用的Web服务
"""

from flask import Flask, request, jsonify, render_template_string
from copper_price_model import CopperPriceModel
from datetime import datetime
import json

app = Flask(__name__)

# 初始化模型
model = CopperPriceModel()


# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>铜价格预测模型</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .current-price {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 30px;
        }

        .current-price h2 {
            font-size: 1.2em;
            margin-bottom: 10px;
            opacity: 0.9;
        }

        .current-price .price {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .current-price .range {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .control-group {
            display: flex;
            flex-direction: column;
        }

        .control-group label {
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }

        .control-group select,
        .control-group input {
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        .control-group select:focus,
        .control-group input:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin: 5px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }

        .btn-warning {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .results {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .result-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }

        .result-card h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
        }

        .result-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }

        .result-item:last-child {
            border-bottom: none;
        }

        .result-label {
            color: #666;
        }

        .result-value {
            font-weight: 600;
            color: #333;
        }

        .trend-up {
            color: #28a745;
        }

        .trend-down {
            color: #dc3545;
        }

        .trend-neutral {
            color: #6c757d;
        }

        .scores-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }

        .score-item {
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .score-item .score-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }

        .score-item .score-value {
            font-size: 1.5em;
            font-weight: bold;
        }

        .score-positive {
            color: #28a745;
        }

        .score-negative {
            color: #dc3545;
        }

        .key-levels {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }

        .level-item {
            text-align: center;
            padding: 15px;
            border-radius: 8px;
        }

        .level-support {
            background: #d4edda;
            color: #155724;
        }

        .level-resistance {
            background: #f8d7da;
            color: #721c24;
        }

        .recommendation {
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 1.2em;
            font-weight: 600;
            margin-top: 20px;
        }

        .rec-buy {
            background: #d4edda;
            color: #155724;
        }

        .rec-sell {
            background: #f8d7da;
            color: #721c24;
        }

        .rec-hold {
            background: #fff3cd;
            color: #856404;
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 1.8em;
            }

            .controls {
                grid-template-columns: 1fr;
            }

            .current-price .price {
                font-size: 2.5em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔋 铜价格预测模型</h1>

        <div class="current-price">
            <h2>当前沪铜主力价格</h2>
            <div class="price">¥{{ current_price:,.0f}} /吨</div>
            <div class="range">运行区间: ¥101,500 - ¥103,500</div>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 20px; color: #333;">选择预测周期</h2>

            <div class="controls">
                <div class="control-group">
                    <label>预测类型</label>
                    <select id="predictType">
                        <option value="short">短期预测 (1-30天)</option>
                        <option value="medium">中期预测 (1-6个月)</option>
                        <option value="long">长期预测 (1-3年)</option>
                        <option value="assessment">市场评估报告</option>
                    </select>
                </div>

                <div class="control-group" id="daysGroup">
                    <label>预测天数</label>
                    <select id="days">
                        <option value="5">5天</option>
                        <option value="10">10天</option>
                        <option value="15">15天</option>
                        <option value="20">20天</option>
                        <option value="30">30天</option>
                    </select>
                </div>

                <div class="control-group" id="monthsGroup" style="display: none;">
                    <label>预测月数</label>
                    <select id="months">
                        <option value="1">1个月</option>
                        <option value="3" selected>3个月</option>
                        <option value="6">6个月</option>
                    </select>
                </div>

                <div class="control-group" id="yearsGroup" style="display: none;">
                    <label>预测年数</label>
                    <select id="years">
                        <option value="1" selected>1年</option>
                        <option value="2">2年</option>
                        <option value="3">3年</option>
                    </select>
                </div>
            </div>

            <div style="text-align: center;">
                <button class="btn btn-primary" onclick="predict()">🔮 开始预测</button>
                <button class="btn btn-success" onclick="getAllPredictions()">📊 综合预测</button>
            </div>
        </div>

        <div id="results" class="results" style="margin-top: 30px;"></div>
    </div>

    <script>
        const currentPrice = {{ current_price }};

        document.getElementById('predictType').addEventListener('change', function() {
            const type = this.value;
            document.getElementById('daysGroup').style.display = type === 'short' ? 'flex' : 'none';
            document.getElementById('monthsGroup').style.display = type === 'medium' ? 'flex' : 'none';
            document.getElementById('yearsGroup').style.display = type === 'long' ? 'flex' : 'none';
        });

        async function predict() {
            const type = document.getElementById('predictType').value;
            let url = '/api/short';

            if (type === 'short') {
                const days = document.getElementById('days').value;
                url = `/api/short?days=${days}`;
            } else if (type === 'medium') {
                const months = document.getElementById('months').value;
                url = `/api/medium?months=${months}`;
            } else if (type === 'long') {
                const years = document.getElementById('years').value;
                url = `/api/long?years=${years}`;
            } else if (type === 'assessment') {
                url = '/api/assessment';
            }

            try {
                const response = await fetch(url);
                const data = await response.json();
                displayResult(data, type);
            } catch (error) {
                alert('预测失败,请稍后重试');
                console.error(error);
            }
        }

        async function getAllPredictions() {
            try {
                const [short, medium, long, assessment] = await Promise.all([
                    fetch('/api/short?days=5').then(r => r.json()),
                    fetch('/api/medium?months=3').then(r => r.json()),
                    fetch('/api/long?years=1').then(r => r.json()),
                    fetch('/api/assessment').then(r => r.json())
                ]);

                displayResult({ short, medium, long, assessment }, 'all');
            } catch (error) {
                alert('预测失败,请稍后重试');
                console.error(error);
            }
        }

        function displayResult(data, type) {
            const resultsDiv = document.getElementById('results');
            let html = '';

            if (type === 'all') {
                html = `
                    <div class="result-card">
                        <h3>⏱️ 短期预测 (${data.short.period})</h3>
                        <div class="result-item">
                            <span class="result-label">当前价格</span>
                            <span class="result-value">¥${data.short.current_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">预测价格</span>
                            <span class="result-value">¥${data.short.predicted_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">预测涨跌</span>
                            <span class="result-value trend-${data.short.trend === '上涨' ? 'up' : 'down'}">
                                ${data.short.predicted_change > 0 ? '+' : ''}${data.short.predicted_change}%
                            </span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">趋势判断</span>
                            <span class="result-value">${data.short.trend}</span>
                        </div>
                        <div class="recommendation rec-${data.short.recommendation === '逢低买入' ? 'buy' : data.short.recommendation === '逢高卖出' ? 'sell' : 'hold'}">
                            ${data.short.recommendation}
                        </div>
                    </div>

                    <div class="result-card">
                        <h3>📅 中期预测 (${data.medium.period})</h3>
                        <div class="result-item">
                            <span class="result-label">当前价格</span>
                            <span class="result-value">¥${data.medium.current_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">预测价格</span>
                            <span class="result-value">¥${data.medium.predicted_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">预测涨跌</span>
                            <span class="result-value trend-${data.medium.trend === '上涨' ? 'up' : 'down'}">
                                ${data.medium.predicted_change > 0 ? '+' : ''}${data.medium.predicted_change}%
                            </span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">波动区间</span>
                            <span class="result-value">
                                ¥${data.medium.target_range['波动区间'][0].toLocaleString()} - 
                                ¥${data.medium.target_range['波动区间'][1].toLocaleString()}
                            </span>
                        </div>
                        <div class="recommendation rec-${data.medium.recommendation === '逢低布局多单' ? 'buy' : 'hold'}">
                            ${data.medium.recommendation}
                        </div>
                    </div>

                    <div class="result-card">
                        <h3>🚀 长期预测 (${data.long.period})</h3>
                        <div class="result-item">
                            <span class="result-label">当前价格</span>
                            <span class="result-value">¥${data.long.current_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">预测价格</span>
                            <span class="result-value">¥${data.long.predicted_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">年均增长</span>
                            <span class="result-value trend-up">${data.long.annual_growth}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">趋势判断</span>
                            <span class="result-value trend-up">${data.long.trend}</span>
                        </div>
                        <div class="recommendation rec-buy">
                            ${data.long.recommendation}
                        </div>
                    </div>
                `;
            } else if (type === 'short' || type === 'medium') {
                const trendClass = data.trend === '上涨' ? 'up' : 'down';
                html = `
                    <div class="result-card">
                        <h3>📊 ${data.period}预测结果</h3>
                        <div class="result-item">
                            <span class="result-label">当前价格</span>
                            <span class="result-value">¥${data.current_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">预测价格</span>
                            <span class="result-value">¥${data.predicted_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">预测涨跌</span>
                            <span class="result-value trend-${trendClass}">
                                ${data.predicted_change > 0 ? '+' : ''}${data.predicted_change}%
                            </span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">趋势判断</span>
                            <span class="result-value trend-${trendClass}">${data.trend}</span>
                        </div>
                `;

                if (data.support) {
                    html += `
                        <h4 style="margin-top: 15px; color: #666;">支撑阻力位</h4>
                        <div class="key-levels" style="margin-top: 10px;">
                            <div class="level-item level-support">
                                <div style="font-size: 0.8em; opacity: 0.8;">支撑1</div>
                                <div style="font-weight: bold;">¥${data.support['支撑1'].toLocaleString()}</div>
                            </div>
                            <div class="level-item level-support">
                                <div style="font-size: 0.8em; opacity: 0.8;">支撑2</div>
                                <div style="font-weight: bold;">¥${data.support['支撑2'].toLocaleString()}</div>
                            </div>
                            <div class="level-item level-resistance">
                                <div style="font-size: 0.8em; opacity: 0.8;">阻力1</div>
                                <div style="font-weight: bold;">¥${data.resistance['阻力1'].toLocaleString()}</div>
                            </div>
                            <div class="level-item level-resistance">
                                <div style="font-size: 0.8em; opacity: 0.8;">阻力2</div>
                                <div style="font-weight: bold;">¥${data.resistance['阻力2'].toLocaleString()}</div>
                            </div>
                        </div>
                    `;
                }

                if (data.scores) {
                    html += `
                        <h4 style="margin-top: 15px; color: #666;">各因子得分</h4>
                        <div class="scores-grid">
                    `;
                    for (const [key, value] of Object.entries(data.scores)) {
                        const scoreClass = value > 0 ? 'score-positive' : value < 0 ? 'score-negative' : '';
                        html += `
                            <div class="score-item">
                                <div class="score-label">${key}</div>
                                <div class="score-value ${scoreClass}">${value.toFixed(3)}</div>
                            </div>
                        `;
                    }
                    html += '</div>';
                }

                html += `
                    <div class="recommendation rec-${data.recommendation.includes('买入') ? 'buy' : data.recommendation.includes('卖出') ? 'sell' : 'hold'}">
                        ${data.recommendation}
                    </div>
                </div>`;
            } else if (type === 'long') {
                html = `
                    <div class="result-card">
                        <h3>🚀 ${data.period}长期预测</h3>
                        <div class="result-item">
                            <span class="result-label">当前价格</span>
                            <span class="result-value">¥${data.current_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">预测价格</span>
                            <span class="result-value trend-up">¥${data.predicted_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">年均增长率</span>
                            <span class="result-value trend-up">${data.annual_growth}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">趋势判断</span>
                            <span class="result-value trend-up">${data.trend}</span>
                        </div>

                        <h4 style="margin-top: 15px; color: #666;">LME价格预测</h4>
                        <div class="result-item">
                            <span class="result-label">2026 Q2</span>
                            <span class="result-value">$${data.price_forecast['LME预测(美元)']['2026_Q2'].toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">2026 Q3</span>
                            <span class="result-value">$${data.price_forecast['LME预测(美元)']['2026_Q3'].toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">2026年均</span>
                            <span class="result-value">$${data.price_forecast['LME预测(美元)']['2026_avg'].toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">2035年目标</span>
                            <span class="result-value trend-up">$${data.price_forecast['LME预测(美元)']['2035'].toLocaleString()}</span>
                        </div>

                        <div class="recommendation rec-buy">
                            ${data.recommendation}
                        </div>
                    </div>
                `;
            } else if (type === 'assessment') {
                html = `
                    <div class="result-card">
                        <h3>📋 市场评估报告</h3>
                        <div class="result-item">
                            <span class="result-label">评估日期</span>
                            <span class="result-value">${data.date}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">当前价格</span>
                            <span class="result-value">¥${data.current_price.toLocaleString()}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">运行区间</span>
                            <span class="result-value">¥${data.price_range}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">周期位置</span>
                            <span class="result-value">${data.cycle_position}</span>
                        </div>

                        <h4 style="margin-top: 15px; color: #666;">关键价位</h4>
                        <div class="key-levels" style="margin-top: 10px;">
                `;

                for (const [level, values] of Object.entries(data.key_levels)) {
                    const levelClass = level === '支撑位' ? 'level-support' : 'level-resistance';
                    for (const [name, price] of Object.entries(values)) {
                        html += `
                            <div class="level-item ${levelClass}">
                                <div style="font-size: 0.8em; opacity: 0.8;">${name}</div>
                                <div style="font-weight: bold;">¥${price.toLocaleString()}</div>
                            </div>
                        `;
                    }
                }

                html += `
                        </div>

                        <h4 style="margin-top: 15px; color: #666;">库存状态</h4>
                        <div class="result-item">
                            <span class="result-label">LME库存</span>
                            <span class="result-value">${data.inventory_status['LME']}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">SHFE库存</span>
                            <span class="result-value">${data.inventory_status['SHFE']}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">中国社库</span>
                            <span class="result-value">${data.inventory_status['中国社库']}</span>
                        </div>

                        <h4 style="margin-top: 15px; color: #666;">交易策略</h4>
                        <div class="result-item">
                            <span class="result-label">短期</span>
                            <span class="result-value">${data.trading_strategy['short_term']}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">中期</span>
                            <span class="result-value">${data.trading_strategy['medium_term']}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">长期</span>
                            <span class="result-value trend-up">${data.trading_strategy['long_term']}</span>
                        </div>

                        <h4 style="margin-top: 15px; color: #666;">风险因素</h4>
                        <ul style="margin-top: 10px; padding-left: 20px;">
                            ${data.risk_factors.map(r => `<li style="color: #dc3545;">⚠️ ${r}</li>`).join('')}
                        </ul>

                        <h4 style="margin-top: 15px; color: #666;">机会因素</h4>
                        <ul style="margin-top: 10px; padding-left: 20px;">
                            ${data.opportunity_factors.map(o => `<li style="color: #28a745;">✅ ${o}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE, current_price=model.current_price)


@app.route('/api/short')
def short_prediction():
    """短期预测API"""
    days = int(request.args.get('days', 5))
    return jsonify(model.predict_short_term(days=days))


@app.route('/api/medium')
def medium_prediction():
    """中期预测API"""
    months = int(request.args.get('months', 3))
    return jsonify(model.predict_medium_term(months=months))


@app.route('/api/long')
def long_prediction():
    """长期预测API"""
    years = int(request.args.get('years', 1))
    return jsonify(model.predict_long_term(years=years))


@app.route('/api/assessment')
def market_assessment():
    """市场评估API"""
    return jsonify(model.get_market_assessment())


@app.route('/api/all')
def all_predictions():
    """综合预测API"""
    return jsonify({
        'short': model.predict_short_term(days=5),
        'medium': model.predict_medium_term(months=3),
        'long': model.predict_long_term(years=1),
        'assessment': model.get_market_assessment()
    })


if __name__ == '__main__':
    port = 5001
    print("=" * 60)
    print("🔋 铜价格预测模型 - Web服务已启动")
    print("=" * 60)
    print(f"📱 访问地址: http://localhost:{port}")
    print("📊 API文档:")
    print(f"   - GET /api/short?days=5      短期预测")
    print(f"   - GET /api/medium?months=3   中期预测")
    print(f"   - GET /api/long?years=1       长期预测")
    print(f"   - GET /api/assessment        市场评估")
    print(f"   - GET /api/all               综合预测")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务\n")

    app.run(debug=True, host='0.0.0.0', port=port)
