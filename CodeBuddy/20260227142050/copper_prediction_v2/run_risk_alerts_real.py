#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用真实数据运行铜价风险预警系统
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

def get_real_copper_data(days=30):
    """获取真实铜价数据"""
    print("=" * 60)
    print("获取真实铜价数据")
    print("=" * 60)
    
    try:
        from data.data_sources import AKShareDataSource
        
        # 创建数据源
        data_source = AKShareDataSource()
        
        if not data_source.available:
            print("⚠️  AKShare不可用，使用模拟数据")
            return None
        
        # 获取过去30天的数据
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        print(f"\n正在获取数据 ({start_date} 至 {end_date})...")
        
        # 获取铜价数据
        df = data_source.fetch_copper_price(start_date=start_date, end_date=end_date)
        
        if df is not None and not df.empty:
            print(f"✅ 成功获取 {len(df)} 条真实数据")
            print(f"   日期范围: {df.index[0].date()} 至 {df.index[-1].date()}")
            print(f"   最新价格: ¥{df['close'].iloc[-1]:,.2f}")
            print(f"   最低价格: ¥{df['low'].min():,.2f}")
            print(f"   最高价格: ¥{df['high'].max():,.2f}")
            
            return df
        else:
            print("❌ 未获取到数据")
            return None
            
    except Exception as e:
        print(f"❌ 获取真实数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_risk_with_real_data(df):
    """使用真实数据进行风险分析"""
    print("\n" + "=" * 60)
    print("风险预警分析")
    print("=" * 60)
    
    if df is None or df.empty:
        print("❌ 没有数据可供分析")
        return None
    
    try:
        from models.risk_alert_system import CopperRiskMonitor, AlertThresholds
        
        # 创建监控器
        monitor = CopperRiskMonitor(thresholds=AlertThresholds())
        
        # 运行完整监控
        print("\n正在运行风险监控...")
        result = monitor.run_full_monitoring(price_data=df, inventory_data={})
        
        # 显示结果
        print(f"\n✅ 风险分析完成")
        print(f"   当前预警级别: {result.get('current_level', 'unknown')}")
        print(f"   预警数量: {len(result.get('alerts', []))}")
        
        if result.get('alerts'):
            print("\n   预警详情:")
            for i, alert in enumerate(result['alerts'], 1):
                print(f"   {i}. [{alert.get('level', 'unknown')}] {alert.get('indicator', 'N/A')}")
                print(f"      当前值: {alert.get('current_value', 'N/A')}")
                print(f"      阈值: {alert.get('threshold', 'N/A')}")
                print(f"      信息: {alert.get('message', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 风险分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_real_data_report(df, risk_result):
    """生成真实数据风险预警报告"""
    print("\n" + "=" * 60)
    print("生成风险预警报告")
    print("=" * 60)
    
    try:
        # 读取模板
        template_file = PROJECT_DIR / "risk_alerts.html"
        with open(template_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 更新时间戳
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        html_content = html_content.replace('生成时间:', f'生成时间: {current_time}')
        
        # 根据风险等级设置预警横幅
        if risk_result:
            level = risk_result.get('current_level', 'normal')
            current_price = df['close'].iloc[-1] if df is not None else 0
            
            if level == 'level-3':
                alert_banner = f"""
                <div class="alert-level-banner level-3">
                    <div class="emoji">🚨</div>
                    <h2>红色预警</h2>
                    <p>价格出现剧烈波动，立即采取风险控制措施</p>
                    <div class="timestamp">报告时间: {datetime.now().strftime("%Y年%m月%d日")}</div>
                </div>
                """
            elif level == 'level-2':
                alert_banner = f"""
                <div class="alert-level-banner level-2">
                    <div class="emoji">🔴</div>
                    <h2>橙色预警</h2>
                    <p>价格波动超出正常范围，需密切关注</p>
                    <div class="timestamp">报告时间: {datetime.now().strftime("%Y年%m月%d日")}</div>
                </div>
                """
            elif level == 'level-1':
                alert_banner = f"""
                <div class="alert-level-banner level-1">
                    <div class="emoji">⚠️</div>
                    <h2>黄色预警</h2>
                    <p>铜价出现调整信号，建议谨慎操作</p>
                    <div class="timestamp">报告时间: {datetime.now().strftime("%Y年%m月%d日")}</div>
                </div>
                """
            else:
                alert_banner = f"""
                <div class="alert-level-banner level-normal">
                    <div class="emoji">✅</div>
                    <h2>正常</h2>
                    <p>所有指标正常，无预警信号</p>
                    <div class="timestamp">报告时间: {datetime.now().strftime("%Y年%m月%d日")}</div>
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
            
            # 更新价格信息
            if df is not None:
                html_content = html_content.replace(
                    '当前铜价',
                    f'当前铜价: ¥{current_price:,.2f}'
                )
        else:
            print("⚠️  没有风险分析结果，使用默认模板")
        
        # 保存报告
        output_dir = PROJECT_DIR / "outputs"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"risk_alerts_real_{timestamp}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 同时保存到根目录
        main_report = PROJECT_DIR / "risk_alerts_real.html"
        with open(main_report, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ 真实数据风险预警报告已生成:")
        print(f"   - {report_file}")
        print(f"   - {main_report}")
        
        return str(report_file)
        
    except Exception as e:
        print(f"❌ 生成报告失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("铜价风险预警系统 - 真实数据版本")
    print("=" * 60)
    print()
    
    # 1. 获取真实数据
    df = get_real_copper_data(days=30)
    
    if df is None:
        print("\n❌ 无法获取真实数据，程序终止")
        return False
    
    # 2. 风险分析
    risk_result = analyze_risk_with_real_data(df)
    
    # 3. 生成报告
    report_file = generate_real_data_report(df, risk_result)
    
    print("\n" + "=" * 60)
    if report_file:
        print("✅ 风险预警系统运行完成！")
        print(f"\n📊 可以在浏览器中打开以下文件查看报告:")
        print(f"   {report_file}")
    else:
        print("⚠️  风险预警系统运行完成，但报告生成失败")
    print("=" * 60)
    
    return report_file is not None

if __name__ == "__main__":
    main()
