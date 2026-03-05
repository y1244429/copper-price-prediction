"""
运行增强预测
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.enhanced_data_sources import EnhancedDataIntegration
from data.prediction_db import PredictionDatabase
from data.real_data import RealDataManager
import numpy as np
from datetime import datetime

class SimpleEnhancedPredictor:
    """简化的增强预测器"""
    
    def __init__(self):
        self.enhanced_data = EnhancedDataIntegration()
        self.db = PredictionDatabase()
        self.data_mgr = RealDataManager()
    
    def predict(self, horizon: int = 5) -> dict:
        """执行增强预测"""
        print("\n" + "="*70)
        print("增强预测系统")
        print("="*70)
        
        # 1. 获取当前价格
        current_data = self.data_mgr.get_full_data(days=60)
        current_price = current_data.iloc[-1]['close']
        print(f"\n当前价格: ¥{current_price:,.2f}")
        
        # 2. 获取增强数据
        print("\n获取增强数据...")
        enhanced_data = self.enhanced_data.get_comprehensive_data()
        
        # 3. 打印增强数据摘要
        self.enhanced_data.print_summary(enhanced_data)
        
        # 4. 判断市场状态
        risk_signals = enhanced_data['risk_signals']
        high_risk_count = sum(1 for s in risk_signals if s.get('level') == 'high')
        
        if high_risk_count >= 2 or len(risk_signals) >= 4:
            market_state = 'crisis'
        elif enhanced_data['news_sentiment'].get('overall_sentiment') == 'positive':
            market_state = 'bull'
        elif enhanced_data['news_sentiment'].get('overall_sentiment') == 'negative':
            market_state = 'bear'
        else:
            market_state = 'normal'
        
        print(f"\n市场状态: {market_state}")
        
        # 5. 基于增强数据生成预测
        # 分析利多利空因素
        bullish_factors = 0
        bearish_factors = 0
        
        macro = enhanced_data['macro']
        if macro['pmi']['value'] > 50:
            bullish_factors += 1
        else:
            bearish_factors += 1
        
        if macro['dollar_index']['value'] < 100:
            bullish_factors += 1
        else:
            bearish_factors += 1
        
        if macro['vix']['value'] < 20:
            bullish_factors += 1
        else:
            bearish_factors += 1
        
        news = enhanced_data['news_sentiment']
        if news.get('overall_sentiment') == 'positive':
            bullish_factors += 1
        elif news.get('overall_sentiment') == 'negative':
            bearish_factors += 1
        
        # 风险信号增加利空因素
        bearish_factors += len(risk_signals)
        
        print(f"\n利多因素: {bullish_factors} 个")
        print(f"利空因素: {bearish_factors} 个")
        
        # 计算预测收益率
        net_factors = bullish_factors - bearish_factors
        
        # 基础收益率（基于利多利空因素）
        base_return = net_factors * 0.5  # 每个因素影响0.5%
        
        # 根据市场状态调整
        if market_state == 'crisis':
            base_return *= 0.5  # 危机时减半
        elif market_state == 'bull':
            base_return *= 1.2  # 牛市时放大
        elif market_state == 'bear':
            base_return *= 0.8  # 熊市时缩小
        
        # 风险调整
        risk_adjustment = 1.0
        for signal in risk_signals:
            if signal['level'] == 'high':
                risk_adjustment *= 0.90
            else:
                risk_adjustment *= 0.97
        
        adjusted_return = base_return * risk_adjustment
        
        # 计算预测价格
        predicted_price = current_price * (1 + adjusted_return / 100)
        
        # 计算预测区间
        confidence = 'low' if high_risk_count > 0 else ('medium' if len(risk_signals) > 1 else 'high')
        
        if confidence == 'high':
            interval_width = 0.05
        elif confidence == 'medium':
            interval_width = 0.08
        else:
            interval_width = 0.12
        
        lower_bound = predicted_price * (1 - interval_width)
        upper_bound = predicted_price * (1 + interval_width)
        
        # 6. 生成投资建议
        if adjusted_return > 1.5:
            direction = 'strong_buy'
            advice = '强烈建议做多'
        elif adjusted_return > 0:
            direction = 'buy'
            advice = '建议适度做多'
        elif adjusted_return > -1.5:
            direction = 'hold'
            advice = '建议观望'
        else:
            direction = 'sell'
            advice = '建议谨慎观望或适度做空'
        
        if confidence == 'low':
            advice += '，但需谨慎控制仓位'
        elif confidence == 'medium':
            advice += '，建议设置止损'
        
        # 7. 整合结果
        result = {
            'prediction_date': datetime.now(),
            'current_price': current_price,
            'horizon_days': horizon,
            'market_state': market_state,
            'predicted_price': predicted_price,
            'predicted_return_pct': adjusted_return,
            'prediction_interval': {
                'lower': lower_bound,
                'upper': upper_bound
            },
            'confidence_level': confidence,
            'bullish_factors': bullish_factors,
            'bearish_factors': bearish_factors,
            'risk_signals': risk_signals,
            'risk_adjustment': risk_adjustment,
            'recommendation': {
                'direction': direction,
                'advice': advice
            },
            'enhanced_data': enhanced_data
        }
        
        # 8. 打印预测结果
        print("\n" + "="*70)
        print("预测结果")
        print("="*70)
        print(f"\n预测价格: ¥{predicted_price:,.2f} ({adjusted_return:+.2f}%)")
        print(f"预测区间: ¥{lower_bound:,.2f} ~ ¥{upper_bound:,.2f}")
        print(f"置信度: {confidence}")
        
        print(f"\n【投资建议】")
        direction_map = {
            'strong_buy': '🟢 强烈做多',
            'buy': '🟢 做多',
            'hold': '🟡 观望',
            'sell': '🔴 做空'
        }
        print(f"操作方向: {direction_map.get(direction, direction)}")
        print(f"建议: {advice}")
        
        if risk_signals:
            print(f"\n⚠️  检测到 {len(risk_signals)} 个风险信号:")
            for i, signal in enumerate(risk_signals[:3], 1):
                level_icon = '🔴' if signal['level'] == 'high' else '🟡'
                print(f"  {i}. {level_icon} {signal['message']}")
        
        print("\n" + "="*70)
        
        return result

if __name__ == '__main__':
    predictor = SimpleEnhancedPredictor()
    result = predictor.predict(horizon=5)
    
    # 保存结果到JSON
    import json
    output_file = f"outputs/enhanced_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("outputs", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n✅ 预测结果已保存到: {output_file}")
