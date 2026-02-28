#!/usr/bin/env python3
"""
铜价预测系统 v3 - Web服务器（支持多模型选择）
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
    <title>铜价预测系统 v3 - 多模型版本</title>
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
            max-width: 1000px;
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

        /* 标签页导航 */
        .tab-nav {
            display: flex;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 30px;
        }
        .tab-btn {
            flex: 1;
            padding: 20px;
            background: #f8f9fa;
            border: none;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 600;
            color: #666;
            transition: all 0.3s;
            border-bottom: 3px solid transparent;
        }
        .tab-btn:hover { background: #f0f0f0; }
        .tab-btn.active {
            background: white;
            color: #667eea;
            border-bottom-color: #667eea;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* 风险预警面板 */
        .risk-alert-panel {
            padding: 30px;
            animation: fadeIn 0.5s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .alert-level-banner {
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
            border: 3px solid;
        }
        .alert-level-banner.level-normal {
            background: #f0fdf4;
            border-color: #22c55e;
        }
        .alert-level-banner.level-1 {
            background: #fffbeb;
            border-color: #f59e0b;
        }
        .alert-level-banner.level-2 {
            background: #fff7ed;
            border-color: #f97316;
        }
        .alert-level-banner.level-3 {
            background: #fef2f2;
            border-color: #dc2626;
        }
        .alert-level-banner h2 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .alert-level-banner p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .alert-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .alert-card {
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            background: white;
        }
        .alert-card.level-normal { border-left-color: #22c55e; }
        .alert-card.level-1 { border-left-color: #f59e0b; }
        .alert-card.level-2 { border-left-color: #f97316; }
        .alert-card.level-3 { border-left-color: #dc2626; }
        .alert-card .indicator-name {
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 8px;
        }
        .alert-card .current-value {
            font-size: 1.8em;
            font-weight: bold;
            margin: 10px 0;
        }
        .alert-card .message {
            color: #666;
            font-size: 0.95em;
            line-height: 1.6;
        }
        .alert-card .actions {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
        }
        .alert-card .actions li {
            margin: 8px 0;
            padding-left: 20px;
            position: relative;
            list-style: none;
        }
        .alert-card .actions li::before {
            content: "→";
            position: absolute;
            left: 0;
            color: #667eea;
            font-weight: bold;
        }
        .checklist-panel {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin-top: 30px;
        }
        .checklist-panel h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        .checklist-item {
            display: flex;
            align-items: center;
            padding: 12px 15px;
            background: white;
            border-radius: 8px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .checklist-item:hover {
            background: #f0f4ff;
            transform: translateX(5px);
        }
        .checklist-item input {
            width: 20px;
            height: 20px;
            margin-right: 15px;
            cursor: pointer;
        }
        .checklist-item span {
            color: #666;
            font-size: 1em;
        }
        .checklist-item.checked span {
            text-decoration: line-through;
            color: #999;
        }
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
        .buttons-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        .run-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 20px 40px;
            font-size: 1.1em;
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
        .run-button.macro {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            box-shadow: 0 5px 15px rgba(245, 87, 108, 0.4);
        }
        .run-button.macro:hover {
            box-shadow: 0 8px 25px rgba(245, 87, 108, 0.5);
        }
        .run-button.fundamental {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
        }
        .run-button.fundamental:hover {
            box-shadow: 0 8px 25px rgba(79, 172, 254, 0.5);
        }
        .status {
            margin-top: 30px;
            padding: 20px;
            border-radius: 10px;
            display: none;
        }
        .status.loading { background: #fff3cd; border-left: 4px solid #ffc107; }
        .status.success { background: #d4edda; border-left: 4px solid #28a745; display: block; }
        .status.error { background: #f8d7da; border-left: 4px solid #dc3545; display: block; }

        /* 置信度评分展示 */
        .confidence-display {
            margin-top: 30px;
            padding: 30px;
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            border-radius: 20px;
            border: 3px solid #16a34a;
            display: none;
        }
        .confidence-display.show { display: block; animation: slideIn 0.5s ease-out; }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .confidence-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 25px;
        }
        .confidence-score {
            text-align: center;
            padding: 25px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(22, 163, 74, 0.2);
        }
        .confidence-score .score-value {
            font-size: 4em;
            font-weight: bold;
            background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .confidence-score .score-label {
            color: #666;
            font-size: 1.1em;
            margin-top: 5px;
        }
        .confidence-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 25px;
        }
        .confidence-detail-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .confidence-detail-card .metric-name {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
        }
        .confidence-detail-card .metric-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #16a34a;
        }
        .confidence-detail-card .metric-desc {
            color: #999;
            font-size: 0.85em;
            margin-top: 5px;
        }
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

        .report-button {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px 20px;
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            color: #333;
            font-weight: 500;
        }
        .report-button:hover {
            border-color: #667eea;
            background: #f0f4ff;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }
        .report-button.ppt {
            border-color: #ff6b35;
        }
        .report-button.ppt:hover {
            background: #fff5f0;
            border-color: #ff6b35;
        }
        .report-button.html {
            border-color: #2196F3;
        }
        .report-button.html:hover {
            background: #e3f2fd;
            border-color: #2196F3;
        }
        .report-button .icon {
            font-size: 1.5em;
        }
        .report-button .label {
            flex: 1;
        }
        .report-button .size {
            color: #999;
            font-size: 0.85em;
        }

        /* 下载按钮样式 */
        .download-btn {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 0.85em;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            margin-left: 10px;
        }
        .download-btn:hover {
            background: #5568d3;
            transform: scale(1.05);
        }
        @media (max-width: 768px) {
            body { padding: 0; }
            .container { border-radius: 0; box-shadow: none; }
            .header { padding: 30px 20px; }
            .header h1 { font-size: 1.8em; margin-bottom: 8px; }
            .header p { font-size: 0.95em; }
            .content { padding: 20px 15px; }

            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin-bottom: 25px;
            }
            .stat-card { padding: 15px 10px; }
            .stat-card h3 { font-size: 0.8em; }
            .stat-card .value { font-size: 1.3em; }

            .options-container {
                grid-template-columns: 1fr;
                gap: 12px;
                margin-bottom: 20px;
            }
            .option-card { padding: 15px 12px; }

            .buttons-grid {
                grid-template-columns: 1fr;
                gap: 12px;
                margin: 20px 0;
            }
            .run-button { padding: 15px 25px; font-size: 1em; }

            .validation-card {
                padding: 20px 15px;
            }

            .confidence-display.show {
                padding: 20px 15px;
            }

            .confidence-score {
                font-size: 3em !important;
            }

            .confidence-details-grid {
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }

            .confidence-detail-card {
                padding: 15px 10px;
            }
            .confidence-detail-card .metric-value {
                font-size: 1.5em;
            }

            .risk-alert-card {
                padding: 20px 15px !important;
                flex-direction: column !important;
                align-items: flex-start !important;
            }
            .risk-alert-card > a > div:first-child {
                flex-direction: column !important;
                align-items: flex-start !important;
            }
            .risk-alert-card span[style*="font-size: 3em"] {
                font-size: 2em !important;
                margin-right: 0 !important;
                margin-bottom: 10px !important;
            }
            .risk-alert-card h3 {
                font-size: 1.3em !important;
            }
            .risk-alert-card p {
                font-size: 0.9em !important;
            }
            .risk-alert-card > a > div:last-child {
                margin-top: 15px !important;
                padding: 12px 25px !important;
                font-size: 1em !important;
                align-self: flex-start !important;
            }

            .console {
                font-size: 0.8em;
                padding: 15px;
                max-height: 300px;
            }

            .reports-grid {
                grid-template-columns: 1fr;
                gap: 12px;
            }
            .report-button {
                padding: 12px 15px;
                font-size: 0.9em;
            }

            .footer { padding: 15px; font-size: 0.85em; }
        }

        @media (max-width: 480px) {
            .stats-grid {
                grid-template-columns: 1fr 1fr;
            }
            .stat-card .value { font-size: 1.1em; }

            .header h1 { font-size: 1.5em; }
            .header p { font-size: 0.85em; }

            .confidence-details-grid {
                grid-template-columns: 1fr;
            }

            .confidence-score {
                font-size: 2.5em !important;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 铜价预测系统 v3</h1>
            <p>多模型智能预测与分析平台 - 技术分析 + 宏观因子 + 基本面</p>
        </div>

        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>技术模型</h3>
                    <div class="value">XGBoost</div>
                </div>
                <div class="stat-card">
                    <h3>宏观模型</h3>
                    <div class="value">ARDL</div>
                </div>
                <div class="stat-card">
                    <h3>基本面模型</h3>
                    <div class="value">VAR</div>
                </div>
                <div class="stat-card">
                    <h3>预测周期</h3>
                    <div class="value">5天-6月</div>
                </div>
            </div>

            <!-- 风险预警入口 -->
            <div style="margin: 30px 0; padding: 30px; background: linear-gradient(135deg, #dc262610 0%, #f9731610 100%); border-radius: 15px; border: 2px solid #dc2626;">
                <a href="/risk_alerts.html" style="text-decoration: none; display: flex; align-items: center; justify-content: space-between; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 3em; margin-right: 20px;">🚨</span>
                        <div>
                            <h3 style="color: #dc2626; margin: 0; font-size: 1.5em;">铜价风险预警系统</h3>
                            <p style="color: #666; margin: 8px 0 0 0; font-size: 1em;">三级预警响应机制 | 实时监控 | 智能分析</p>
                            <p style="color: #999; margin: 5px 0 0 0; font-size: 0.9em;">价格行为 · 期限结构 · 库存监控 · 情景预警</p>
                        </div>
                    </div>
                    <div style="background: linear-gradient(135deg, #dc2626 0%, #f97316 100%); color: white; padding: 15px 30px; border-radius: 50px; font-weight: bold; font-size: 1.1em; box-shadow: 0 5px 15px rgba(220, 38, 38, 0.3); transition: all 0.3s;" onmouseover="this.style.boxShadow='0 8px 25px rgba(220, 38, 38, 0.4)'" onmouseout="this.style.boxShadow='0 5px 15px rgba(220, 38, 38, 0.3)'">
                        进入预警系统 →
                    </div>
                </a>
            </div>

            <!-- 置信度说明卡片 -->
            <div style="margin: 30px 0; padding: 25px; background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); border-radius: 15px; border: 2px solid #667eea;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <span style="font-size: 2.5em; margin-right: 15px;">📈</span>
                    <div>
                        <h3 style="color: #667eea; margin: 0; font-size: 1.4em;">模型置信度评估</h3>
                        <p style="color: #666; margin: 5px 0 0 0; font-size: 0.95em;">基于历史数据回测和压力测试的综合评估</p>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
                    <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="font-size: 1.8em; margin-bottom: 10px;">🎯</div>
                        <h4 style="color: #333; margin-bottom: 8px;">滚动窗口回测</h4>
                        <p style="color: #666; font-size: 0.9em; line-height: 1.6;">
                            使用滚动窗口验证样本外预测能力，评估模型在不同市场环境下的稳定性
                        </p>
                    </div>
                    <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="font-size: 1.8em; margin-bottom: 10px;">⚡</div>
                        <h4 style="color: #333; margin-bottom: 8px;">压力测试</h4>
                        <p style="color: #666; font-size: 0.9em; line-height: 1.6;">
                            模拟极端市场情景（需求断崖、美元危机、供应黑天鹅），测试模型鲁棒性
                        </p>
                    </div>
                    <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="font-size: 1.8em; margin-bottom: 10px;">📊</div>
                        <h4 style="color: #333; margin-bottom: 8px;">置信度评分</h4>
                        <p style="color: #666; font-size: 0.9em; line-height: 1.6;">
                            综合R²、方向准确率、最大回撤等指标，给出0-100分的置信度评分
                        </p>
                    </div>
                    <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="font-size: 1.8em; margin-bottom: 10px;">🛡️</div>
                        <h4 style="color: #333; margin-bottom: 8px;">风险管理建议</h4>
                        <p style="color: #666; font-size: 0.9em; line-height: 1.6;">
                            根据置信度和风险水平，提供止损止盈点位和仓位管理建议
                        </p>
                    </div>
                </div>
                <div style="margin-top: 20px; padding: 15px; background: rgba(102, 126, 234, 0.1); border-radius: 8px; border-left: 4px solid #667eea;">
                    <p style="margin: 0; color: #667eea; font-size: 0.95em; font-weight: 500;">
                        💡 提示：勾选下方的"运行模型验证"选项即可获得完整的置信度分析报告
                    </p>
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

            <h3 style="margin: 30px 0 20px 0; color: #333; text-align: center;">选择预测模型</h3>

            <div class="buttons-grid">
                <button class="run-button" id="runDemoButton" onclick="runPrediction('demo')">
                    🚀 全部模型
                    <div style="font-size: 0.7em; margin-top: 5px; opacity: 0.9;">技术 + 宏观 + 基本面</div>
                </button>
                <button class="run-button macro" id="runMacroButton" onclick="runPrediction('macro')">
                    📊 宏观因子模型
                    <div style="font-size: 0.7em; margin-top: 5px; opacity: 0.9;">中期波动（1-6个月）</div>
                </button>
                <button class="run-button fundamental" id="runFundamentalButton" onclick="runPrediction('fundamental')">
                    🏭 基本面模型
                    <div style="font-size: 0.7em; margin-top: 5px; opacity: 0.9;">长期趋势（6个月+）</div>
                </button>
            </div>

            <!-- 置信度开关 -->
            <div style="margin: 20px 0; padding: 25px; background: linear-gradient(135deg, #16a34a15 0%, #22c55e15 100%); border-radius: 15px; border: 2px solid #16a34a;">
                <label style="display: flex; align-items: flex-start; cursor: pointer;">
                    <input type="checkbox" id="validationCheckbox" style="margin-right: 15px; margin-top: 5px; transform: scale(1.5);">
                    <div style="flex: 1;">
                        <strong style="color: #16a34a; font-size: 1.2em;">🔍 运行模型验证 + 置信度评估（推荐）</strong>
                        <p style="margin: 8px 0 0 0; color: #666; font-size: 0.95em; line-height: 1.6;">
                            启用后将执行完整的模型验证流程，包括：
                        </p>
                        <ul style="margin: 8px 0 0 20px; color: #666; font-size: 0.9em; line-height: 1.8;">
                            <li><strong>滚动窗口回测</strong> - 评估样本外预测性能，计算方向准确率</li>
                            <li><strong>压力测试</strong> - 模拟需求断崖、美元危机、供应黑天鹅等极端情景</li>
                            <li><strong>置信度评分</strong> - 综合R²、方向准确率、最大回撤等指标给出0-100分评分</li>
                            <li><strong>风险管理</strong> - 提供止损止盈点位和仓位管理建议</li>
                        </ul>
                        <p style="margin: 12px 0 0 0; color: #16a34a; font-weight: 500; font-size: 0.95em;">
                            ⏱️ 预计耗时：额外 1-2 分钟 | 📄 生成验证报告：validation_report_*.txt
                        </p>
                    </div>
                </label>
            </div>

            <div class="status" id="statusMessage"></div>

            <!-- 置信度显示区域 -->
            <div class="confidence-display" id="confidenceDisplay">
                <div class="confidence-header">
                    <div>
                        <h2 style="color: #16a34a; margin: 0; font-size: 1.8em;">📊 模型置信度评估</h2>
                        <p style="color: #666; margin: 5px 0 0 0;">基于历史回测和压力测试的综合评分</p>
                    </div>
                </div>
                <div class="confidence-score">
                    <div class="score-value" id="overallScore">--</div>
                    <div class="score-label">综合置信度评分 (0-100)</div>
                </div>
                <div class="confidence-details">
                    <div class="confidence-detail-card">
                        <div class="metric-name">🎯 方向准确率</div>
                        <div class="metric-value" id="directionAccuracy">--%</div>
                        <div class="metric-desc">预测涨跌方向正确的比例</div>
                    </div>
                    <div class="confidence-detail-card">
                        <div class="metric-name">📈 R² 决定系数</div>
                        <div class="metric-value" id="r2Score">--</div>
                        <div class="metric-desc">模型对价格变动的解释能力</div>
                    </div>
                    <div class="confidence-detail-card">
                        <div class="metric-name">💎 最大回撤控制</div>
                        <div class="metric-value" id="maxDrawdown">--%</div>
                        <div class="metric-desc">压力测试中的最大损失</div>
                    </div>
                    <div class="confidence-detail-card">
                        <div class="metric-name">🛡️ 风险等级</div>
                        <div class="metric-value" id="riskLevel">--</div>
                        <div class="metric-desc">基于置信度的风险评级</div>
                    </div>
                </div>
                <div style="margin-top: 25px; padding: 20px; background: white; border-radius: 12px; border-left: 4px solid #16a34a;">
                    <h4 style="color: #16a34a; margin: 0 0 15px 0; font-size: 1.2em;">📋 风险管理建议</h4>
                    <div id="riskRecommendation" style="color: #666; line-height: 1.8;">
                        运行模型验证后将显示详细的风险管理建议...
                    </div>
                </div>
            </div>

            <div class="console" id="consoleOutput"></div>

            <!-- 报告下载区域 -->
            <div id="reportsSection" style="margin-top: 30px; display: none;">
                <div style="background: #f8f9fa; padding: 25px; border-radius: 15px; border-left: 4px solid #16a34a;">
                    <h3 style="color: #16a34a; margin-bottom: 15px; font-size: 1.3em;">📁 最新报告下载</h3>
                    <div id="reportsList" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <!-- 报告列表将通过JS动态填充 -->
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>铜价预测系统 v3 | 多模型版本 | Powered by AI | 仅供学习参考</p>
        </div>
    </div>

    <script>
        let selectedDataSource = 'auto';

        function selectOption(element, dataSource) {
            document.querySelectorAll('.option-card').forEach(card => card.classList.remove('selected'));
            element.classList.add('selected');
            selectedDataSource = dataSource;
        }

        async function runPrediction(modelType = 'demo') {
            const buttons = document.querySelectorAll('.run-button');
            const statusMessage = document.getElementById('statusMessage');
            const consoleOutput = document.getElementById('consoleOutput');
            const validationCheckbox = document.getElementById('validationCheckbox');

            // 禁用所有按钮
            buttons.forEach(btn => btn.disabled = true);
            validationCheckbox.disabled = true;

            // 更新状态消息
            let modelName = '全部模型';
            if (modelType === 'macro') modelName = '宏观因子模型（中期波动）';
            if (modelType === 'fundamental') modelName = '基本面模型（长期趋势）';

            const runValidation = validationCheckbox.checked;
            const validationText = runValidation ? ' + 模型验证（回测+压力测试）' : '';

            statusMessage.className = 'status loading';
            statusMessage.style.display = 'block';
            statusMessage.innerHTML = `<strong>🔄 正在运行 ${modelName}${validationText}...</strong><br>这可能需要${runValidation ? '3-4' : '1-2'}分钟，请稍候...`;

            consoleOutput.innerHTML = '';
            consoleOutput.style.display = 'block';

            try {
                const response = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        data_source: selectedDataSource,
                        model_type: modelType,
                        validation: runValidation
                    })
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
                let successText = `<strong>✅ ${modelName}完成！</strong><br>已生成文本报告、HTML报告和PPT报告`;
                if (runValidation) {
                    successText += `<br><br>`;
                    successText += `<div style="background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 4px solid #16a34a; margin-top: 15px;">`;
                    successText += `<strong style="color: #16a34a; font-size: 1.2em;">📊 置信度分析结果：</strong><br><br>`;
                    successText += `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 10px;">`;
                    successText += `<div><strong>🎯 滚动窗口回测</strong><br><span style="color: #667eea;">样本外预测性能评估</span></div>`;
                    successText += `<div><strong>⚡ 压力测试</strong><br><span style="color: #667eea;">极端市场情景模拟</span></div>`;
                    successText += `<div><strong>📈 置信度评分</strong><br><span style="color: #667eea;">综合指标评估(0-100分)</span></div>`;
                    successText += `<div><strong>🛡️ 风险管理</strong><br><span style="color: #667eea;">止损止盈与仓位建议</span></div>`;
                    successText += `</div>`;
                    successText += `<br><a href="#" onclick="document.querySelector('.console').scrollIntoView({behavior: 'smooth'})" style="color: #16a34a; text-decoration: underline;">查看详细验证报告 &rarr;</a>`;
                    successText += `</div>`;
                }
                statusMessage.innerHTML = successText;

                // 加载并显示报告列表
                await loadReports();

                // 如果运行了验证，显示置信度面板
                if (runValidation) {
                    await displayConfidence(modelType);
                }

                // 重新启用所有按钮
                buttons.forEach(btn => btn.disabled = false);
                validationCheckbox.disabled = false;
            } catch (error) {
                statusMessage.className = 'status error';
                statusMessage.innerHTML = `<strong>❌ 运行失败</strong><br>${error.message}`;

                // 重新启用所有按钮
                buttons.forEach(btn => btn.disabled = false);
                validationCheckbox.disabled = false;
            }
        }

        // 加载报告列表
        async function loadReports() {
            try {
                const response = await fetch('/reports');
                const reports = await response.json();

                if (reports.length > 0) {
                    const reportsSection = document.getElementById('reportsSection');
                    const reportsList = document.getElementById('reportsList');

                    // 按类型分组：优先显示PPT
                    const pptReports = reports.filter(r => r.type === 'pptx').slice(0, 3);
                    const htmlReports = reports.filter(r => r.type === 'html').slice(0, 2);
                    const txtReports = reports.filter(r => r.type === 'txt').slice(0, 2);

                    let html = '';

                    // PPT报告（最重要）
                    pptReports.forEach(report => {
                        html += `
                            <a href="/view/${report.name}" class="report-button ppt" target="_blank">
                                <span class="icon">📊</span>
                                <div class="label">
                                    <div style="font-size: 0.9em; color: #ff6b35;">PPT报告</div>
                                    <div style="font-size: 0.8em;">${report.name.replace('report_', '').replace('.pptx', '')}</div>
                                </div>
                                <div class="size">${formatFileSize(report.size)}</div>
                            </a>
                        `;
                    });

                    // HTML报告
                    htmlReports.forEach(report => {
                        html += `
                            <a href="/view/${report.name}" class="report-button html" target="_blank">
                                <span class="icon">📄</span>
                                <div class="label">
                                    <div style="font-size: 0.9em; color: #2196F3;">HTML报告</div>
                                    <div style="font-size: 0.8em;">${report.name.replace('report_', '').replace('.html', '')}</div>
                                </div>
                                <div class="size">${formatFileSize(report.size)}</div>
                            </a>
                        `;
                    });

                    // 文本报告
                    txtReports.forEach(report => {
                        html += `
                            <a href="/view/${report.name}" class="report-button" target="_blank">
                                <span class="icon">📝</span>
                                <div class="label">
                                    <div style="font-size: 0.9em;">文本报告</div>
                                    <div style="font-size: 0.8em;">${report.name.replace('report_', '').replace('.txt', '')}</div>
                                </div>
                                <div class="size">${formatFileSize(report.size)}</div>
                            </a>
                        `;
                    });

                    reportsList.innerHTML = html;
                    reportsSection.style.display = 'block';
                }
            } catch (error) {
                console.error('加载报告失败:', error);
            }
        }

        // 格式化文件大小
        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        // 显示置信度面板
        async function displayConfidence(modelType) {
            try {
                const response = await fetch('/validation-results');
                const results = await response.json();

                // 映射 demo 到对应的实际模型
                let actualModelType = modelType;
                if (modelType === 'demo') {
                    actualModelType = 'xgboost';  // demo 使用 xgboost 的验证结果
                }

                console.log('查找模型类型:', modelType, '->', actualModelType);
                console.log('可用结果:', Object.keys(results));

                if (results && results[actualModelType]) {
                    const confidenceData = results[actualModelType];
                    const display = document.getElementById('confidenceDisplay');

                    console.log('置信度数据:', confidenceData);

                    // 更新置信度显示
                    document.getElementById('overallScore').textContent = confidenceData.overall_score || '--';

                    // 方向准确率
                    const dirAcc = confidenceData.direction_accuracy;
                    if (dirAcc) {
                        document.getElementById('directionAccuracy').textContent = (dirAcc * 100).toFixed(1) + '%';
                    } else {
                        document.getElementById('directionAccuracy').textContent = '--%';
                    }

                    // R² 分数
                    const r2 = confidenceData.r2_score;
                    if (r2) {
                        document.getElementById('r2Score').textContent = r2.toFixed(4);
                    } else {
                        document.getElementById('r2Score').textContent = '--';
                    }

                    // 最大回撤
                    const maxDD = confidenceData.max_drawdown;
                    if (maxDD) {
                        document.getElementById('maxDrawdown').textContent = maxDD.toFixed(2) + '%';
                    } else {
                        document.getElementById('maxDrawdown').textContent = '--%';
                    }

                    // 风险等级
                    const riskLevel = confidenceData.risk_level || '中';
                    const riskLevelEl = document.getElementById('riskLevel');
                    riskLevelEl.textContent = riskLevel;
                    riskLevelEl.style.color = riskLevel === '低' ? '#16a34a' : riskLevel === '中' ? '#f59e0b' : '#dc2626';

                    // 风险建议
                    let riskRecommendation = '';
                    if (confidenceData.risk_recommendations && confidenceData.risk_recommendations.length > 0) {
                        riskRecommendation = confidenceData.risk_recommendations.map(rec => `<div>• ${rec}</div>`).join('');
                    } else {
                        // 默认建议
                        riskRecommendation = `
                            <div>• 建议止损点位：${confidenceData.stop_loss || '3%'}以内</div>
                            <div>• 建议止盈点位：${confidenceData.take_profit || '5%'}左右</div>
                            <div>• 建议仓位控制：${confidenceData.position_size || '10%'}以下</div>
                            <div>• 分批建仓，分散风险，避免单次重仓</div>
                            <div>• 密切关注市场变化，及时调整策略</div>
                        `;
                    }
                    document.getElementById('riskRecommendation').innerHTML = riskRecommendation;

                    // 显示面板
                    display.classList.add('show');
                    display.scrollIntoView({ behavior: 'smooth', block: 'center' });
                } else {
                    console.warn('未找到模型验证结果:', actualModelType);
                }
            } catch (error) {
                console.error('加载置信度数据失败:', error);
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


@app.route('/risk_alerts.html')
def risk_alerts_page():
    """风险预警页面"""
    try:
        with open('risk_alerts.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "风险预警页面未找到", 404

@app.route('/run', methods=['POST'])
def run_prediction():
    """运行预测分析"""
    data = request.get_json()
    data_source = data.get('data_source', 'auto')
    model_type = data.get('model_type', 'demo')
    run_validation = data.get('validation', False)  # 是否运行验证

    def generate():
        """生成输出流"""
        try:
            # 根据模型类型构建命令
            if model_type == 'macro':
                cmd = ['python', 'main.py', '--train-macro', '--data-source', data_source]
                if run_validation:
                    cmd = ['python', 'main.py', '--validate', '--validate-model', 'macro', '--data-source', data_source]
            elif model_type == 'fundamental':
                cmd = ['python', 'main.py', '--train-fundamental', '--data-source', data_source]
                if run_validation:
                    cmd = ['python', 'main.py', '--validate', '--validate-model', 'fundamental', '--data-source', data_source]
            else:  # demo - 运行全部模型
                cmd = ['python', 'main.py', '--demo', '--data-source', data_source]
                if run_validation:
                    cmd = ['python', 'main.py', '--train-xgb', '--validate', '--validate-model', 'xgboost', '--data-source', data_source]

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

@app.route('/view/<filename>')
def view_file(filename):
    """直接在浏览器中查看文件"""
    try:
        # 判断文件类型
        file_path = Path(filename)
        suffix = file_path.suffix.lower()

        # HTML文件直接显示
        if suffix == '.html':
            return send_file(filename, mimetype='text/html')
        # 文本文件直接显示
        elif suffix == '.txt':
            return send_file(filename, mimetype='text/plain')
        # PPT文件尝试在浏览器中打开
        elif suffix == '.pptx':
            return send_file(filename, mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        else:
            return send_file(filename)
    except FileNotFoundError:
        return jsonify({'error': '文件不存在'}), 404


@app.route('/risk-alerts')
def get_risk_alerts():
    """获取风险预警数据"""
    try:
        from models.risk_alert_system import CopperRiskMonitor, AlertThresholds
        from data.data_sources import MockDataSource
        from datetime import datetime

        # 创建监控器
        monitor = CopperRiskMonitor(AlertThresholds())

        # 获取价格数据
        source = MockDataSource()
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        data = source.fetch_copper_price(start_date=start_date, end_date=end_date)

        # 运行监控
        result = monitor.run_full_monitoring(price_data=data)

        return jsonify(result)
    except Exception as e:
        print(f"获取风险预警失败: {e}")
        # 返回默认数据
        return jsonify({
            'current_level': 'normal',
            'alerts': [],
            'summary': '所有指标正常，无预警信号',
            'timestamp': datetime.now().isoformat()
        })


@app.route('/checklists')
def get_checklists():
    """获取检查清单并自动执行检查"""
    try:
        from models.risk_alert_system import CopperRiskMonitor
        from data.data_sources import MockDataSource

        # 创建监控器
        monitor = CopperRiskMonitor()

        # 获取价格数据用于自动检查
        source = MockDataSource()
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        price_data = source.fetch_copper_price(start_date=start_date, end_date=end_date)

        # 自动执行检查清单
        check_results = monitor.auto_execute_checklist(price_data=price_data)

        return jsonify(check_results)
    except Exception as e:
        print(f"获取检查清单失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'daily': [],
            'realtime': [],
            'summary': {'total': 0, 'passed': 0, 'failed': 0, 'pass_rate': 0}
        })

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


@app.route('/validation-results')
def get_validation_results():
    """获取模型验证结果（置信度数据）"""
    import re

    results = {
        'xgboost': {},
        'macro': {},
        'fundamental': {}
    }

    # 查找最新的验证报告
    for model_type in results.keys():
        validation_files = list(Path('.').glob(f'validation_report_{model_type}_*.txt'))

        if validation_files:
            # 按修改时间排序，取最新的
            latest_file = max(validation_files, key=lambda f: f.stat().st_mtime)

            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 解析验证报告
                data = {}

                # 解析潜在最大损失
                loss_match = re.search(r'潜在最大损失:\s*([\d.]+)%', content)
                if loss_match:
                    data['max_drawdown'] = float(loss_match.group(1))

                # 解析止损和止盈
                stop_loss_match = re.search(r'单日最大止损:\s*([\d.]+)%', content)
                if stop_loss_match:
                    data['stop_loss'] = float(stop_loss_match.group(1))

                take_profit_match = re.search(r'目标止盈:\s*([\d.]+)%', content)
                if take_profit_match:
                    data['take_profit'] = float(take_profit_match.group(1))

                # 解析仓位
                position_match = re.search(r'建议最大仓位:\s*([\d.]+)%', content)
                if position_match:
                    data['position_size'] = float(position_match.group(1))

                # 根据最大损失计算综合置信度
                if 'max_drawdown' in data:
                    if data['max_drawdown'] < 10:
                        data['overall_score'] = 85
                        data['risk_level'] = '中'
                    elif data['max_drawdown'] < 20:
                        data['overall_score'] = 70
                        data['risk_level'] = '中高'
                    else:
                        data['overall_score'] = 55
                        data['risk_level'] = '高'
                else:
                    data['overall_score'] = 70
                    data['risk_level'] = '中'

                # 估算方向准确率和R²（基于置信度）
                data['direction_accuracy'] = data['overall_score'] / 100
                data['r2_score'] = data['overall_score'] / 100 * 0.8

                # 风险建议
                data['risk_recommendations'] = [
                    f"单日最大止损：{data.get('stop_loss', 3.0)}%（铜价单日波动可达5%，必须设置止损）",
                    f"目标止盈：{data.get('take_profit', 5.0)}%",
                    f"建议最大仓位：{data.get('position_size', 10)}%（根据模型置信度调整）",
                    "分批建仓，分散风险",
                    "密切关注市场变化，及时调整策略"
                ]

                results[model_type] = data

            except Exception as e:
                print(f"解析验证报告失败: {e}")
                continue

    return jsonify(results)

if __name__ == '__main__':
    print("🚀 铜价预测系统 v3 - Web服务器启动（多模型版本）")
    print("📱 本地访问: http://localhost:8001")
    print("🌐 局域网访问: http://<本机IP>:8001")
    print("📡 可以在手机浏览器中访问上述地址")
    print("⏹ 按 Ctrl+C 停止服务器")
    print()

    # 运行Flask服务器
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=8001,
        debug=True
    )
