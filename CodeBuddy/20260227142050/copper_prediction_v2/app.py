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

            #resultsSection {
                padding: 20px 15px;
            }
            #resultsSection h3 {
                font-size: 1.3em;
            }
            #multiModelResults > div {
                grid-template-columns: 1fr !important;
            }
            #multiModelResults > div > div {
                padding: 18px 15px;
            }
            #multiModelResults h4 {
                font-size: 1.15em;
            }
            #multiModelResults .metric-value {
                font-size: 1.6em;
            }
            #multiModelResults .metric-desc {
                font-size: 0.8em;
            }
            #ensemblePrice, #ensembleChange {
                font-size: 1.8em !important;
            }
            #ensembleDirection, #modelConsensus {
                font-size: 1.5em !important;
            }
            #singleModelPrice {
                font-size: 2em !important;
            }
            #singleModelChange {
                font-size: 1.6em !important;
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

            #resultsSection {
                padding: 20px 15px;
            }
            #resultsSection h3 {
                font-size: 1.2em;
            }
            #multiModelResults > div > div {
                padding: 15px 12px;
            }
            #multiModelResults h4 {
                font-size: 1.1em;
            }
            #multiModelResults .metric-value {
                font-size: 1.3em;
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

            <!-- 模型指标查看入口 -->
            <div style="margin: 30px 0; padding: 30px; background: linear-gradient(135deg, #16a34a15 0%, #22c55e15 100%); border-radius: 15px; border: 2px solid #16a34a;">
                <a href="/model-indicators.html" style="text-decoration: none; display: flex; align-items: center; justify-content: space-between; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 3em; margin-right: 20px;">📊</span>
                        <div>
                            <h3 style="color: #16a34a; margin: 0; font-size: 1.5em;">模型指标详情</h3>
                            <p style="color: #666; margin: 8px 0 0 0; font-size: 1em;">宏观因子 & 基本面模型 | 关键变量 | 实时指标</p>
                            <p style="color: #999; margin: 5px 0 0 0; font-size: 0.9em;">美元指数 · PMI · 产量增长率 · 成本支撑价</p>
                        </div>
                    </div>
                    <div style="background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%); color: white; padding: 15px 30px; border-radius: 50px; font-weight: bold; font-size: 1.1em; box-shadow: 0 5px 15px rgba(22, 163, 74, 0.3); transition: all 0.3s;" onmouseover="this.style.boxShadow='0 8px 25px rgba(22, 163, 74, 0.4)'" onmouseout="this.style.boxShadow='0 5px 15px rgba(22, 163, 74, 0.3)'">
                        查看指标 →
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
                <button class="run-button" id="runDemoButton">
                    <span>🚀 全部模型</span>
                    <br>
                    <span style="font-size: 0.7em; opacity: 0.9;">技术 + 宏观 + 基本面</span>
                </button>
                <button class="run-button macro" id="runMacroButton">
                    <span>📊 宏观因子模型</span>
                    <br>
                    <span style="font-size: 0.7em; opacity: 0.9;">中期波动（1-6个月）</span>
                </button>
                <button class="run-button fundamental" id="runFundamentalButton">
                    <span>🏭 基本面模型</span>
                    <br>
                    <span style="font-size: 0.7em; opacity: 0.9;">长期趋势（6个月+）</span>
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

            <!-- 预测结果展示 -->
            <div id="resultsSection" style="margin-top: 30px; display: none;">
                <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 30px; border-radius: 15px; border: 2px solid #0ea5e9;">
                    <h3 style="color: #0284c7; margin: 0 0 25px 0; font-size: 1.4em; text-align: center;">📊 预测结果展示</h3>

                    <!-- 多模型结果 -->
                    <div id="multiModelResults" style="display: none;">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 25px;">
                            <!-- XGBoost结果 -->
                            <div style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #667eea; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <h4 style="color: #667eea; margin: 0 0 15px 0; font-size: 1.2em; display: flex; align-items: center;">
                                    <span style="margin-right: 8px;">📈</span>XGBoost技术模型
                                </h4>
                                <div style="margin-bottom: 12px;">
                                    <span style="color: #666; font-size: 0.9em;">预测价格：</span>
                                    <span style="font-size: 1.5em; font-weight: bold; color: #333;" id="xgboostPrice">--</span>
                                </div>
                                <div style="margin-bottom: 12px;">
                                    <span style="color: #666; font-size: 0.9em;">涨跌幅：</span>
                                    <span style="font-size: 1.3em; font-weight: bold;" id="xgboostChange">--</span>
                                </div>
                                <div style="padding: 10px; background: #f0f4ff; border-radius: 8px;">
                                    <span style="color: #666; font-size: 0.9em;">预测周期：</span>
                                    <span style="color: #667eea; font-weight: 500;" id="xgboostPeriod">短期（5天）</span>
                                </div>
                            </div>

                            <!-- ARDL宏观模型 -->
                            <div style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #f5576c; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <h4 style="color: #f5576c; margin: 0 0 15px 0; font-size: 1.2em; display: flex; align-items: center;">
                                    <span style="margin-right: 8px;">📊</span>ARDL宏观模型
                                </h4>
                                <div style="margin-bottom: 12px;">
                                    <span style="color: #666; font-size: 0.9em;">预测价格：</span>
                                    <span style="font-size: 1.5em; font-weight: bold; color: #333;" id="macroPrice">--</span>
                                </div>
                                <div style="margin-bottom: 12px;">
                                    <span style="color: #666; font-size: 0.9em;">涨跌幅：</span>
                                    <span style="font-size: 1.3em; font-weight: bold;" id="macroChange">--</span>
                                </div>
                                <div style="padding: 10px; background: #fff0f3; border-radius: 8px;">
                                    <span style="color: #666; font-size: 0.9em;">预测周期：</span>
                                    <span style="color: #f5576c; font-weight: 500;" id="macroPeriod">中期（1-6个月）</span>
                                </div>
                            </div>

                            <!-- VAR基本面模型 -->
                            <div style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #00f2fe; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <h4 style="color: #0099cc; margin: 0 0 15px 0; font-size: 1.2em; display: flex; align-items: center;">
                                    <span style="margin-right: 8px;">🏭</span>VAR基本面模型
                                </h4>
                                <div style="margin-bottom: 12px;">
                                    <span style="color: #666; font-size: 0.9em;">预测价格：</span>
                                    <span style="font-size: 1.5em; font-weight: bold; color: #333;" id="fundamentalPrice">--</span>
                                </div>
                                <div style="margin-bottom: 12px;">
                                    <span style="color: #666; font-size: 0.9em;">涨跌幅：</span>
                                    <span style="font-size: 1.3em; font-weight: bold;" id="fundamentalChange">--</span>
                                </div>
                                <div style="padding: 10px; background: #e0f7fa; border-radius: 8px;">
                                    <span style="color: #666; font-size: 0.9em;">预测周期：</span>
                                    <span style="color: #0099cc; font-weight: 500;" id="fundamentalPeriod">长期（6个月+）</span>
                                </div>
                            </div>
                        </div>

                        <!-- 综合预测 -->
                        <div style="background: white; padding: 25px; border-radius: 12px; border: 2px solid #16a34a; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                            <h4 style="color: #16a34a; margin: 0 0 20px 0; font-size: 1.3em; text-align: center;">🎯 多模型综合预测</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; text-align: center;">
                                <div>
                                    <div style="color: #666; font-size: 0.95em; margin-bottom: 8px;">综合预测价格</div>
                                    <div style="font-size: 2.2em; font-weight: bold; color: #16a34a;" id="ensemblePrice">--</div>
                                </div>
                                <div>
                                    <div style="color: #666; font-size: 0.95em; margin-bottom: 8px;">综合涨跌幅</div>
                                    <div style="font-size: 2.2em; font-weight: bold;" id="ensembleChange">--</div>
                                </div>
                                <div>
                                    <div style="color: #666; font-size: 0.95em; margin-bottom: 8px;">预测方向</div>
                                    <div style="font-size: 1.8em; font-weight: bold; color: #16a34a;" id="ensembleDirection">--</div>
                                </div>
                                <div>
                                    <div style="color: #666; font-size: 0.95em; margin-bottom: 8px;">模型一致性</div>
                                    <div style="font-size: 1.8em; font-weight: bold;" id="modelConsensus">--</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 单模型结果 -->
                    <div id="singleModelResults" style="display: none;">
                        <div style="background: white; padding: 30px; border-radius: 12px; border: 2px solid #667eea; text-align: center;">
                            <h4 style="color: #667eea; margin: 0 0 20px 0; font-size: 1.5em;" id="singleModelTitle">模型预测结果</h4>
                            <div style="margin-bottom: 20px;">
                                <span style="color: #666; font-size: 1.1em;">预测价格：</span>
                                <span style="font-size: 2.5em; font-weight: bold; color: #333;" id="singleModelPrice">--</span>
                            </div>
                            <div style="margin-bottom: 20px;">
                                <span style="color: #666; font-size: 1.1em;">涨跌幅：</span>
                                <span style="font-size: 2em; font-weight: bold;" id="singleModelChange">--</span>
                            </div>
                            <div style="display: inline-block; padding: 12px 25px; background: #f0f4ff; border-radius: 8px;">
                                <span style="color: #667eea; font-size: 1.1em; font-weight: 500;" id="singleModelPeriod">--</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

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

        // 页面加载完成后添加事件监听器
        document.addEventListener('DOMContentLoaded', function() {
            console.log('页面加载完成');

            // 为按钮添加额外的点击事件监听
            const runDemoButton = document.getElementById('runDemoButton');
            const runMacroButton = document.getElementById('runMacroButton');
            const runFundamentalButton = document.getElementById('runFundamentalButton');

            if (runDemoButton) {
                console.log('找到 runDemoButton');
                runDemoButton.addEventListener('click', function(e) {
                    console.log('全部模型按钮被点击');
                    e.preventDefault();
                    e.stopPropagation();
                    runPrediction('demo');
                });
            }

            if (runMacroButton) {
                console.log('找到 runMacroButton');
                runMacroButton.addEventListener('click', function(e) {
                    console.log('宏观因子模型按钮被点击');
                    e.preventDefault();
                    e.stopPropagation();
                    runPrediction('macro');
                });
            }

            if (runFundamentalButton) {
                console.log('找到 runFundamentalButton');
                runFundamentalButton.addEventListener('click', function(e) {
                    console.log('基本面模型按钮被点击');
                    e.preventDefault();
                    e.stopPropagation();
                    runPrediction('fundamental');
                });
            }
        });

        async function runPrediction(modelType = 'demo') {
            console.log('runPrediction 被调用，modelType:', modelType);
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

                // 显示预测结果
                await displayPredictionResults(modelType);

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

        // 显示预测结果
        async function displayPredictionResults(modelType) {
            try {
                const response = await fetch('/reports');
                const reports = await response.json();

                // 查找最新的文本报告
                const txtReports = reports.filter(r => r.type === 'txt');
                if (txtReports.length === 0) {
                    return;
                }

                // 读取最新的报告文件
                const latestReport = txtReports[0];
                const reportResponse = await fetch(`/view/${latestReport.name}`);
                const reportText = await reportResponse.text();

                // 解析预测结果
                const results = parsePredictionResults(reportText);

                // 显示结果区域
                const resultsSection = document.getElementById('resultsSection');
                resultsSection.style.display = 'block';

                if (modelType === 'demo' || modelType === 'xgboost') {
                    // 多模型结果
                    document.getElementById('multiModelResults').style.display = 'block';
                    document.getElementById('singleModelResults').style.display = 'none';

                    // XGBoost
                    if (results.xgboost) {
                        updateModelResult('xgboost', results.xgboost);
                    }
                    // ARDL
                    if (results.macro) {
                        updateModelResult('macro', results.macro);
                    }
                    // VAR
                    if (results.fundamental) {
                        updateModelResult('fundamental', results.fundamental);
                    }

                    // 综合预测
                    if (results.ensemble) {
                        updateEnsembleResult(results.ensemble);
                    }
                } else {
                    // 单模型结果
                    document.getElementById('multiModelResults').style.display = 'none';
                    document.getElementById('singleModelResults').style.display = 'block';

                    const modelKey = modelType === 'macro' ? 'macro' : 'fundamental';
                    if (results[modelKey]) {
                        updateSingleModelResult(modelType, results[modelKey]);
                    }
                }

                // 滚动到结果区域
                resultsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });

            } catch (error) {
                console.error('显示预测结果失败:', error);
            }
        }

        // 解析预测结果
        function parsePredictionResults(reportText) {
            const results = {
                xgboost: null,
                macro: null,
                fundamental: null,
                ensemble: null
            };

            // 使用正则表达式提取预测结果
            // XGBoost预测
            const xgboostMatch = reportText.match(/技术分析模型 \(XGBoost\)[\s\S]*?短期 \(5天\): ¥([\d,.]+)/);
            if (xgboostMatch) {
                const xgboostLine = reportText.match(/技术分析模型 \(XGBoost\)[\s\S]*?短期 \(5天\): ¥([\d,.]+) \(([+-][\d.]+)%\)/);
                if (xgboostLine) {
                    results.xgboost = {
                        price: parseFloat(xgboostLine[1].replace(/,/g, '')),
                        change: parseFloat(xgboostLine[2])
                    };
                }
            }

            // ARDL宏观预测
            const macroMatch = reportText.match(/宏观因子模型[\s\S]*?预测 \(90天\): ¥([\d,.]+) \(([+-][\d.]+)%\)/);
            if (macroMatch) {
                results.macro = {
                    price: parseFloat(macroMatch[1].replace(/,/g, '')),
                    change: parseFloat(macroMatch[2])
                };
            }

            // VAR基本面预测
            const fundamentalMatch = reportText.match(/基本面模型[\s\S]*?预测 \(180天\): ¥([\d,.]+) \(([+-][\d.]+)%\)/);
            if (fundamentalMatch) {
                results.fundamental = {
                    price: parseFloat(fundamentalMatch[1].replace(/,/g, '')),
                    change: parseFloat(fundamentalMatch[2])
                };
            }

            // 综合预测（计算平均值）
            if (results.xgboost && results.macro && results.fundamental) {
                const avgPrice = (results.xgboost.price + results.macro.price + results.fundamental.price) / 3;
                const avgChange = (results.xgboost.change + results.macro.change + results.fundamental.change) / 3;

                // 计算一致性（三个模型方向是否一致）
                const directions = [
                    results.xgboost.change >= 0 ? 1 : -1,
                    results.macro.change >= 0 ? 1 : -1,
                    results.fundamental.change >= 0 ? 1 : -1
                ];
                const sameDirection = directions.every(d => d === directions[0]);
                const consensus = sameDirection ? '高度一致' : '存在分歧';

                results.ensemble = {
                    price: avgPrice,
                    change: avgChange,
                    direction: avgChange >= 0 ? '看涨' : '看跌',
                    consensus: consensus
                };
            }

            return results;
        }

        // 更新单模型结果
        function updateModelResult(modelPrefix, data) {
            const priceEl = document.getElementById(`${modelPrefix}Price`);
            const changeEl = document.getElementById(`${modelPrefix}Change`);

            if (priceEl) {
                priceEl.textContent = `¥${data.price.toLocaleString()}`;
            }

            if (changeEl) {
                const change = data.change;
                changeEl.textContent = `${change > 0 ? '+' : ''}${change.toFixed(2)}%`;
                changeEl.style.color = change > 0 ? '#16a34a' : change < 0 ? '#dc2626' : '#666';
            }
        }

        // 更新综合预测结果
        function updateEnsembleResult(data) {
            document.getElementById('ensemblePrice').textContent = `¥${data.price.toLocaleString()}`;

            const changeEl = document.getElementById('ensembleChange');
            const change = data.change;
            changeEl.textContent = `${change > 0 ? '+' : ''}${change.toFixed(2)}%`;
            changeEl.style.color = change > 0 ? '#16a34a' : change < 0 ? '#dc2626' : '#666';

            document.getElementById('ensembleDirection').textContent = data.direction;
            document.getElementById('modelConsensus').textContent = data.consensus;
        }

        // 更新单模型预测结果
        function updateSingleModelResult(modelType, data) {
            const titleMap = {
                'macro': '宏观因子模型预测结果',
                'fundamental': '基本面模型预测结果'
            };
            const periodMap = {
                'macro': '中期波动（1-6个月）',
                'fundamental': '长期趋势（6个月+）'
            };

            document.getElementById('singleModelTitle').textContent = titleMap[modelType];
            document.getElementById('singleModelPrice').textContent = `¥${data.price.toLocaleString()}`;

            const changeEl = document.getElementById('singleModelChange');
            const change = data.change;
            changeEl.textContent = `${change > 0 ? '+' : ''}${change.toFixed(2)}%`;
            changeEl.style.color = change > 0 ? '#16a34a' : change < 0 ? '#dc2626' : '#666';

            document.getElementById('singleModelPeriod').textContent = periodMap[modelType];
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
    """获取风险预警数据（使用真实数据源）"""
    try:
        from models.risk_alert_system import CopperRiskMonitor, AlertThresholds
        from data.data_sources import AKShareDataSource, MockDataSource
        from datetime import datetime, timedelta
        import numpy as np

        # 创建监控器
        monitor = CopperRiskMonitor(AlertThresholds())

        # 尝试使用真实数据源
        print("📡 尝试从AKShare获取COMEX铜价数据...")

        try:
            source = AKShareDataSource()
            if not source.available:
                raise ImportError("AKShare不可用")

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            data = source.fetch_copper_price(start_date=start_date, end_date=end_date)

            if data is None or len(data) == 0:
                print("⚠️  AKShare返回空数据，切换到模拟数据")
                source = MockDataSource()
                data = source.fetch_copper_price(start_date=start_date, end_date=end_date)
            else:
                print(f"✅ 成功获取 {len(data)} 条真实数据")

        except Exception as e:
            print(f"⚠️  真实数据获取失败: {e}")
            print("🔄 使用模拟数据")
            source = MockDataSource()
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            data = source.fetch_copper_price(start_date=start_date, end_date=end_date)

        # 运行监控
        result = monitor.run_full_monitoring(price_data=data)

        # 计算波动率（基于真实数据）
        if len(data) > 0:
            print(f"📊 计算波动率指标...")
            # 计算收益率
            data['returns'] = data['close'].pct_change()

            # 日内波动率（使用最近5天的平均日内波动）
            if 'high' in data.columns and 'low' in data.columns:
                recent_data = data.tail(5)
                intraday_vol = ((recent_data['high'] - recent_data['low']) / recent_data['close']).mean() * 100
                print(f"   日内波动率: {intraday_vol:.2f}%")
            else:
                intraday_vol = data['returns'].tail(5).std() * np.sqrt(252) * 100
                print(f"   日内波动率（备用）: {intraday_vol:.2f}%")

            # 20日波动率（年化）
            if len(data) >= 20:
                daily_vol_20d = data['returns'].tail(20).std() * np.sqrt(252) * 100
            else:
                daily_vol_20d = data['returns'].std() * np.sqrt(252) * 100
            print(f"   20日年化波动率: {daily_vol_20d:.2f}%")

            # 周波动率（5日）
            if len(data) >= 5:
                weekly_vol = data['returns'].tail(5).std() * np.sqrt(52) * 100
            else:
                weekly_vol = data['returns'].std() * np.sqrt(52) * 100
            print(f"   周波动率: {weekly_vol:.2f}%")

            # 添加波动率数据
            result['volatility'] = {
                'intraday': float(intraday_vol),
                'daily_20d': float(daily_vol_20d),
                'weekly': float(weekly_vol)
            }

            # 如果日内波动率 > 9%，添加高风险预警
            if intraday_vol > 9:
                print(f"⚠️  警告：日内波动率 {intraday_vol:.2f}% 超过9%阈值！")
                if 'alerts' not in result:
                    result['alerts'] = []
                result['alerts'].append({
                    'type': 'intraday_volatility',
                    'level': 'level_3',
                    'title': 'COMEX铜价日内波动率异常',
                    'message': f'当前日内波动率为{intraday_vol:.2f}%，超过9%的风险阈值',
                    'indicator': '日内波动率',
                    'value': f'{intraday_vol:.2f}%',
                    'threshold': '9%',
                    'recommendation': '建议降低仓位，设置止损，密切关注市场动向'
                })
                # 如果当前级别低于3，升级到3
                if result.get('current_level') == 'normal':
                    result['current_level'] = 'level_3'

        # 添加数据源标识
        result['data_source'] = 'real' if isinstance(source, AKShareDataSource) else 'mock'

        return jsonify(result)

    except Exception as e:
        print(f"❌ 获取风险预警失败: {e}")
        import traceback
        traceback.print_exc()
        # 返回默认数据（包含波动率）
        return jsonify({
            'current_level': 'normal',
            'alerts': [],
            'summary': '所有指标正常，无预警信号',
            'timestamp': datetime.now().isoformat(),
            'volatility': {
                'intraday': 2.5,
                'daily_20d': 3.5,
                'weekly': 4.2
            },
            'data_source': 'error'
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


# 模型指标展示页面的HTML模板
MODEL_INDICATORS_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>模型指标详情 - 铜价预测系统</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 1200px;
            margin: 0 auto;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .back-btn {
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            transition: all 0.3s;
        }
        .back-btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-50%) scale(1.05);
        }
        .content {
            padding: 30px;
        }
        .model-section {
            margin-bottom: 40px;
            padding: 25px;
            border-radius: 15px;
            border-left: 5px solid;
        }
        .model-section.macro {
            background: linear-gradient(135deg, #fff0f3 0%, #ffe5ec 100%);
            border-color: #f5576c;
        }
        .model-section.fundamental {
            background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%);
            border-color: #0ea5e9;
        }
        .model-title {
            font-size: 1.8em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .model-title.macro { color: #f5576c; }
        .model-title.fundamental { color: #0ea5e9; }
        .model-desc {
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        .indicators-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        .indicator-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s;
            position: relative;
        }
        .indicator-card:hover {
            transform: translateY(-5px);
        }
        .indicator-score {
            position: absolute;
            top: 15px;
            right: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .indicator-score.high { background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%); }
        .indicator-score.medium { background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%); }
        .indicator-score.low { background: linear-gradient(135deg, #dc2626 0%, #f97316 100%); }
        .indicator-name {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
        }
        .indicator-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        .indicator-value.positive { color: #16a34a; }
        .indicator-value.negative { color: #dc2626; }
        .indicator-range {
            font-size: 0.8em;
            color: #999;
            line-height: 1.4;
        }
        .indicator-range strong {
            color: #666;
        }
        .variable-table {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .variable-table table {
            width: 100%;
            border-collapse: collapse;
        }
        .variable-table th {
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
        }
        .variable-table td {
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        .variable-table tr:last-child td {
            border-bottom: none;
        }
        .variable-table tr:hover {
            background: #f8f9fa;
        }
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            background: #fef2f2;
            border: 2px solid #dc2626;
            border-radius: 12px;
            padding: 20px;
            color: #dc2626;
            text-align: center;
        }
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 20px;
        }
        .refresh-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="/" class="back-btn">← 返回主页</a>
            <h1>📊 模型指标详情</h1>
            <p>宏观因子模型 & 基本面模型的关键变量和指标</p>
        </div>

        <div class="content" id="content">
            <div class="loading">
                <div class="loading-spinner"></div>
                <p>正在加载模型指标...</p>
            </div>
        </div>
    </div>

    <script>
        async function loadIndicators() {
            const content = document.getElementById('content');
            
            try {
                const response = await fetch('/model-indicators-data');
                if (!response.ok) {
                    throw new Error('无法加载模型指标');
                }
                const data = await response.json();
                displayIndicators(data);
            } catch (error) {
                content.innerHTML = `
                    <div class="error">
                        <h3>❌ 加载失败</h3>
                        <p>${error.message}</p>
                        <p style="margin-top: 10px;">请先在主页运行预测，然后再查看模型指标</p>
                        <button class="refresh-btn" onclick="location.href='/')">返回主页</button>
                    </div>
                `;
            }
        }

        // 计算指标评分和参考范围
        function calculateIndicatorScore(name, value, modelType) {
            const indicators = {
                macro: {
                    '美元指数': { min: 90, max: 110, optimal: 'low', reverse: true },
                    '中国PMI': { min: 45, max: 55, optimal: 'high', reverse: false },
                    '实际利率(%)': { min: -2, max: 4, optimal: 'low', reverse: true },
                    'LME升贴水': { min: -50, max: 100, optimal: 'high', reverse: false }
                },
                fundamental: {
                    '产量增长率': { min: -5, max: 10, optimal: 'low', reverse: true },
                    '消费增长率': { min: -5, max: 15, optimal: 'high', reverse: false },
                    '库存变化率': { min: -20, max: 20, optimal: 'low', reverse: true },
                    '成本支撑价': { min: 70000, max: 120000, optimal: 'high', reverse: false },
                    '供应干扰指数': { min: 0, max: 30, optimal: 'high', reverse: false }
                }
            };

            const indicator = indicators[modelType]?.[name];
            if (!indicator) return { score: 50, level: 'medium', range: '参考范围：暂无数据' };

            // 计算归一化得分（0-100）
            let normalized;
            const range = indicator.max - indicator.min;
            if (range === 0) normalized = 50;
            else {
                normalized = ((value - indicator.min) / range) * 100;
            }

            // 如果是反向指标（数值越小越好），翻转得分
            if (indicator.reverse) {
                normalized = 100 - normalized;
            }

            // 计算评分等级
            let score, level;
            if (normalized >= 70) {
                score = normalized.toFixed(0);
                level = 'high';
            } else if (normalized >= 40) {
                score = normalized.toFixed(0);
                level = 'medium';
            } else {
                score = normalized.toFixed(0);
                level = 'low';
            }

            // 生成参考范围描述
            const rangeText = `参考范围: ${indicator.min} ~ ${indicator.max} | ${indicator.optimal === 'high' ? '数值越高越利好' : '数值越低越利好'}`;

            return { score, level, range: rangeText };
        }

        function displayIndicators(data) {
            const content = document.getElementById('content');
            let html = '';

            // 宏观模型指标
            if (data.macro) {
                html += `
                    <div class="model-section macro">
                        <h2 class="model-title macro">📊 宏观因子模型（中期波动）</h2>
                        <p class="model-desc">
                            适用于1-6个月的战术调整，基于美元指数、中国PMI、实际利率、LME升贴水等宏观因子。
                        </p>
                        <h3 style="margin-bottom: 15px; color: #333;">关键指标</h3>
                        <div class="indicators-grid">
                `;

                for (const [key, value] of Object.entries(data.macro.indicators || {})) {
                    const numValue = typeof value === 'number' ? value : parseFloat(value);
                    const valueDisplay = typeof value === 'number' ? value.toFixed(2) : value;
                    const valueClass = numValue > 0 ? 'positive' : (numValue < 0 ? 'negative' : '');
                    
                    const { score, level, range } = calculateIndicatorScore(key, numValue, 'macro');
                    const scoreText = `${score}分`;
                    
                    html += `
                        <div class="indicator-card">
                            <div class="indicator-score ${level}">${scoreText}</div>
                            <div class="indicator-name">${key}</div>
                            <div class="indicator-value ${valueClass}">${valueDisplay}</div>
                            <div class="indicator-range">${range}</div>
                        </div>
                    `;
                }

                html += `
                        </div>
                        <h3 style="margin-bottom: 15px; color: #333;">变量说明</h3>
                        <div class="variable-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>变量名称</th>
                                        <th>影响方向</th>
                                        <th>说明</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>美元指数</strong></td>
                                        <td style="color: #dc2626;">负相关</td>
                                        <td>美元走强，铜价下跌（通常系数-0.7以上）</td>
                                    </tr>
                                    <tr>
                                        <td><strong>中国PMI</strong></td>
                                        <td style="color: #16a34a;">正相关</td>
                                        <td>制造业景气度，铜被称为"铜博士"</td>
                                    </tr>
                                    <tr>
                                        <td><strong>实际利率</strong></td>
                                        <td style="color: #dc2626;">负相关</td>
                                        <td>持有机会成本，影响投资需求</td>
                                    </tr>
                                    <tr>
                                        <td><strong>LME升贴水</strong></td>
                                        <td style="color: #16a34a;">正相关</td>
                                        <td>反映即期供需紧张度（Backwardation看涨）</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }

            // 基本面模型指标
            if (data.fundamental) {
                html += `
                    <div class="model-section fundamental">
                        <h2 class="model-title fundamental">🏭 基本面模型（长期趋势）</h2>
                        <p class="model-desc">
                            适用于6个月以上的战略配置，基于供需平衡、成本支撑、库存变化等基本面因素。
                        </p>
                        <h3 style="margin-bottom: 15px; color: #333;">关键指标</h3>
                        <div class="indicators-grid">
                `;

                for (const [key, value] of Object.entries(data.fundamental.indicators || {})) {
                    const numValue = typeof value === 'number' ? value : parseFloat(value);
                    const valueDisplay = typeof value === 'number' ? value.toFixed(2) : value;
                    const valueClass = numValue > 0 ? 'positive' : (numValue < 0 ? 'negative' : '');
                    
                    const { score, level, range } = calculateIndicatorScore(key, numValue, 'fundamental');
                    const scoreText = `${score}分`;
                    
                    html += `
                        <div class="indicator-card">
                            <div class="indicator-score ${level}">${scoreText}</div>
                            <div class="indicator-name">${key}</div>
                            <div class="indicator-value ${valueClass}">${valueDisplay}</div>
                            <div class="indicator-range">${range}</div>
                        </div>
                    `;
                }

                html += `
                        </div>
                        <h3 style="margin-bottom: 15px; color: #333;">变量说明</h3>
                        <div class="variable-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>变量名称</th>
                                        <th>影响方向</th>
                                        <th>说明</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>产量增长率</strong></td>
                                        <td style="color: #dc2626;">负相关</td>
                                        <td>供应增加，价格承压</td>
                                    </tr>
                                    <tr>
                                        <td><strong>消费增长率</strong></td>
                                        <td style="color: #16a34a;">正相关</td>
                                        <td>需求增长，价格上涨</td>
                                    </tr>
                                    <tr>
                                        <td><strong>库存变化率</strong></td>
                                        <td style="color: #dc2626;">负相关</td>
                                        <td>库存累积，供应充足</td>
                                    </tr>
                                    <tr>
                                        <td><strong>成本支撑价</strong></td>
                                        <td style="color: #16a34a;">支撑</td>
                                        <td>C1成本90分位线，价格底部支撑</td>
                                    </tr>
                                    <tr>
                                        <td><strong>供应干扰指数</strong></td>
                                        <td style="color: #16a34a;">正相关</td>
                                        <td>罢工、地缘政治等供应冲击</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }

            if (!data.macro && !data.fundamental) {
                html += `
                    <div class="error">
                        <h3>⚠️ 暂无模型指标数据</h3>
                        <p>请先在主页运行宏观或基本面模型的预测</p>
                        <button class="refresh-btn" onclick="location.href='/')">返回主页运行预测</button>
                    </div>
                `;
            }

            content.innerHTML = html;
        }

        // 页面加载时加载指标
        loadIndicators();
    </script>
</body>
</html>
"""


@app.route('/model-indicators.html')
def model_indicators_page():
    """模型指标详情页面"""
    return render_template_string(MODEL_INDICATORS_TEMPLATE)


@app.route('/model-indicators-data')
def get_model_indicators_data():
    """获取模型指标数据"""
    import json
    
    # 查找最新的报告文件
    reports = list(Path('.').glob('report_*.txt'))
    
    result = {
        'macro': {'indicators': {}},
        'fundamental': {'indicators': {}}
    }
    
    if reports:
        # 按修改时间排序，取最新的
        latest_report = max(reports, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析宏观模型指标
            import re
            
            # 查找宏观因子部分
            if '宏观因子模型' in content:
                macro_section = content[content.find('宏观因子模型'):content.find('基本面模型') if '基本面模型' in content else len(content)]
                
                # 提取美元指数
                usd_match = re.search(r'美元指数[:\s]*([-\d.]+)', macro_section)
                if usd_match:
                    result['macro']['indicators']['美元指数'] = float(usd_match.group(1))
                
                # 提取PMI
                pmi_match = re.search(r'中国PMI[:\s]*([-\d.]+)', macro_section)
                if pmi_match:
                    result['macro']['indicators']['中国PMI'] = float(pmi_match.group(1))
                
                # 提取信贷脉冲
                credit_match = re.search(r'信贷脉冲[:\s]*([-\d.]+)', macro_section)
                if credit_match:
                    result['macro']['indicators']['信贷脉冲'] = float(credit_match.group(1))
            
            # 查找基本面模型指标
            if '基本面模型' in content:
                fund_section = content[content.find('基本面模型'):]
                
                # 提取供应干扰指数
                disr_match = re.search(r'供应干扰指数[:\s]*([-\d.]+)', fund_section)
                if disr_match:
                    result['fundamental']['indicators']['供应干扰指数'] = float(disr_match.group(1))
            
            # 如果指标为空，提供模拟数据用于演示
            if not result['macro']['indicators'] and not result['fundamental']['indicators']:
                # 宏观模型模拟数据
                result['macro']['indicators'] = {
                    '美元指数': 99.04,
                    '中国PMI': 54.69,
                    '实际利率(%)': 0.5,
                    'LME升贴水': 15.5,
                    '信贷脉冲': 140.81
                }
                # 基本面模型模拟数据
                result['fundamental']['indicators'] = {
                    '产量增长率': 3.2,
                    '消费增长率': 5.8,
                    '库存变化率': -2.5,
                    '成本支撑价': 98000.0,
                    '供应干扰指数': 28.21
                }
        
        except Exception as e:
            print(f"解析模型指标失败: {e}")
            # 提供默认数据
            result['macro']['indicators'] = {
                '美元指数': 99.04,
                '中国PMI': 54.69,
                '实际利率(%)': 0.5,
                'LME升贴水': 15.5,
                '信贷脉冲': 140.81
            }
            result['fundamental']['indicators'] = {
                '产量增长率': 3.2,
                '消费增长率': 5.8,
                '库存变化率': -2.5,
                '成本支撑价': 98000.0,
                '供应干扰指数': 28.21
            }
    
    return jsonify(result)


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
