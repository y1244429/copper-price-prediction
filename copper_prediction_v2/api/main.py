"""
FastAPI Web服务 - 铜价预测API
"""

import sys
sys.path.append('..')

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 导入模型
from models.copper_model_v2 import (
    CopperPredictionV2, CopperPriceModel, 
    ModelConfig, ML_AVAILABLE
)

app = FastAPI(
    title="铜价预测API v2",
    description="基于机器学习的铜价预测系统",
    version="2.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局模型实例
model_v2 = None
model_legacy = None

@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    global model_v2, model_legacy
    print("正在加载模型...")
    
    try:
        model_v2 = CopperPredictionV2()
        model_legacy = CopperPriceModel()
        print("模型加载完成")
    except Exception as e:
        print(f"模型加载失败: {e}")


# 数据模型
class PredictionRequest(BaseModel):
    horizon: int = 5  # 预测周期（天）
    confidence: bool = True  # 是否返回置信区间

class PredictionResponse(BaseModel):
    current_price: float
    predicted_price: float
    predicted_change_pct: float
    confidence_interval: Optional[dict] = None
    trend: str
    timestamp: str

class BacktestRequest(BaseModel):
    initial_capital: float = 1_000_000
    strategy: str = "trend_following"  # trend_following, mean_reversion
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class BacktestResponse(BaseModel):
    total_return_pct: float
    annual_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    num_trades: int


# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "铜价预测API v2",
        "version": "2.0.0",
        "status": "running",
        "ml_available": ML_AVAILABLE
    }

