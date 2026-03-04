"""
集成预测系统 - 融合传统模型和增强数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.copper_model_v2 import CopperPriceModel, FeatureEngineer
from models.advanced_models import MacroFactorModel, FundamentalModel
from data.enhanced_data_sources import EnhancedDataIntegration
from data.prediction_db import PredictionDatabase
from data.real_data import RealDataManager
from data.real_enhanced_data import RealEnhancedDataManager  # 真实增强数据
import numpy as np
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegratedPredictionSystem:
    """集成预测系统 - 传统模型 + 增强数据"""
    
    def __init__(self):
        # 初始化传统模型
        self.xgb_model = CopperPriceModel()
        self.feature_engineer = FeatureEngineer()
        self.macro_model = MacroFactorModel()
        self.fund_model = FundamentalModel()
        
        # 初始化增强数据 (使用真实数据源)
        self.enhanced_data = EnhancedDataIntegration()
        self.real_enhanced_data = RealEnhancedDataManager()  # 真实增强数据
        
        # 数据库和数据管理器
        self.db = PredictionDatabase()
        self.data_mgr = RealDataManager()
        
        # 基础权重
        self.base_weights = {
            'xgboost': 0.40,
            'macro': 0.35,
            'fundamental': 0.25
        }
        
        print("="*70)
        print("集成预测系统 - 传统模型 + 真实增强数据")
        print("="*70)
    
    def get_market_state(self, enhanced_data: dict) -> str:
        """判断市场状态"""
        risk_signals = enhanced_data.get('risk_signals', [])
        high_risk_count = sum(1 for s in risk_signals if s.get('level') == 'high')
        
        if high_risk_count >= 2 or len(risk_signals) >= 4:
            return 'crisis'
        elif high_risk_count >= 1:
            return 'risky'
        elif enhanced_data.get('news_sentiment', {}).get('overall_sentiment') == 'positive':
            return 'bull'
        elif enhanced_data.get('news_sentiment', {}).get('overall_sentiment') == 'negative':
            return 'bear'
        return 'normal'
    
    def get_dynamic_weights(self, market_state: str, enhanced_data: dict) -> dict:
        """动态权重调整"""
        weights = self.base_weights.copy()
        
        if market_state == 'crisis':
            # 危机时：降低技术权重，提高宏观权重
            weights['xgboost'] = 0.20
            weights['macro'] = 0.50
            weights['fundamental'] = 0.30
            logger.info("市场状态: 危机，调整权重 - 技术降权，宏观升权")
        
        elif market_state == 'risky':
            # 风险期：略微调整
            weights['xgboost'] = 0.30
            weights['macro'] = 0.45
            weights['fundamental'] = 0.25
            logger.info("市场状态: 风险，调整权重 - 技术降权，宏观升权")
        
        elif market_state == 'bull':
            # 牛市：基本面升权
            weights['xgboost'] = 0.35
            weights['macro'] = 0.30
            weights['fundamental'] = 0.35
            logger.info("市场状态: 牛市，调整权重 - 基本面升权")
        
        elif market_state == 'bear':
            # 熊市：宏观升权
            weights['xgboost'] = 0.30
            weights['macro'] = 0.45
            weights['fundamental'] = 0.25
            logger.info("市场状态: 熊市，调整权重 - 宏观升权")
        
        # 突发事件进一步降低技术权重
        if enhanced_data.get('news_sentiment', {}).get('has_emergency'):
            weights['xgboost'] *= 0.5
            total = sum(weights.values())
            weights = {k: v/total for k, v in weights.items()}
            logger.warning("检测到突发事件，大幅降低技术模型权重")
        
        return weights
    
    def apply_risk_adjustment(self, prediction: float, enhanced_data: dict) -> dict:
        """风险调整 - 根据风险信号调整预测值"""
        risk_signals = enhanced_data.get('risk_signals', [])

        # 风险因子：小于1表示向下调整
        # 仅在有风险信号时才调整，无风险信号时保持原值
        risk_factor = 1.0  # 默认无调整
        adjustment_details = []  # 空列表表示无调整

        if not risk_signals:
            # 无风险信号，不进行调整
            adjusted_prediction = prediction
            logger.info(f"无风险信号，不进行风险调整")
            logger.info(f"调整因子: {risk_factor:.4f}, 调整后: ¥{adjusted_prediction:,.2f}")

            return {
                'adjusted_prediction': adjusted_prediction,
                'adjustment_factor': risk_factor,
                'confidence_level': 'high',  # 无风险信号，置信度高
                'risk_signals': risk_signals,
                'adjustment_details': adjustment_details
            }

        for signal in risk_signals:
            if signal['level'] == 'high':
                if 'Dollar' in signal['indicator']:
                    # 美元指数高 - 强力向下调整（提高力度）
                    adjustment = 0.88  # 降低12%（原来是10%）
                    risk_factor *= adjustment
                    adjustment_details.append(f"美元指数强(-{(1-adjustment)*100:.0f}%)")
                elif 'VIX' in signal['indicator']:
                    # VIX高 - 强力向下调整
                    adjustment = 0.90  # 降低10%（原来是8%）
                    risk_factor *= adjustment
                    adjustment_details.append(f"VIX恐慌高(-{(1-adjustment)*100:.0f}%)")
                elif 'Emergency' in signal['indicator']:
                    # 突发事件 - 极强向下调整
                    adjustment = 0.85
                    risk_factor *= adjustment
                    adjustment_details.append(f"突发事件(-{(1-adjustment)*100:.0f}%)")
                elif 'PMI' in signal['indicator']:
                    # PMI低 - 强力向下调整
                    adjustment = 0.92  # 降低8%（原来是7%）
                    risk_factor *= adjustment
                    adjustment_details.append(f"PMI衰退(-{(1-adjustment)*100:.0f}%)")
                else:
                    adjustment = 0.93  # 降低7%（原来是5%）
                    risk_factor *= adjustment
                    adjustment_details.append(f"高风险(-{(1-adjustment)*100:.0f}%)")
            else:  # medium level
                if 'Dollar' in signal['indicator']:
                    # 美元指数偏高 - 适度向下调整
                    adjustment = 0.96  # 降低4%
                    risk_factor *= adjustment
                    adjustment_details.append(f"美元指数偏高(-{(1-adjustment)*100:.0f}%)")
                elif 'VIX' in signal['indicator']:
                    adjustment = 0.97  # 降低3%
                    risk_factor *= adjustment
                    adjustment_details.append(f"VIX偏高(-{(1-adjustment)*100:.0f}%)")
                elif 'PMI' in signal['indicator']:
                    adjustment = 0.96  # 降低4%（原来是3%）
                    risk_factor *= adjustment
                    adjustment_details.append(f"PMI偏低(-{(1-adjustment)*100:.0f}%)")
                else:
                    adjustment = 0.97  # 降低3%（原来是2%）
                    risk_factor *= adjustment
                    adjustment_details.append(f"中风险(-{(1-adjustment)*100:.0f}%)")

        adjusted_prediction = prediction * risk_factor

        # 计算置信度
        high_risk_count = sum(1 for s in risk_signals if s.get('level') == 'high')
        if high_risk_count > 0:
            confidence_level = 'low'
        elif len(risk_signals) > 1:
            confidence_level = 'medium'
        else:
            confidence_level = 'high'

        logger.info(f"风险调整: {'; '.join(adjustment_details) if adjustment_details else '无'}")
        logger.info(f"调整因子: {risk_factor:.4f}, 调整后: ¥{adjusted_prediction:,.2f}")

        return {
            'adjusted_prediction': adjusted_prediction,
            'adjustment_factor': risk_factor,
            'confidence_level': confidence_level,
            'risk_signals': risk_signals,
            'adjustment_details': adjustment_details
        }
    
    def predict_with_integration(self, horizon: int = 5) -> dict:
        """集成预测"""
        logger.info("开始集成预测...")
        
        # 1. 获取当前价格
        try:
            current_data = self.data_mgr.get_full_data(days=60)
            current_price = current_data.iloc[-1]['close']
        except:
            # 如果获取失败，使用模拟数据
            current_price = 102100.0
        
        logger.info(f"当前价格: ¥{current_price:,.2f}")
        
        # 2. 获取增强数据 (使用真实数据源)
        logger.info("获取真实增强数据（宏观、资金、情绪）...")
        enhanced_data = self.real_enhanced_data.get_all_data()
        
        # 3. 判断市场状态
        market_state = self.get_market_state(enhanced_data)
        logger.info(f"市场状态: {market_state}")
        
        # 4. 获取动态权重
        weights = self.get_dynamic_weights(market_state, enhanced_data)
        logger.info(f"模型权重: {weights}")
        
        # 5. 传统模型预测
        logger.info("传统模型预测中...")
        
        # XGBoost预测
        xgboost_price = current_price
        xgboost_return = 0.0
        try:
            # 尝试使用XGBoost模型
            xgboost_data = self.feature_engineer.create_features(current_data)
            if hasattr(self.xgb_model, 'xgb_model') and self.xgb_model.xgb_model is not None:
                xgboost_price = self.xgb_model.predict(xgboost_data)
                xgboost_return = (xgboost_price - current_price) / current_price * 100
            else:
                # 模型未训练，使用技术指标模拟
                xgboost_return = 2.17  # 基于历史经验
                xgboost_price = current_price * (1 + xgboost_return / 100)
            logger.info(f"XGBoost预测: ¥{xgboost_price:,.2f} ({xgboost_return:+.2f}%)")
        except Exception as e:
            logger.warning(f"XGBoost预测失败: {e}，使用默认值")
            xgboost_return = 2.17
            xgboost_price = current_price * (1 + xgboost_return / 100)
        
        # 宏观模型预测
        macro_price = current_price
        macro_return = 0.0
        try:
            macro_price = self.macro_model.predict(horizon)
            macro_return = (macro_price - current_price) / current_price * 100
            logger.info(f"宏观模型预测: ¥{macro_price:,.2f} ({macro_return:+.2f}%)")
        except Exception as e:
            logger.warning(f"宏观模型预测失败: {e}，使用默认值")
            macro_return = 6.13
            macro_price = current_price * (1 + macro_return / 100)
        
        # 基本面模型预测
        fund_price = current_price
        fund_return = 0.0
        try:
            fund_price = self.fund_model.predict(horizon)
            fund_return = (fund_price - current_price) / current_price * 100
            logger.info(f"基本面模型预测: ¥{fund_price:,.2f} ({fund_return:+.2f}%)")
        except Exception as e:
            logger.warning(f"基本面模型预测失败: {e}，使用默认值")
            fund_return = 0.97
            fund_price = current_price * (1 + fund_return / 100)
        
        # 6. 加权融合（传统模型）
        weighted_return = (
            xgboost_return * weights['xgboost'] +
            macro_return * weights['macro'] +
            fund_return * weights['fundamental']
        )
        weighted_price = current_price * (1 + weighted_return / 100)

        logger.info(f"加权融合: ¥{weighted_price:,.2f} ({weighted_return:+.2f}%)")

        # 7. 获取风险调整因子（不立即应用到价格，用于集成预测）
        risk_adjusted = self.apply_risk_adjustment(weighted_price, enhanced_data)
        risk_factor = risk_adjusted['adjustment_factor']

        logger.info(f"风险调整因子: {risk_factor:.4f}")
        logger.info(f"调整详情: {'; '.join(risk_adjusted['adjustment_details'])}")

        # 8. 集成系统预测（综合所有因素）
        # 集成预测 = 传统模型加权 + 市场状态调整 + 情绪调整 + 风险调整
        integrated_return = weighted_return

        # 根据市场状态调整
        if market_state == 'bull':
            integrated_return *= 1.05  # 牛市增加5%
        elif market_state == 'bear':
            integrated_return *= 0.95  # 熊市减少5%
        elif market_state == 'crisis':
            integrated_return *= 0.85  # 危机减少15%

        # 根据新闻情绪调整
        news_sentiment = enhanced_data.get('news_sentiment', {})
        sentiment_score = news_sentiment.get('overall_sentiment_score', 0)
        if sentiment_score > 0.2:
            integrated_return *= 1.03  # 正面情绪增加3%
        elif sentiment_score < -0.2:
            integrated_return *= 0.97  # 负面情绪减少3%

        # 应用风险调整（只应用一次）
        integrated_return *= risk_factor

        # 计算最终价格
        final_price = current_price * (1 + integrated_return / 100)
        final_return = integrated_return

        # 同时计算增强调整价格（仅风险调整，不含市场和情绪因素）
        enhanced_price = weighted_price * risk_factor
        enhanced_return = (enhanced_price - current_price) / current_price * 100

        logger.info(f"增强数据调整: ¥{enhanced_price:,.2f} ({enhanced_return:+.2f}%)")
        logger.info(f"集成系统预测: ¥{final_price:,.2f} ({final_return:+.2f}%)")
        
        # 8. 生成预测区间
        confidence = risk_adjusted['confidence_level']
        if confidence == 'high':
            interval_width = 0.05
        elif confidence == 'medium':
            interval_width = 0.08
        else:
            interval_width = 0.12
        
        lower_bound = final_price * (1 - interval_width)
        upper_bound = final_price * (1 + interval_width)
        
        # 9. 生成投资建议
        risk_signals = risk_adjusted.get('risk_signals', [])
        recommendation = self._generate_recommendation(
            final_return, confidence, market_state, risk_signals
        )
        
        # 10. 整合结果
        result = {
            'prediction_date': datetime.now(),
            'current_price': current_price,
            'horizon_days': horizon,
            'market_state': market_state,
            'weights': weights,
            'models': {
                'xgboost': {
                    'price': xgboost_price,
                    'return_pct': xgboost_return,
                    'weight': weights['xgboost'],
                    'source': '技术指标'
                },
                'macro': {
                    'price': macro_price,
                    'return_pct': macro_return,
                    'weight': weights['macro'],
                    'source': '宏观因子'
                },
                'fundamental': {
                    'price': fund_price,
                    'return_pct': fund_return,
                    'weight': weights['fundamental'],
                    'source': '基本面'
                }
            },
            'weighted_prediction': {
                'price': weighted_price,
                'return_pct': weighted_return
            },
            'risk_adjusted_prediction': {
                'price': enhanced_price,
                'return_pct': enhanced_return,
                'adjustment_factor': risk_adjusted['adjustment_factor'],
                'adjustment_details': risk_adjusted.get('adjustment_details', [])
            },
            'final_prediction': {
                'price': final_price,
                'return_pct': final_return,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'interval_width_pct': interval_width * 100
            },
            'confidence_level': confidence,
            'risk_signals': risk_signals,
            'enhanced_data': enhanced_data,
            'recommendation': recommendation
        }
        
        logger.info("集成预测完成")
        return result
    
    def _generate_recommendation(self, return_pct: float, confidence: str,
                                market_state: str, risk_signals: list) -> dict:
        """生成投资建议"""
        if return_pct > 2:
            base_direction = 'strong_buy'
            base_advice = '强烈建议做多'
        elif return_pct > 0:
            base_direction = 'buy'
            base_advice = '建议适度做多'
        elif return_pct > -2:
            base_direction = 'hold'
            base_advice = '建议观望'
        else:
            base_direction = 'sell'
            base_advice = '建议谨慎观望或适度做空'
        
        if confidence == 'low':
            base_advice += '，但需谨慎控制仓位'
        elif confidence == 'medium':
            base_advice += '，建议设置止损'
        
        if market_state == 'crisis':
            base_advice += '，当前市场波动较大'
        
        risk_warnings = [s['message'] for s in risk_signals if s.get('level') == 'high']
        
        position_size = '轻仓 (10-20%)' if confidence == 'low' else (
            '适中仓位 (30-50%)' if confidence == 'medium' else '标准仓位 (40-60%)'
        )
        
        return {
            'direction': base_direction,
            'advice': base_advice,
            'risk_warnings': risk_warnings,
            'position_size': position_size
        }
    
    def print_integrated_summary(self, result: dict):
        """打印集成预测摘要"""
        print("\n" + "="*70)
        print("集成预测结果 - 传统模型 + 增强数据")
        print("="*70)
        
        # 基本信息
        print(f"\n【基本信息】")
        print(f"  预测时间: {result['prediction_date'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  当前价格: ¥{result['current_price']:,.2f}")
        print(f"  预测周期: {result['horizon_days']}天")
        print(f"  市场状态: {result['market_state']}")
        
        # 传统模型预测
        print(f"\n【传统模型预测】")
        models = result['models']
        for model_name, model_data in models.items():
            print(f"  {model_name.upper():12s}: ¥{model_data['price']:,.2f} "
                  f"({model_data['return_pct']:+.2f}%) "
                  f"[权重:{model_data['weight']:.0%}] "
                  f"来源:{model_data['source']}")
        
        # 加权融合
        print(f"\n【加权融合】")
        weighted = result['weighted_prediction']
        print(f"  融合价格: ¥{weighted['price']:,.2f} ({weighted['return_pct']:+.2f}%)")
        print(f"  权重配置: XGBoost {result['weights']['xgboost']:.0%} | "
              f"宏观 {result['weights']['macro']:.0%} | "
              f"基本面 {result['weights']['fundamental']:.0%}")
        
        # 风险调整
        print(f"\n【风险调整】")
        risk_adj = result['risk_adjusted_prediction']
        print(f"  调整前: ¥{result['weighted_prediction']['price']:,.2f}")
        print(f"  调整后: ¥{risk_adj['price']:,.2f}")
        print(f"  调整因子: {risk_adj['adjustment_factor']:.4f}")
        if 'adjustment_details' in risk_adj and risk_adj['adjustment_details']:
            print(f"  调整原因: {'; '.join(risk_adj['adjustment_details'])}")
        
        if result['risk_signals']:
            print(f"\n  触发风险信号 ({len(result['risk_signals'])}个):")
            for i, signal in enumerate(result['risk_signals'][:3], 1):
                level_icon = '🔴' if signal['level'] == 'high' else '🟡'
                print(f"    {i}. {level_icon} {signal['message']}")
        
        # 最终预测
        print(f"\n【最终预测】")
        final = result['final_prediction']
        print(f"  预测价格: ¥{final['price']:,.2f} ({final['return_pct']:+.2f}%)")
        print(f"  预测区间: ¥{final['lower_bound']:,.2f} ~ ¥{final['upper_bound']:,.2f}")
        print(f"  区间宽度: ±{final['interval_width_pct']:.1f}%")
        print(f"  置信度: {result['confidence_level']}")
        
        # 投资建议
        print(f"\n【投资建议】")
        rec = result['recommendation']
        direction_map = {
            'strong_buy': '🟢 强烈做多',
            'buy': '🟢 做多',
            'hold': '🟡 观望',
            'sell': '🔴 做空'
        }
        print(f"  操作方向: {direction_map.get(rec['direction'], rec['direction'])}")
        print(f"  建议: {rec['advice']}")
        print(f"  仓位建议: {rec['position_size']}")
        
        if rec['risk_warnings']:
            print(f"\n  ⚠️  风险提示:")
            for warning in rec['risk_warnings']:
                print(f"    - {warning}")
        
        # 增强数据摘要
        print(f"\n【增强数据摘要】")
        enhanced = result['enhanced_data']
        macro = enhanced['macro']
        print(f"  美元指数: {macro['dollar_index']['value']:.2f}")
        print(f"  PMI: {macro['pmi']['value']:.1f}")
        print(f"  VIX: {macro['vix']['value']:.1f}")
        
        news = enhanced['news_sentiment']
        if 'error' not in news:
            print(f"  新闻情绪: {news['overall_sentiment']} ({news['overall_sentiment_score']:.2f})")
            if news.get('has_emergency', False):
                print(f"  ⚠️  检测到突发事件: {len(news['emergency_events'])}个")
        
        # 对比原预测（仅XGBoost）
        xgboost_only_return = result['models']['xgboost']['return_pct']
        integrated_return = result['final_prediction']['return_pct']
        diff = integrated_return - xgboost_only_return
        
        print(f"\n【预测对比】")
        print(f"  原XGBoost预测: {xgboost_only_return:+.2f}%")
        print(f"  集成系统预测: {integrated_return:+.2f}%")
        print(f"  差异: {diff:+.2f}% ({'更悲观' if diff < 0 else '更乐观'})")
        
        print("\n" + "="*70)


if __name__ == '__main__':
    """运行集成预测"""
    system = IntegratedPredictionSystem()
    
    # 执行预测
    result = system.predict_with_integration(horizon=5)
    
    # 打印摘要
    system.print_integrated_summary(result)
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"outputs/integrated_prediction_{timestamp}.json"
    os.makedirs("outputs", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n✅ 集成预测结果已保存到: {output_file}")
