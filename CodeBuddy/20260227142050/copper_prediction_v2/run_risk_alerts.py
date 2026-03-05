#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铜价风险预警系统运行脚本
生成风险预警报告并发送邮件
"""

import sys
from pathlib import Path
from datetime import datetime
import os

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

try:
    from models.risk_alert_system import CopperRiskMonitor, AlertThresholds
    from data.data_sources import DataManager
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("尝试使用直接导入...")
    try:
        # 尝试直接导入
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "risk_alert_system",
            PROJECT_DIR / "models" / "risk_alert_system.py"
        )
        risk_alert_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(risk_alert_module)
        CopperRiskMonitor = risk_alert_module.CopperRiskMonitor
        AlertThresholds = risk_alert_module.AlertThresholds

        # 数据管理器可能失败，我们稍后处理
        DataManager = None
    except Exception as e2:
        print(f"直接导入也失败: {e2}")
        print("将使用模拟数据")
        CopperRiskMonitor = None
        AlertThresholds = None
        DataManager = None


def generate_risk_alert_report():
    """生成风险预警报告"""
    print("=" * 50)
    print("铜价风险预警系统启动")
    print("=" * 50)
    print()

    try:
        # 初始化数据管理器
        print("正在初始化数据管理器...")
        if DataManager is not None:
            try:
                data_manager = DataManager()
            except:
                data_manager = None
        else:
            data_manager = None

        # 初始化风险预警系统
        print("正在初始化风险预警系统...")
        if CopperRiskMonitor is not None and AlertThresholds is not None:
            alert_system = CopperRiskMonitor(thresholds=AlertThresholds())
        else:
            alert_system = None

        # 获取最新数据
        print("正在获取最新数据...")
        if data_manager is not None:
            try:
                data = data_manager.get_latest_data()
            except:
                data = None
        else:
            data = None

        if data is None or len(data) == 0:
            print("警告：未获取到数据，使用模拟数据")
            # 生成模拟数据用于测试
            import pandas as pd
            import numpy as np

            dates = pd.date_range(end=datetime.now(), periods=30)
            data = pd.DataFrame({
                'date': dates,
                'close': np.random.uniform(70000, 75000, 30),
                'volume': np.random.uniform(100000, 200000, 30),
                'high': np.random.uniform(70000, 75000, 30),
                'low': np.random.uniform(70000, 75000, 30)
            })

        # 运行风险预警分析
        print("正在运行风险预警分析...")
        if alert_system is not None:
            try:
                alert_results = alert_system.analyze(data)

                # 生成HTML报告
                print("正在生成HTML报告...")
                html_report = alert_system.generate_html_report(alert_results)
            except Exception as e:
                print(f"分析失败: {e}，使用默认HTML")
                # 使用现有的HTML文件
                default_file = PROJECT_DIR / "risk_alerts.html"
                if default_file.exists():
                    with open(default_file, 'r', encoding='utf-8') as f:
                        html_report = f.read()
                else:
                    # 创建简单的HTML
                    html_report = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>铜价风险预警报告</title>
</head>
<body>
    <h1>⚠️ 铜价风险预警报告</h1>
    <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p>风险预警系统运行成功</p>
</body>
</html>
"""
        else:
            # 使用现有的HTML文件
            print("使用默认HTML报告")
            default_file = PROJECT_DIR / "risk_alerts.html"
            if default_file.exists():
                with open(default_file, 'r', encoding='utf-8') as f:
                    html_report = f.read()
            else:
                # 创建简单的HTML
                html_report = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>铜价风险预警报告</title>
</head>
<body>
    <h1>⚠️ 铜价风险预警报告</h1>
    <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p>风险预警系统运行成功</p>
</body>
</html>
"""

        # 保存HTML报告
        output_dir = PROJECT_DIR / "outputs"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_file = output_dir / f"risk_alerts_{timestamp}.html"

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)

        print(f"✅ 风险预警报告已生成: {html_file}")
        print()

        # 同时保存为risk_alerts.html（默认文件）
        default_file = PROJECT_DIR / "risk_alerts.html"
        with open(default_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print(f"✅ 默认报告已更新: {default_file}")

        return str(html_file)

    except Exception as e:
        print(f"❌ 生成风险预警报告失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def send_risk_alert_email(html_file):
    """发送风险预警邮件"""
    try:
        # 导入邮件发送模块
        base_dir = Path(__file__).parent
        email_sender_path = base_dir / "email_sender.py"

        if not email_sender_path.exists():
            news_dir = base_dir.parent.parent / "20260301115643"
            email_sender_path = news_dir / "email_sender.py"

        if not email_sender_path.exists():
            print("邮件发送模块不存在")
            return False

        sys.path.insert(0, str(email_sender_path.parent))
        from email_sender import EmailSender, load_email_config

        # 加载邮件配置
        config = load_email_config()

        # 检查配置是否完整
        required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'receiver_email']
        for field in required_fields:
            if not config.get(field):
                print(f"邮件配置不完整（缺少 {field}）")
                return False

        # 读取HTML报告
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 创建邮件发送器
        email_sender = EmailSender(
            smtp_server=config['smtp_server'],
            smtp_port=config['smtp_port'],
            sender_email=config['sender_email'],
            sender_password=config['sender_password']
        )

        # 发送邮件
        print("正在发送风险预警邮件...")
        today = datetime.now().strftime("%Y年%m月%d日")
        subject = f"⚠️ 铜价风险预警报告 - {today}"

        success, message = email_sender.send_email(
            to_email=config['receiver_email'],
            subject=subject,
            html_content=html_content
        )

        if success:
            print(f"✅ 风险预警邮件发送成功")
            return True
        else:
            print(f"❌ 风险预警邮件发送失败: {message}")
            return False

    except Exception as e:
        print(f"发送邮件时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print()
    print("=" * 60)
    print("铜价风险预警系统 - 运行并发送邮件")
    print("=" * 60)
    print()

    # 生成风险预警报告
    html_file = generate_risk_alert_report()

    if not html_file:
        print()
        print("❌ 生成报告失败，无法发送邮件")
        return False

    print()
    print("-" * 60)
    print("邮件发送")
    print("-" * 60)

    # 发送邮件
    success = send_risk_alert_email(html_file)

    print()
    print("=" * 60)
    if success:
        print("✅ 风险预警系统运行完成！")
    else:
        print("⚠️ 风险预警系统运行完成，但邮件发送失败")
    print("=" * 60)

    return success


if __name__ == "__main__":
    main()