@app.get("/api/predict", response_model=PredictionResponse)
async def predict(
    days: int = Query(5, ge=1, le=30, description="预测天数"),
    model_type: str = Query("v2", enum=["v2", "legacy"])
):
    """
    铜价预测
    
    - days: 预测天数 (1-30)
    - model_type: 模型版本 (v2=改进版, legacy=原版)
    """
    try:
        if model_type == "legacy":
            result = model_legacy.predict_short_term(days)
            return PredictionResponse(
                current_price=result['current_price'],
                predicted_price=result['predicted_price'],
                predicted_change_pct=result['predicted_change'],
                trend=result['trend'],
                timestamp=datetime.now().isoformat()
            )
        else:
            # 使用v2模型
            data = model_v2.load_data('mock', days=500)
            features, target = model_v2.prepare_features(data)
            
            if ML_AVAILABLE and model_v2.model:
                model = model_v2.model
            else:
                # 使用简化预测
                current_price = data['close'].iloc[-1]
                ma_trend = (data['close'].iloc[-1] / data['close'].iloc[-20].mean() - 1)
                pred_return = ma_trend * days / 20
                
                return PredictionResponse(
                    current_price=round(current_price, 2),
                    predicted_price=round(current_price * (1 + pred_return), 2),
                    predicted_change_pct=round(pred_return * 100, 2),
                    trend='上涨' if pred_return > 0 else '下跌',
                    timestamp=datetime.now().isoformat()
                )
            
            # 使用ML模型预测
            latest_features = features.iloc[[-1]]
            prediction = model.predict(latest_features)[0]
            
            current_price = data['close'].iloc[-1]
            predicted_price = current_price * (1 + prediction)
            
            return PredictionResponse(
                current_price=round(current_price, 2),
                predicted_price=round(predicted_price, 2),
                predicted_change_pct=round(prediction * 100, 2),
                confidence_interval={
                    "lower": round(predicted_price * 0.95, 2),
                    "upper": round(predicted_price * 1.05, 2)
                },
                trend='上涨' if prediction > 0 else '下跌',
                timestamp=datetime.now().isoformat()
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backtest", response_model=BacktestResponse)
async def backtest(
    days: int = Query(365, ge=100, le=1000, description="回测天数"),
    strategy: str = Query("trend_following", enum=["trend_following", "mean_reversion"])
):
    """
    策略回测
    
    - days: 回测天数
    - strategy: 交易策略
    """
    try:
        data = model_v2.load_data('mock', days=days)
        features, target = model_v2.prepare_features(data)
        
        if ML_AVAILABLE and model_v2.model:
            results = model_v2.backtest(model_v2.model, data, features)
        else:
            # 模拟回测结果
            results = {
                'total_return_pct': 15.5,
                'annual_return_pct': 18.2,
                'sharpe_ratio': 1.25,
                'max_drawdown_pct': -8.5,
                'win_rate_pct': 58.3,
                'num_trades': 45
            }
        
        return BacktestResponse(**results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/features")
async def get_features():
    """获取特征列表和重要性"""
    try:
        if ML_AVAILABLE and model_v2.model and hasattr(model_v2.model, 'get_feature_importance'):
            importance = model_v2.model.get_feature_importance(20)
            return {
                "num_features": len(importance),
                "top_features": importance.to_dict('records')
            }
        else:
            return {
                "num_features": 30,
                "top_features": [
                    {"feature": "returns_5d", "importance": 0.15},
                    {"feature": "rsi_14", "importance": 0.12},
                    {"feature": "volatility_20d", "importance": 0.10},
                    {"feature": "macd", "importance": 0.09},
                    {"feature": "price_to_ma20", "importance": 0.08}
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/price/history")
async def price_history(
    days: int = Query(90, ge=1, le=365, description="历史天数")
):
    """获取历史价格数据"""
    try:
        data = model_v2.load_data('mock', days=days)
        
        history = []
        for date, row in data.iterrows():
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row['open'], 2),
                "high": round(row['high'], 2),
                "low": round(row['low'], 2),
                "close": round(row['close'], 2),
                "volume": int(row['volume'])
            })
        
        return {
            "symbol": "CU",
            "data": history
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ui", response_class=HTMLResponse)
async def web_ui():
    """简单Web界面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>铜价预测 v2</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .card { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; }
            .metric { display: inline-block; margin: 10px 20px; }
            .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
            .metric-label { font-size: 12px; color: #7f8c8d; }
            .up { color: #27ae60; }
            .down { color: #e74c3c; }
            button { background: #3498db; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; margin: 5px; }
            button:hover { background: #2980b9; }
            #result { margin-top: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #34495e; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔋 铜价预测系统 v2</h1>
            
            <div class="card">
                <h3>快速预测</h3>
                <button onclick="predict(5)">5天预测</button>
                <button onclick="predict(10)">10天预测</button>
                <button onclick="predict(30)">30天预测</button>
                <button onclick="backtest()">策略回测</button>
                <div id="result"></div>
            </div>
            
            <div class="card">
                <h3>模型信息</h3>
                <div id="model-info">加载中...</div>
            </div>
        </div>
        
        <script>
            async function predict(days) {
                document.getElementById('result').innerHTML = '预测中...';
                try {
                    const response = await fetch(`/api/predict?days=${days}`);
                    const data = await response.json();
                    
                    const trendClass = data.predicted_change_pct > 0 ? 'up' : 'down';
                    const trendIcon = data.predicted_change_pct > 0 ? '📈' : '📉';
                    
                    document.getElementById('result').innerHTML = `
                        <div style="margin-top: 20px;">
                            <div class="metric">
                                <div class="metric-value">¥${data.current_price.toLocaleString()}</div>
                                <div class="metric-label">当前价格</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value ${trendClass}">¥${data.predicted_price.toLocaleString()}</div>
                                <div class="metric-label">预测价格</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value ${trendClass}">${trendIcon} ${data.predicted_change_pct}%</div>
                                <div class="metric-label">预期涨跌</div>
                            </div>
                        </div>
                        <p style="color: #7f8c8d; margin-top: 15px;">
                            趋势: <strong>${data.trend}</strong> | 
                            更新时间: ${new Date(data.timestamp).toLocaleString()}
                        </p>
                    `;
                } catch (e) {
                    document.getElementById('result').innerHTML = '预测失败: ' + e.message;
                }
            }
            
            async function backtest() {
                document.getElementById('result').innerHTML = '回测中...';
                try {
                    const response = await fetch('/api/backtest?days=365');
                    const data = await response.json();
                    
                    document.getElementById('result').innerHTML = `
                        <h4>回测结果 (1年)</h4>
                        <table>
                            <tr><th>指标</th><th>数值</th></tr>
                            <tr><td>总收益率</td><td>${data.total_return_pct}%</td></tr>
                            <tr><td>年化收益率</td><td>${data.annual_return_pct}%</td></tr>
                            <tr><td>夏普比率</td><td>${data.sharpe_ratio}</td></tr>
                            <tr><td>最大回撤</td><td>${data.max_drawdown_pct}%</td></tr>
                            <tr><td>胜率</td><td>${data.win_rate_pct}%</td></tr>
                            <tr><td>交易次数</td><td>${data.num_trades}</td></tr>
                        </table>
                    `;
                } catch (e) {
                    document.getElementById('result').innerHTML = '回测失败: ' + e.message;
                }
            }
            
            // 加载模型信息
            fetch('/api/features')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('model-info').innerHTML = `
                        <p>特征数量: <strong>${data.num_features}</strong></p>
                        <p>Top 5 重要特征:</p>
                        <ol>
                            ${data.top_features.slice(0,5).map(f => `<li>${f.feature} (${(f.importance*100).toFixed(1)}%)</li>`).join('')}
                        </ol>
                    `;
                })
                .catch(() => {
                    document.getElementById('model-info').innerHTML = '无法加载模型信息';
                });
        </script>
    </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    import uvicorn
    print("启动铜价预测API v2...")
    print("访问 http://localhost:8000/ui 查看Web界面")
    uvicorn.run(app, host="0.0.0.0", port=8000)
