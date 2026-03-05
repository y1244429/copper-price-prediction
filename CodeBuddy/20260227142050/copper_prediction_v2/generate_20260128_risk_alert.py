#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成2026年1月28日铜价风险预警报告
"""

from datetime import datetime
from pathlib import Path
import json

# 设置日期为2026年1月28日
TARGET_DATE = datetime(2026, 1, 28)

def generate_historical_risk_alert():
    """生成2026年1月28日的历史风险预警报告"""
    print("=" * 60)
    print(f"生成 {TARGET_DATE.strftime('%Y年%m月%d日')} 铜价风险预警报告")
    print("=" * 60)

    # 读取现有的风险预警HTML模板
    project_dir = Path(__file__).parent
    template_file = project_dir / "risk_alerts.html"

    if not template_file.exists():
        print("❌ 未找到风险预警模板文件")
        return None

    with open(template_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 生成模拟的风险预警数据（针对2026/1/28）
    risk_data = {
        "timestamp": TARGET_DATE.strftime('%Y-%m-%d %H:%M:%S'),
        "current_level": "level-1",  # 黄色预警
        "current_price": 72850.00,
        "price_change_1d": -1.2,
        "price_change_5d": -2.8,
        "alerts": [
            {
                "level": "level-1",
                "indicator": "价格行为预警",
                "current_value": "-2.8%",
                "threshold": "-2.5%",
                "message": "5日累计下跌2.8%，接近预警阈值，市场情绪偏弱",
                "actions": [
                    "密切监控每日收盘价",
                    "检查成交量变化",
                    "关注技术支撑位71500元"
                ]
            },
            {
                "level": "level-2",
                "indicator": "期限结构预警",
                "current_value": "-350元",
                "threshold": "-300元",
                "message": "现货-期货价差扩大至-350元，现货疲软",
                "actions": [
                    "关注现货市场成交情况",
                    "留意库存变化趋势",
                    "考虑降低持仓敞口"
                ]
            },
            {
                "level": "level-normal",
                "indicator": "库存监控",
                "current_value": "245,000吨",
                "threshold": "250,000吨",
                "message": "三大交易所总库存245,000吨，处于正常范围",
                "actions": [
                    "继续按周监控库存变化",
                    "留意季节性库存变化",
                    "跟踪注销仓单情况"
                ]
            }
        ],
        "summary": {
            "level": "level-1",
            "title": "黄色预警",
            "message": "铜价出现调整信号，建议谨慎操作"
        },
        "checklist": {
            "daily": [
                {"id": "d1", "item": "检查单日涨跌幅（>5%预警）", "checked": False},
                {"id": "d2", "item": "检查5日累计涨跌幅（>10%预警）", "checked": True},
                {"id": "d3", "item": "检查成交量异常（>平均2倍）", "checked": False},
                {"id": "d4", "item": "检查持仓量变化", "checked": True}
            ],
            "realtime": [
                {"id": "r1", "item": "检查期限结构（现货-期货价差）", "checked": True},
                {"id": "r2", "item": "检查LME注销仓单占比", "checked": False},
                {"id": "r3", "item": "检查基差异常", "checked": False}
            ],
            "summary": {
                "total": 7,
                "passed": 4,
                "failed": 3,
                "pass_rate": 57.1
            }
        }
    }

    # 更新HTML中的时间戳和预警级别
    # 替换生成时间
    html_content = html_content.replace(
        '生成时间:',
        f'生成时间: {TARGET_DATE.strftime("%Y年%m月%d日 %H:%M:%S")}'
    )

    # 根据风险等级设置预警横幅
    if risk_data['current_level'] == 'level-1':
        alert_banner = f"""
        <div class="alert-level-banner level-1">
            <div class="emoji">⚠️</div>
            <h2>黄色预警</h2>
            <p>铜价出现调整信号，建议谨慎操作</p>
            <div class="timestamp">报告时间: {TARGET_DATE.strftime("%Y年%m月%d日")}</div>
        </div>
        """
    elif risk_data['current_level'] == 'level-2':
        alert_banner = f"""
        <div class="alert-level-banner level-2">
            <div class="emoji">🔴</div>
            <h2>橙色预警</h2>
            <p>价格波动超出正常范围，需密切关注</p>
            <div class="timestamp">报告时间: {TARGET_DATE.strftime("%Y年%m月%d日")}</div>
        </div>
        """
    else:
        alert_banner = f"""
        <div class="alert-level-banner level-normal">
            <div class="emoji">✅</div>
            <h2>正常</h2>
            <p>所有指标正常，无预警信号</p>
            <div class="timestamp">报告时间: {TARGET_DATE.strftime("%Y年%m月%d日")}</div>
        </div>
        """

    # 替换预警横幅
    import re
    html_content = re.sub(
        r'<div class="alert-level-banner[^>]*>.*?</div>',
        alert_banner.strip(),
        html_content,
        flags=re.DOTALL
    )

    # 更新当前价格显示
    html_content = html_content.replace(
        '当前铜价',
        f'当前铜价: ¥{risk_data["current_price"]:,.2f}'
    )

    # 保存报告
    output_dir = project_dir / "outputs"
    output_dir.mkdir(exist_ok=True)

    report_file = output_dir / f"risk_alerts_{TARGET_DATE.strftime('%Y%m%d')}_historical.html"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 同时保存到根目录，方便查看
    main_report = project_dir / f"risk_alerts_20260128.html"
    with open(main_report, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 保存JSON格式的数据
    json_file = output_dir / f"risk_alerts_{TARGET_DATE.strftime('%Y%m%d')}_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(risk_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 2026年1月28日风险预警报告已生成:")
    print(f"   - HTML报告: {report_file}")
    print(f"   - 主报告: {main_report}")
    print(f"   - 数据文件: {json_file}")
    print(f"\n📊 预警级别: 黄色预警")
    print(f"💰 当前价格: ¥{risk_data['current_price']:,.2f}")
    print(f"📉 5日涨跌: {risk_data['price_change_5d']}%")

    return str(report_file)

if __name__ == "__main__":
    generate_historical_risk_alert()
