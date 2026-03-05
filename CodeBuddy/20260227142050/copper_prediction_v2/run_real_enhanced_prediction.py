#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强数据预测 - 真实数据版本
使用 real_enhanced_data.py 的真实数据源
"""

import sys
import os
sys.path.append('/Users/ydy/CodeBuddy/20260227142050/copper_prediction_v2')

from data.real_enhanced_data import RealEnhancedDataManager
from data.real_data import RealDataManager
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealEnhancedPrediction:
    """基于真实数据的增强预测系统"""
    
    def __init__(self):
        logger.info("初始化真实增强数据预测系统...")
        self.enhanced_data_mgr = RealEnhancedDataManager()
        self.price_data_mgr = RealDataManager()
        logger.info("✓ 初始化完成")
    
    def get_market_state(self, risk_signals, macro_data):
        """判断市场状态"""
        high_risk_count = sum(1 for s in risk_signals if s['level'] == 'high')
        risk_count = len(risk_signals)
        
        # 获取宏观数据
        dollar_index = macro_data.get('dollar_index', {}).get('value', 100)
        vix = macro_data.get('vix', {}).get('value', 20)
        pmi = macro_data.get('pmi', {}).get('value', 50)
        
        # 判断逻辑
        if high_risk_count >= 2 or risk_count >= 4:
            return 'crisis'
        elif high_risk_count >= 1 or risk_count >= 1:
            return 'risky'
        elif vix > 22:
            return 'bear'
        elif dollar_index > 105:
            return 'bear'
        elif pmi > 52:
            return 'bull'
        else:
            return 'normal'
    
    def calculate_base_return(self, enhanced_data):
        """计算基础收益率"""
        macro = enhanced_data['macro']
        capital_flow = enhanced_data['capital_flow']
        news = enhanced_data.get('news', {})
        
        bullish_factors = 0
        bearish_factors = 0
        
        # 1. PMI分析
        pmi = macro['pmi']['value']
        if pmi > 52:
            bullish_factors += 1
        elif pmi < 50:
            bearish_factors += 1
        
        # 2. 美元指数分析
        dollar_index = macro['dollar_index']['value']
        if dollar_index < 100:
            bullish_factors += 1
        elif dollar_index > 102:
            bearish_factors += 1
        
        # 3. VIX分析
        vix = macro['vix']['value']
        if vix < 20:
            bullish_factors += 1
        elif vix > 25:
            bearish_factors += 1
        
        # 4. 利率分析
        interest_rate = macro['interest_rate']['federal_funds_rate']
        if interest_rate < 4.5:
            bullish_factors += 1
        elif interest_rate > 5.0:
            bearish_factors += 1
        
        # 5. 资金流向分析
        cftc = capital_flow.get('cftc', {})
        if 'speculative' in cftc:
            net_position = cftc['speculative'].get('net', 0)
            if net_position > 50000:
                bullish_factors += 1
            elif net_position < -30000:
                bearish_factors += 1
        
        # 6. 新闻情绪分析
        news_sentiment = enhanced_data.get('news_sentiment', {})
        if 'overall_sentiment' in news_sentiment:
            sentiment = news_sentiment['overall_sentiment']
            if sentiment == 'positive':
                bullish_factors += 1
            elif sentiment == 'negative':
                bearish_factors += 1
        
        # 计算基础收益率
        base_return = (bullish_factors - bearish_factors) * 0.5
        
        logger.info(f"利多因素: {bullish_factors}个, 利空因素: {bearish_factors}个")
        logger.info(f"基础收益率: {base_return:.2f}%")
        
        return base_return, bullish_factors, bearish_factors
    
    def apply_market_adjustment(self, base_return, market_state):
        """市场状态调整"""
        adjusted_return = base_return
        
        if market_state == 'crisis':
            adjusted_return *= 0.5
            logger.info(f"市场状态: 危机 → 收益率调整 ×0.5")
        elif market_state == 'risky':
            adjusted_return *= 0.8
            logger.info(f"市场状态: 风险 → 收益率调整 ×0.8")
        elif market_state == 'bull':
            adjusted_return *= 1.2
            logger.info(f"市场状态: 牛市 → 收益率调整 ×1.2")
        elif market_state == 'bear':
            adjusted_return *= 0.8
            logger.info(f"市场状态: 熊市 → 收益率调整 ×0.8")
        
        return adjusted_return
    
    def apply_risk_adjustment(self, return_value, risk_signals):
        """风险调整"""
        risk_adjustment = 1.0
        
        for signal in risk_signals:
            if signal['level'] == 'high':
                risk_adjustment *= 0.90
            else:
                risk_adjustment *= 0.97
        
        logger.info(f"风险调整因子: {risk_adjustment:.3f}")
        adjusted_return = return_value * risk_adjustment
        
        return adjusted_return, risk_adjustment
    
    def predict(self, horizon=5):
        """
        执行预测
        
        Args:
            horizon: 预测周期(天)
        """
        logger.info("\n" + "="*80)
        logger.info("开始增强数据预测 (真实数据版本)")
        logger.info("="*80)
        
        # 1. 获取当前价格
        logger.info("\n【步骤1】获取当前价格...")
        price_data = self.price_data_mgr.get_full_data(days=5)
        if not price_data.empty:
            current_price = float(price_data['close'].iloc[-1])
            logger.info(f"✓ 当前铜价: ¥{current_price:,.2f}")
        else:
            logger.error("❌ 无法获取铜价数据")
            return None
        
        # 2. 获取增强数据
        logger.info("\n【步骤2】获取真实增强数据...")
        enhanced_data = self.enhanced_data_mgr.get_all_data()
        logger.info("✓ 增强数据获取完成")
        
        # 3. 显示数据来源
        logger.info("\n【数据来源】")
        macro = enhanced_data['macro']
        logger.info(f"  • 美元指数: {macro['dollar_index']['value']} ({macro['dollar_index']['source']})")
        logger.info(f"  • VIX恐慌指数: {macro['vix']['value']} ({macro['vix']['source']})")
        logger.info(f"  • PMI: {macro['pmi']['value']} ({macro['pmi']['source']})")
        logger.info(f"  • 联邦利率: {macro['interest_rate']['federal_funds_rate']}% ({macro['interest_rate']['source']})")
        
        # 4. 获取风险信号
        risk_signals = enhanced_data.get('risk_signals', [])
        logger.info(f"\n【步骤3】风险信号 ({len(risk_signals)}个)")
        for i, signal in enumerate(risk_signals, 1):
            level = '🔴' if signal['level'] == 'high' else '🟡'
            logger.info(f"  {i}. {level} {signal['message']}")
        
        # 5. 计算基础收益率
        logger.info("\n【步骤4】计算基础收益率...")
        base_return, bullish_factors, bearish_factors = self.calculate_base_return(enhanced_data)
        
        # 6. 判断市场状态
        logger.info("\n【步骤5】判断市场状态...")
        market_state = self.get_market_state(risk_signals, macro)
        logger.info(f"✓ 市场状态: {market_state}")
        
        # 7. 市场状态调整
        logger.info("\n【步骤6】市场状态调整...")
        market_adjusted_return = self.apply_market_adjustment(base_return, market_state)
        
        # 8. 风险调整
        logger.info("\n【步骤7】风险调整...")
        adjusted_return, risk_adjustment = self.apply_risk_adjustment(market_adjusted_return, risk_signals)
        
        # 9. 计算预测价格
        predicted_price = current_price * (1 + adjusted_return / 100)
        
        # 10. 计算预测区间
        high_risk_count = sum(1 for s in risk_signals if s['level'] == 'high')
        confidence = 'low' if high_risk_count > 0 else ('medium' if len(risk_signals) > 1 else 'high')
        
        if confidence == 'high':
            interval_width = 0.05
        elif confidence == 'medium':
            interval_width = 0.08
        else:
            interval_width = 0.12
        
        lower_bound = predicted_price * (1 - interval_width)
        upper_bound = predicted_price * (1 + interval_width)
        
        # 11. 生成投资建议
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
        
        # 12. 整合结果
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
        
        # 13. 打印预测结果
        print("\n" + "="*80)
        print("增强数据预测结果 (真实数据版本)")
        print("="*80)
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
        
        print("\n" + "="*80)
        
        return result


def main():
    """主函数"""
    predictor = RealEnhancedPrediction()
    result = predictor.predict(horizon=5)
    return result


if __name__ == "__main__":
    main()
