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
            'xgboost': 0.40,      # XGBoost 40%
            'enhanced': 0.40,    # 增强数据调整 40%
            'fundamental': 0.08, # 基本面 8%
            'macro': 0.02        # 宏观 2%
        }
        
        print("="*70)
        print("集成预测系统 - 传统模型 + 真实增强数据")
        print("="*70)
    
    def get_market_state(self, enhanced_data: dict) -> str:
        """判断市场状态 - 仅基于宏观数据，不依赖新闻情绪"""
        risk_signals = enhanced_data.get('risk_signals', [])
        high_risk_count = sum(1 for s in risk_signals if s.get('level') == 'high')

        # 仅根据风险信号判断市场状态
        if high_risk_count >= 2 or len(risk_signals) >= 4:
            return 'crisis'
        elif high_risk_count >= 1 or len(risk_signals) >= 1:
            return 'risky'
        else:
            # 无风险信号时，基于宏观数据判断
            macro = enhanced_data.get('macro', {})
            vix = macro.get('vix', {}).get('value', 19.0)
            dollar_index = macro.get('dollar_index', {}).get('value', 103.0)
            pmi = macro.get('pmi', {}).get('value', 50.0)

            # VIX高 = 熊市信号
            if vix > 22:
                return 'bear'
            # 美元指数强 = 熊市信号
            elif dollar_index > 105:
                return 'bear'
            # PMI扩张 = 牛市信号
            elif pmi > 52:
                return 'bull'
        return 'normal'
    
    def get_dynamic_weights(self, market_state: str, enhanced_data: dict) -> dict:
        """动态权重调整 - 基于市场状态，不依赖新闻情绪"""
        weights = self.base_weights.copy()

        # 统一配置：XGBoost 40% | 增强数据调整 40% | 基本面 8% | 宏观 2%
        weights['xgboost'] = 0.40
        weights['enhanced'] = 0.40
        weights['fundamental'] = 0.08
        weights['macro'] = 0.02

        logger.info(f"市场状态: {market_state}，权重 - XGBoost 40% | 增强数据调整 40% | 基本面 8% | 宏观 2%")

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
                    # 美元指数偏高 - 加强向下调整力度
                    adjustment = 0.94  # 降低6%（原来是4%）
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
            # 获取更多数据以满足宏观因子模型的训练需求(至少100条)
            current_data = self.data_mgr.get_full_data(days=365)
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
                # 模型未训练，基于当前市场趋势动态计算
                # 计算最近几天的平均涨跌幅
                if len(current_data) >= 5:
                    recent_returns = current_data['close'].pct_change().tail(5).dropna()
                    avg_return = recent_returns.mean() * 100
                    # 降低波动，使用0.5倍的平均收益率
                    xgboost_return = avg_return * 0.5
                    xgboost_price = current_price * (1 + xgboost_return / 100)
                    logger.info(f"基于最近5天趋势计算: 平均{avg_return:+.2f}%, 预测{xgboost_return:+.2f}%")
                else:
                    # 数据不足，使用小幅正向均值回归
                    xgboost_return = 0.5  # 0.5%小幅正向
                    xgboost_price = current_price * (1 + xgboost_return / 100)
            logger.info(f"XGBoost预测: ¥{xgboost_price:,.2f} ({xgboost_return:+.2f}%)")
        except Exception as e:
            logger.warning(f"XGBoost预测失败: {e}，使用默认值")
            # 使用基于市场趋势的默认值
            if len(current_data) >= 3:
                recent_returns = current_data['close'].pct_change().tail(3).dropna()
                avg_return = recent_returns.mean() * 100
                xgboost_return = avg_return * 0.5
            else:
                xgboost_return = 0.5
            xgboost_price = current_price * (1 + xgboost_return / 100)
        
        # 宏观模型预测
        macro_price = current_price
        macro_return = 0.0
        try:
            # 需要先训练模型
            self.macro_model.train(current_data)
            # 宏观因子模型使用90天预测,不管传入的horizon是多少
            macro_horizon = 90
            macro_pred = self.macro_model.predict(current_data, horizon=macro_horizon)
            macro_price = macro_pred['predicted_price']
            macro_return = macro_pred['predicted_return']
            logger.info(f"宏观模型预测 ({macro_horizon}天): ¥{macro_price:,.2f} ({macro_return:+.2f}%)")
        except Exception as e:
            logger.warning(f"宏观模型预测失败: {e}，使用默认值")
            # 基于最近趋势计算，而不是固定6.13%
            if len(current_data) >= 5:
                recent_returns = current_data['close'].pct_change().tail(5).dropna()
                avg_return = recent_returns.mean() * 100
                macro_return = avg_return * 0.8
            else:
                macro_return = 0.3  # 小幅正向
            macro_price = current_price * (1 + macro_return / 100)

        # 基本面模型预测
        fund_price = current_price
        fund_return = 0.0
        try:
            # 需要先训练模型
            self.fund_model.train(current_data)
            # 基本面模型使用180天预测,不管传入的horizon是多少
            fund_horizon = 180
            fund_pred = self.fund_model.predict(current_data, horizon=fund_horizon)
            fund_price = fund_pred['predicted_price']
            fund_return = fund_pred['predicted_return']
            logger.info(f"基本面模型预测 ({fund_horizon}天): ¥{fund_price:,.2f} ({fund_return:+.2f}%)")
        except Exception as e:
            logger.warning(f"基本面模型预测失败: {e}，使用默认值")
            # 基于最近趋势计算，而不是固定0.97%
            if len(current_data) >= 5:
                recent_returns = current_data['close'].pct_change().tail(5).dropna()
                avg_return = recent_returns.mean() * 100
                fund_return = avg_return * 0.6
            else:
                fund_return = 0.2  # 小幅正向
            fund_price = current_price * (1 + fund_return / 100)
        
        # 6. 传统模型加权融合（仅包含XGBoost、宏观、基本面）
        # 注意：这里计算的是不含增强数据调整的传统模型融合
        traditional_weights = {
            'xgboost': weights['xgboost'] + weights['enhanced'],  # XGBoost + 增强数据调整
            'macro': weights['macro'],
            'fundamental': weights['fundamental']
        }
        
        weighted_price = (
            xgboost_price * traditional_weights['xgboost'] +
            macro_price * traditional_weights['macro'] +
            fund_price * traditional_weights['fundamental']
        )
        weighted_return = (weighted_price - current_price) / current_price * 100

        logger.info(f"传统模型加权融合: ¥{weighted_price:,.2f} ({weighted_return:+.2f}%)")

        # 7. 获取风险调整因子（用于增强数据调整）
        # 增强数据调整基于XGBoost价格，而非加权融合价格
        risk_adjusted = self.apply_risk_adjustment(xgboost_price, enhanced_data)
        risk_factor = risk_adjusted['adjustment_factor']
        enhanced_price = risk_adjusted['adjusted_prediction']
        enhanced_return = (enhanced_price - current_price) / current_price * 100

        logger.info(f"风险调整因子: {risk_factor:.4f}")
        logger.info(f"调整详情: {'; '.join(risk_adjusted['adjustment_details'])}")
        logger.info(f"增强数据调整价格: ¥{enhanced_price:,.2f} ({enhanced_return:+.2f}%)")

        # 8. 集成系统预测（综合所有因素）
        # 加权融合 = XGBoost 40% + 增强数据调整 40% + 基本面 8% + 宏观 2%
        integrated_weighted_price = (
            xgboost_price * weights['xgboost'] +
            enhanced_price * weights['enhanced'] +
            fund_price * weights['fundamental'] +
            macro_price * weights['macro']
        )
        integrated_return = (integrated_weighted_price - current_price) / current_price * 100

        logger.info(f"集成加权融合: ¥{integrated_weighted_price:,.2f} ({integrated_return:+.2f}%)")

        # 9. 根据市场状态调整
        if market_state == 'bull':
            # 牛市：如果是正预测增加，如果是负预测减小幅度
            if integrated_return >= 0:
                integrated_return *= 1.05  # 正向预测增加5%
            else:
                integrated_return *= 0.95  # 负向预测减小5%（趋向于0）
            logger.info(f"市场状态牛市调整: {integrated_return:+.2f}%")
        elif market_state == 'bear':
            # 熊市：如果是正预测减小，如果是负预测增加
            if integrated_return >= 0:
                integrated_return *= 0.95  # 正向预测减少5%
            else:
                integrated_return *= 1.05  # 负向预测增加5%（更看跌）
            logger.info(f"市场状态熊市调整: {integrated_return:+.2f}%")
        elif market_state == 'crisis':
            # 危机：大幅向下调整
            integrated_return *= 0.85  # 减少15%
            logger.info(f"市场状态危机调整: {integrated_return:+.2f}%")

        # 应用风险调整（因为增强数据已经在加权融合中，这里不再重复应用）
        # 集成系统的风险调整已经通过增强数据的权重体现
        logger.info(f"市场状态调整后: {integrated_return:+.2f}%")

        # 计算最终价格
        final_price = current_price * (1 + integrated_return / 100)
        final_return = integrated_return

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
                'enhanced': {
                    'price': enhanced_price,
                    'return_pct': enhanced_return,
                    'weight': weights['enhanced'],
                    'source': '增强数据调整'
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
        print(f"  传统模型融合价格: ¥{weighted['price']:,.2f} ({weighted['return_pct']:+.2f}%)")
        print(f"  传统模型权重配置: XGBoost {result['weights']['xgboost']:.0%} | "
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

        # 集成系统加权融合
        print(f"\n【集成系统加权融合】")
        print(f"  集成权重配置: XGBoost {result['weights']['xgboost']:.0%} | "
              f"增强数据调整 {result['weights']['enhanced']:.0%} | "
              f"宏观 {result['weights']['macro']:.0%} | "
              f"基本面 {result['weights']['fundamental']:.0%}")

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
