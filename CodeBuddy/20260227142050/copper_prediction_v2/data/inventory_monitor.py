"""
全球铜库存监控模块
支持 LME / SHFE / COMEX 三地库存数据采集与分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import akshare as ak

class CopperInventoryMonitor:
    """铜库存监控器"""
    
    # 历史参考区间 (万吨)
    HISTORICAL_RANGES = {
        'low': (10, 40),      # 低位区间
        'mid': (40, 70),      # 中位区间
        'high': (70, 100),    # 高位区间
        'extreme': 100        # 极高
    }
    
    # 20年历史统计参考
    HIST_STATS = {
        'min': 10,      # 最低约10万吨
        'avg': 65,      # 平均约65万吨
        'max': 120      # 最高约120万吨
    }
    
    def __init__(self):
        self.data = {}
        self.last_update = None
        
    def fetch_lme_inventory(self) -> pd.DataFrame:
        """获取LME库存数据"""
        try:
            df = ak.macro_euro_lme_stock()
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期')
            
            # 提取铜库存数据
            copper_df = pd.DataFrame({
                'date': df['日期'],
                'inventory_tons': df['铜-库存'],
                'registered': df['铜-注册仓单'],
                'cancelled': df['铜-注销仓单'],
                'exchange': 'LME'
            })
            
            # 计算注销仓单比例
            copper_df['cancelled_pct'] = (
                copper_df['cancelled'] / copper_df['inventory_tons'] * 100
            ).round(2)
            
            return copper_df
            
        except Exception as e:
            print(f"❌ LME数据获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_shfe_inventory(self) -> pd.DataFrame:
        """获取SHFE库存数据（通过99期货）"""
        try:
            df = ak.futures_inventory_99()
            df['date'] = pd.to_datetime(df['日期'])
            df = df.sort_values('date')
            
            copper_df = pd.DataFrame({
                'date': df['date'],
                'inventory_tons': df['库存'],
                'close_price': df['收盘价'],
                'exchange': 'SHFE'
            })
            
            return copper_df
            
        except Exception as e:
            print(f"❌ SHFE数据获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_comex_inventory(self, manual_value: float = 80000) -> pd.DataFrame:
        """
        获取COMEX库存数据
        注意: AKShare暂不支持，需手动输入或爬虫获取
        """
        # 返回最近日期的估计值
        today = datetime.now()
        return pd.DataFrame({
            'date': [today],
            'inventory_tons': [manual_value],
            'exchange': ['COMEX'],
            'note': ['manual_estimate']
        })
    
    def update_all(self, comex_manual: float = 80000) -> Dict:
        """更新所有库存数据"""
        print("📦 正在更新全球铜库存数据...")
        
        # 获取三地数据
        lme_df = self.fetch_lme_inventory()
        shfe_df = self.fetch_shfe_inventory()
        comex_df = self.fetch_comex_inventory(comex_manual)
        
        # 存储数据
        self.data = {
            'LME': lme_df,
            'SHFE': shfe_df,
            'COMEX': comex_df
        }
        self.last_update = datetime.now()
        
        return self.analyze_inventory()
    
    def analyze_inventory(self) -> Dict:
        """分析库存水平"""
        if not self.data:
            return {}
        
        # 获取最新库存
        lme_latest = self.data['LME'].tail(1) if not self.data['LME'].empty else None
        shfe_latest = self.data['SHFE'].tail(1) if not self.data['SHFE'].empty else None
        comex_latest = self.data['COMEX'].tail(1) if not self.data['COMEX'].empty else None
        
        # 计算总量（转换为万吨）
        lme_vol = lme_latest['inventory_tons'].iloc[0] / 10000 if lme_latest is not None else 0
        shfe_vol = shfe_latest['inventory_tons'].iloc[0] / 10000 if shfe_latest is not None else 0
        comex_vol = comex_latest['inventory_tons'].iloc[0] / 10000 if comex_latest is not None else 0
        
        total = lme_vol + shfe_vol + comex_vol
        
        # 计算历史百分位
        stats = self.HIST_STATS
        percentile = (total - stats['min']) / (stats['max'] - stats['min']) * 100
        percentile = max(0, min(100, percentile))
        
        # 判断库存水平
        if total < self.HISTORICAL_RANGES['low'][1]:
            level = 'low'
            level_desc = '低位区间 (强烈看涨)'
            signal = 'bullish'
        elif total < self.HISTORICAL_RANGES['mid'][1]:
            level = 'mid_low'
            level_desc = '中低位区间 (偏多)'
            signal = 'slightly_bullish'
        elif total < self.HISTORICAL_RANGES['high'][1]:
            level = 'mid_high'
            level_desc = '中高位区间 (偏空)'
            signal = 'slightly_bearish'
        elif total < self.HISTORICAL_RANGES['extreme']:
            level = 'high'
            level_desc = '高位区间 (看跌)'
            signal = 'bearish'
        else:
            level = 'extreme'
            level_desc = '极高区间 (强烈看跌)'
            signal = 'very_bearish'
        
        # 分析趋势（基于LME近5日vs30日）
        trend_signal = 'neutral'
        trend_desc = '趋势不明'
        
        if lme_latest is not None and len(self.data['LME']) >= 30:
            lme_5d = self.data['LME'].tail(5)['inventory_tons'].mean()
            lme_30d = self.data['LME'].tail(30)['inventory_tons'].mean()
            trend_change = (lme_5d / lme_30d - 1) * 100
            
            if trend_change > 10:
                trend_signal = 'rapid_build'
                trend_desc = f'⚠️ 快速累库 (+{trend_change:.1f}%)'
            elif trend_change > 0:
                trend_signal = 'slow_build'
                trend_desc = f'↗️ 缓慢累库 (+{trend_change:.1f}%)'
            elif trend_change > -10:
                trend_signal = 'slow_draw'
                trend_desc = f'↘️ 缓慢去库 ({trend_change:.1f}%)'
            else:
                trend_signal = 'rapid_draw'
                trend_desc = f'✅ 快速去库 ({trend_change:.1f}%)'
        
        # 构建结果
        result = {
            'update_time': self.last_update.strftime('%Y-%m-%d %H:%M:%S'),
            'inventory': {
                'LME': {'tons': lme_vol * 10000, 'wan_tons': round(lme_vol, 1), 
                        'pct': round(lme_vol/total*100, 1) if total > 0 else 0},
                'SHFE': {'tons': shfe_vol * 10000, 'wan_tons': round(shfe_vol, 1),
                         'pct': round(shfe_vol/total*100, 1) if total > 0 else 0},
                'COMEX': {'tons': comex_vol * 10000, 'wan_tons': round(comex_vol, 1),
                          'pct': round(comex_vol/total*100, 1) if total > 0 else 0},
                'total': {'wan_tons': round(total, 1)}
            },
            'analysis': {
                'percentile': round(percentile, 0),
                'level': level,
                'level_desc': level_desc,
                'signal': signal,
                'trend_signal': trend_signal,
                'trend_desc': trend_desc,
                'reference': {
                    'hist_low': self.HIST_STATS['min'],
                    'hist_avg': self.HIST_STATS['avg'],
                    'hist_high': self.HIST_STATS['max']
                }
            },
            'details': {
                'lme_cancelled_pct': lme_latest['cancelled_pct'].iloc[0] if lme_latest is not None else None,
                'shfe_price': shfe_latest['close_price'].iloc[0] if shfe_latest is not None else None
            }
        }
        
        return result
    
    def generate_report(self) -> str:
        """生成库存分析报告"""
        data = self.analyze_inventory()
        if not data:
            return "暂无数据"
        
        inv = data['inventory']
        ana = data['analysis']
        
        report = f"""
{'='*70}
📦 全球铜库存监测报告
{'='*70}
更新时间: {data['update_time']}

