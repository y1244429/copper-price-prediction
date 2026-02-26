"""
铜价格预测模型
基于技术指标、基本面因素和市场情绪的综合预测模型
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json


class CopperPriceModel:
    """铜价格预测模型类"""

    def __init__(self):
        # 基础参数
        self.current_price = 103040  # 当前沪铜价格(元/吨)
        self.lme_price = 13253.5     # 当前LME价格(美元/吨)
        self.exchange_rate = 7.78    # 汇率

        # 库存数据(吨)
        self.lme_inventory = 249650
        self.shfe_inventory = 287806
        self.comex_inventory = 545257
        self.china_social_inventory = 507100

        # 技术指标
        self.moving_averages = {
            'MA5': 102800,
            'MA10': 102500,
            'MA20': 101800,
            'MA60': 100500,
        }

        # 基本面权重
        self.weights = {
            'inventory': 0.30,      # 库存因素
            'technical': 0.25,      # 技术面
            'fundamental': 0.25,    # 基本面(供需)
            'sentiment': 0.10,      # 市场情绪
            'macro': 0.10,          # 宏观经济
        }

    def calculate_inventory_score(self) -> float:
        """
        计算库存得分
        库存增加 = 负分(看空)
        库存减少 = 正分(看多)
        """
        # 库存变化率(假设)
        lme_change_rate = 0.026  # +2.6%
        shfe_change_rate = 0.038  # +3.8%

        # 归一化到[-1, 1]
        lme_score = -min(lme_change_rate / 0.05, 1.0)
        shfe_score = -min(shfe_change_rate / 0.05, 1.0)

        # 综合得分
        inventory_score = (lme_score + shfe_score) / 2

        return inventory_score

    def calculate_technical_score(self) -> float:
        """计算技术面得分"""
        current = self.current_price

        # 均线排列得分
        ma_scores = []
        for period, ma in self.moving_averages.items():
            if current > ma:
                ma_scores.append(1.0)
            else:
                ma_scores.append(-1.0)

        # 价格位置得分
        ma20 = self.moving_averages['MA20']
        ma60 = self.moving_averages['MA60']
        position_score = (current - ma60) / (ma20 - ma60 + 0.01)
        position_score = max(-1.0, min(1.0, position_score))

        # 综合技术得分
        technical_score = (np.mean(ma_scores) * 0.6 + position_score * 0.4)

        return technical_score

    def calculate_fundamental_score(self) -> float:
        """计算基本面得分(供需关系)"""
        # 供应端
        supply_factors = {
            'mine_production': 0.7,      # 铜矿供应偏紧
            'smelter_output': 0.8,       # 冶炼厂产量高位但增速放缓
            'import_volume': -0.3,       # 进口较少
        }

        # 需求端
        demand_factors = {
            'seasonal_factor': -0.4,     # 传统消费淡季
            'q2_expectation': 0.8,      # Q2旺季预期
            'ai_infrastructure': 0.9,    # AI基建需求
            'new_energy': 0.8,          # 新能源需求
            'real_estate': -0.2,        # 房地产需求弱
        }

        supply_score = np.mean(list(supply_factors.values()))
        demand_score = np.mean(list(demand_factors.values()))

        # 供需综合得分(需求减供应,数值大表示供不应求)
        fundamental_score = (demand_score - supply_score) / 2

        return fundamental_score

    def calculate_sentiment_score(self) -> float:
        """计算市场情绪得分"""
        sentiment_factors = {
            'institutional_outlook': 0.7,    # 机构看多
            'trader_position': 0.5,        # 交易员偏多
            'institutional_position': 0.6, # 机构持仓增加
            'market_news': 0.4,            # 新闻面偏多
        }

        sentiment_score = np.mean(list(sentiment_factors.values()))

        return sentiment_score

    def calculate_macro_score(self) -> float:
        """计算宏观经济得分"""
        macro_factors = {
            'us_tariff': -0.6,      # 美国关税负向
            'inflation': -0.4,      # 通胀压力
            'interest_rate': -0.3,  # 利率高位
            'china_policy': 0.7,    # 中国政策支持
            'global_growth': 0.4,   # 全球温和增长
        }

        macro_score = np.mean(list(macro_factors.values()))

        return macro_score

    def predict_short_term(self, days: int = 5) -> Dict:
        """
        短期价格预测(1-30天)
        """
        # 计算各因子得分
        inventory_score = self.calculate_inventory_score()
        technical_score = self.calculate_technical_score()
        fundamental_score = self.calculate_fundamental_score()
        sentiment_score = self.calculate_sentiment_score()
        macro_score = self.calculate_macro_score()

        # 综合得分
        total_score = (
            inventory_score * self.weights['inventory'] +
            technical_score * self.weights['technical'] +
            fundamental_score * self.weights['fundamental'] +
            sentiment_score * self.weights['sentiment'] +
            macro_score * self.weights['macro']
        )

        # 计算预测涨跌幅
        volatility = 0.02  # 日波动率
        predicted_return = total_score * volatility * days

        # 预测价格
        predicted_price = self.current_price * (1 + predicted_return / 100)

        # 支撑阻力位
        support1 = self.current_price * 0.98
        support2 = self.current_price * 0.96
        resistance1 = self.current_price * 1.02
        resistance2 = self.current_price * 1.04

        return {
            'period': f'{days}天',
            'current_price': self.current_price,
            'predicted_price': round(predicted_price, 2),
            'predicted_change': round(predicted_return, 2),
            'trend': '上涨' if predicted_return > 0 else '下跌',
            'support': {
                '支撑1': round(support1, 2),
                '支撑2': round(support2, 2),
            },
            'resistance': {
                '阻力1': round(resistance1, 2),
                '阻力2': round(resistance2, 2),
            },
            'scores': {
                '库存得分': round(inventory_score, 3),
                '技术面得分': round(technical_score, 3),
                '基本面得分': round(fundamental_score, 3),
                '情绪得分': round(sentiment_score, 3),
                '宏观得分': round(macro_score, 3),
                '综合得分': round(total_score, 3),
            },
            'confidence': '中等',
            'recommendation': '区间操作' if abs(predicted_return) < 1 else ('逢低买入' if predicted_return > 1 else '逢高卖出')
        }

    def predict_medium_term(self, months: int = 3) -> Dict:
        """
        中期价格预测(1-6个月)
        """
        # 中期更看重基本面
        medium_weights = {
            'inventory': 0.20,
            'technical': 0.20,
            'fundamental': 0.35,
            'sentiment': 0.15,
            'macro': 0.10,
        }

        # 计算各因子得分
        fundamental_score = self.calculate_fundamental_score()
        technical_score = self.calculate_technical_score()

        # 季节性调整(Q2旺季预期)
        seasonal_boost = 0.5 if months <= 3 else 0.0

        # 综合得分
        total_score = (
            fundamental_score * 0.5 +
            technical_score * 0.3 +
            seasonal_boost * 0.2
        )

        # 预测涨跌幅(中期波动更大)
        volatility = 0.05 * months
        predicted_return = total_score * volatility

        # 预测价格
        predicted_price = self.current_price * (1 + predicted_return / 100)

        # Q2冲高,Q3回落
        if months == 3:
            predicted_price *= 1.05  # Q2旺季溢价
        elif months == 6:
            predicted_price *= 0.95  # Q3回调

        return {
            'period': f'{months}个月',
            'current_price': self.current_price,
            'predicted_price': round(predicted_price, 2),
            'predicted_change': round(predicted_return, 2),
            'trend': '上涨' if predicted_return > 0 else '下跌',
            'target_range': {
                '目标价': round(predicted_price, 2),
                '波动区间': [
                    round(predicted_price * 0.95, 2),
                    round(predicted_price * 1.05, 2)
                ]
            },
            'key_factors': [
                f'Q{"二" if months <= 3 else "三"}季节性因素',
                '供需基本面',
                '库存变化',
                '宏观经济环境',
            ],
            'confidence': '较高',
            'recommendation': '逢低布局多单' if predicted_return > 2 else '观望为主'
        }

    def predict_long_term(self, years: int = 1) -> Dict:
        """
        长期价格预测(1-3年)
        """
        # 长期看结构性因素
        long_term_factors = {
            'energy_transition': 0.9,    # 能源转型
            'ai_infrastructure': 0.95,   # AI基建
            'supply_constraint': 0.85,   # 供应约束
            'urbanization': 0.6,         # 城市化
            'population_growth': 0.4,    # 人口增长
        }

        # 长期平均增长率
        annual_growth_rate = 0.08  # 8%年均增长

        # 预测价格
        predicted_price = self.current_price * (1 + annual_growth_rate) ** years

        # LME价格预测(机构观点)
        lme_forecast = {
            '2026_Q2': 13500,  # 摩根大通
            '2026_Q3': 13000,
            '2026_avg': 11400,  # 高盛
            '2035': 15000,      # 高盛长期
        }

        return {
            'period': f'{years}年',
            'current_price': self.current_price,
            'predicted_price': round(predicted_price, 2),
            'annual_growth': f'{annual_growth_rate * 100:.1f}%',
            'trend': '结构性牛市',
            'price_forecast': {
                '沪铜预测': round(predicted_price, 2),
                'LME预测(美元)': lme_forecast,
            },
            'key_drivers': {
                '需求端': ['能源转型', 'AI基建', '新能源车', '电网升级'],
                '供应端': ['铜精矿偏紧', '新矿山投产慢', '政策限制'],
                '技术端': ['电气化进程', '数据中心建设'],
            },
            'institutional_views': [
                '摩根大通: 2026年铜市缺口13万吨',
                '高盛: 长期看多,2035年或达15,000美元',
                '中信建投: 中长线逢低布局',
            ],
            'confidence': '长期逻辑清晰',
            'recommendation': '长期持有,每次深调布局'
        }

    def get_market_assessment(self) -> Dict:
        """获取市场评估报告"""
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'current_price': self.current_price,
            'price_range': '101,500-103,500',
            'trend': '高位震荡',
            'cycle_position': '短期承压,中期向好,长期结构性牛市',
            'key_levels': {
                '支撑位': {
                    '第一支撑': 100000,
                    '第二支撑': 98000,
                    '强支撑': 96000,
                },
                '阻力位': {
                    '第一阻力': 104000,
                    '第二阻力': 106000,
                    '强阻力': 108000,
                },
            },
            'inventory_status': {
                'LME': f'{self.lme_inventory:,}吨(连增11天)',
                'SHFE': f'{self.shfe_inventory:,}吨(环比增加)',
                '中国社库': f'{self.china_social_inventory:,}吨(十年峰值)',
                'status': '累库压力存在',
            },
            'market_sentiment': {
                '机构观点': '偏多',
                '交易员情绪': '中性偏多',
                '持仓情况': '多单增加',
            },
            'trading_strategy': {
                'short_term': '区间操作,高抛低吸',
                'medium_term': 'Q2前逢低布局',
                'long_term': '长期持有核心资产',
            },
            'risk_factors': [
                '库存累库压力',
                '消费淡季',
                '美国关税',
                '全球经济放缓',
            ],
            'opportunity_factors': [
                'Q2旺季预期',
                '供应缺口',
                'AI基建需求',
                '能源转型',
            ],
        }


def main():
    """主函数 - 演示模型使用"""
    model = CopperPriceModel()

    # 短期预测
    print("=" * 60)
    print("铜价格短期预测")
    print("=" * 60)
    short_term = model.predict_short_term(days=5)
    print(json.dumps(short_term, indent=2, ensure_ascii=False))

    # 中期预测
    print("\n" + "=" * 60)
    print("铜价格中期预测")
    print("=" * 60)
    medium_term = model.predict_medium_term(months=3)
    print(json.dumps(medium_term, indent=2, ensure_ascii=False))

    # 长期预测
    print("\n" + "=" * 60)
    print("铜价格长期预测")
    print("=" * 60)
    long_term = model.predict_long_term(years=1)
    print(json.dumps(long_term, indent=2, ensure_ascii=False))

    # 市场评估
    print("\n" + "=" * 60)
    print("市场评估报告")
    print("=" * 60)
    assessment = model.get_market_assessment()
    print(json.dumps(assessment, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