📊 库存分布:
  ┌─────────┬──────────┬────────┐
  │ 交易所  │ 库存(万吨)│ 占比   │
  ├─────────┼──────────┼────────┤
  │ LME     │ {inv['LME']['wan_tons']:>7.1f}  │ {inv['LME']['pct']:>5.1f}% │
  │ SHFE    │ {inv['SHFE']['wan_tons']:>7.1f}  │ {inv['SHFE']['pct']:>5.1f}% │
  │ COMEX   │ {inv['COMEX']['wan_tons']:>7.1f}  │ {inv['COMEX']['pct']:>5.1f}% │
  ├─────────┼──────────┼────────┤
  │ 总计    │ {inv['total']['wan_tons']:>7.1f}  │ 100.0% │
  └─────────┴──────────┴────────┘

📈 库存水平分析:
  当前库存: {inv['total']['wan_tons']:.1f} 万吨
  历史低位: {ana['reference']['hist_low']} 万吨
  历史平均: {ana['reference']['hist_avg']} 万吨
  历史高位: {ana['reference']['hist_high']} 万吨
  
  相对位置: {ana['percentile']:.0f}% 分位
  库存水平: {ana['level_desc']}
  
📉 趋势信号: {ana['trend_desc']}

💡 投资建议:
"""
        
        if ana['signal'] in ['bullish', 'slightly_bullish']:
            report += """  • 🎯 库存偏低，供给紧张支撑价格
  • 📈 建议逢低做多，关注补库需求
  • 👀 监测LME注销仓单变化
"""
        elif ana['signal'] in ['bearish', 'very_bearish']:
            report += """  • 🎯 库存偏高，供给宽松压制价格
  • 📉 建议逢高做空，关注库存去化
  • 👀 监测全球需求变化
"""
        else:
            report += """  • 🎯 库存中性，价格受宏观因素主导
  • 📊 建议区间操作，关注边际变化
  • 👀 重点关注美元指数和PMI数据
"""
        
        report += f"""
📌 关键指标:
  • LME注销仓单比例: {data['details']['lme_cancelled_pct']:.1f}%
  • SHFE期货收盘价: {data['details']['shfe_price']}

⚠️  免责声明: 本报告仅供参考，不构成投资建议
{'='*70}
"""
        return report
    
    def save_to_csv(self, filepath: str = 'copper_inventory.csv'):
        """保存数据到CSV"""
        all_data = []
        for exchange, df in self.data.items():
            if not df.empty:
                df_copy = df.copy()
                df_copy['inventory_wan_tons'] = df_copy['inventory_tons'] / 10000
                all_data.append(df_copy)
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            combined.to_csv(filepath, index=False)
            print(f"✅ 数据已保存到: {filepath}")
        else:
            print("❌ 无数据可保存")


# 使用示例
if __name__ == '__main__':
    # 初始化监控器
    monitor = CopperInventoryMonitor()
    
    # 更新数据（COMEX手动输入当前值，单位：吨）
    result = monitor.update_all(comex_manual=80000)
    
    # 打印报告
    print(monitor.generate_report())
    
    # 保存数据
    monitor.save_to_csv('data/copper_inventory_history.csv')
