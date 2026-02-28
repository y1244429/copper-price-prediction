"""
模型验证与风险管理模块
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class WalkForwardConfig:
    """滚动窗口回测配置"""
    initial_train_size: int = 252  # 初始训练样本数（约1年）
    test_size: int = 30  # 测试样本数（约1个月）
    step_size: int = 15  # 滚动步长（约半个月）
    min_train_size: int = 100  # 最小训练样本数


@dataclass
class StressTestConfig:
    """压力测试配置"""
    # 中国需求断崖情景
    china_demand_drop: float = -0.30  # 需求下降30%
    
    # 美元流动性危机情景
    usd_spike_scenario: str = '2020-03'  # '2020-03' 或 '2022-09'
    
    # 供应端黑天鹅情景
    supply_shock_types: List[str] = None  # ['chile_earthquake', 'panama_drought']
    
    def __post_init__(self):
        if self.supply_shock_types is None:
            self.supply_shock_types = ['chile_earthquake', 'panama_drought']


@dataclass
class RiskMetricsConfig:
    """风险指标配置"""
    # 方向准确率阈值
    directional_accuracy_threshold: float = 0.65  # 65%为优秀
    
    # 最大回撤阈值
    max_drawdown_threshold: float = 0.05  # 单日波动5%
    
    # 止损逻辑参数
    stop_loss_pct: float = 0.03  # 止损3%
    take_profit_pct: float = 0.05  # 止盈5%


class WalkForwardAnalyzer:
    """滚动窗口回测分析器"""
    
    def __init__(self, config: WalkForwardConfig = None):
        self.config = config or WalkForwardConfig()
    
    def run(self, model, data: pd.DataFrame, features: pd.DataFrame,
            target_col: str = 'close') -> Dict:
        """
        运行滚动窗口回测
        
        Args:
            model: 预测模型（必须有fit和predict方法）
            data: 原始价格数据
            features: 特征数据
            target_col: 目标列名
            
        Returns:
            回测结果字典
        """
        print("="*60)
        print("📊 滚动窗口回测 (Walk-forward Analysis)")
        print("="*60)
        
        # 对齐数据
        aligned_idx = data.index.intersection(features.index)
        data_aligned = data.loc[aligned_idx]
        features_aligned = features.loc[aligned_idx]
        
        total_samples = len(aligned_idx)
        predictions = []
        actuals = []
        indices = []
        
        # 滚动窗口
        test_start = self.config.initial_train_size
        
        fold = 0
        while test_start + self.config.test_size < total_samples:
            fold += 1
            
            # 训练集和测试集
            train_end = test_start - 1
            test_end = test_start + self.config.test_size - 1
            
            train_X = features_aligned.iloc[:train_end]
            train_y = data_aligned[target_col].iloc[:train_end]
            
            test_X = features_aligned.iloc[test_start:test_end+1]
            test_y = data_aligned[target_col].iloc[test_start:test_end+1]
            
            # 检查数据量
            if len(train_X) < self.config.min_train_size:
                print(f"  Fold {fold}: 训练数据不足，跳过")
                test_start += self.config.step_size
                continue
            
            try:
                # 训练模型
                if hasattr(model, 'fit'):
                    # 清除NaN值
                    train_X_clean = train_X.dropna()
                    train_y_clean = train_y.loc[train_X_clean.index]
                    
                    model.fit(train_X_clean, train_y_clean)
                
                # 预测
                if hasattr(model, 'predict'):
                    pred = model.predict(test_X)
                    # 处理返回字典的情况（如宏观因子模型和基本面模型）
                    if isinstance(pred, dict):
                        if 'predicted_price' in pred:
                            pred = np.full(len(test_X), pred['predicted_price'])
                        else:
                            pred = self._fallback_predict(test_X, train_y)
                else:
                    # 备用预测逻辑
                    pred = self._fallback_predict(test_X, train_y)
                
                predictions.extend(pred)
                actuals.extend(test_y.values)
                indices.extend(test_y.index)
                
                print(f"  Fold {fold}: 训练{len(train_X)}条 | 预测{len(test_X)}条 | "
                      f"MAE={np.mean(np.abs(np.array(pred) - test_y.values)):.2f}")
                
                # 确保pred是numpy数组
                if not isinstance(predictions[-len(test_X):], list):
                    predictions = list(predictions)  # 转换为列表
                
            except Exception as e:
                print(f"  Fold {fold}: 预测失败: {e}")
            
            test_start += self.config.step_size
        
        # 计算整体指标
        if len(predictions) == 0:
            print("✗ 没有成功的预测结果")
            return {}
        
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # 计算指标
        rmse = np.sqrt(mean_squared_error(actuals, predictions))
        mae = mean_absolute_error(actuals, predictions)
        r2 = r2_score(actuals, predictions)
        
        # 方向准确率
        if len(predictions) > 1:
            pred_direction = np.sign(predictions[1:] - predictions[:-1])
            actual_direction = np.sign(actuals[1:] - actuals[:-1])
            directional_accuracy = np.mean(pred_direction == actual_direction)
        else:
            directional_accuracy = 0.0
        
        print(f"\n✓ 滚动窗口回测完成")
        print(f"  总预测数: {len(predictions)}")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  MAE: {mae:.2f}")
        print(f"  R²: {r2:.4f}")
        print(f"  方向准确率: {directional_accuracy*100:.2f}%")
        
        return {
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'directional_accuracy': directional_accuracy,
            'predictions': predictions,
            'actuals': actuals,
            'indices': indices,
            'total_folds': fold,
            'config': self.config
        }
    
    def _fallback_predict(self, test_X, train_y):
        """备用预测逻辑（简单的移动平均）"""
        last_price = train_y.iloc[-1]
        return np.full(len(test_X), last_price)
    
    def analyze_market_regimes(self, data: pd.DataFrame,
                                results: Dict) -> Dict:
        """
        分析不同市场环境下的表现差异
        
        Args:
            data: 价格数据
            results: 滚动窗口回测结果
            
        Returns:
            不同市场环境下的表现
        """
        print("\n" + "="*60)
        print("📈 市场环境分析")
        print("="*60)
        
        if 'indices' not in results or len(results['indices']) == 0:
            print("✗ 没有预测数据，无法分析")
            return {}
        
        # 将预测结果转换为DataFrame
        pred_df = pd.DataFrame({
            'predicted': results['predictions'],
            'actual': results['actuals']
        }, index=results['indices'])
        
        # 合并价格数据
        merged = pred_df.join(data[['close']], how='left')
        
        # 计算收益率（判断趋势）
        merged['returns_20d'] = merged['actual'].pct_change(20)
        
        # 定义市场环境
        trend_threshold = 0.10  # 20日涨跌幅超过10%定义为趋势市
        
        merged['market_regime'] = np.where(
            merged['returns_20d'].abs() > trend_threshold,
            'trending',
            'sideways'
        )
        
        # 趋势方向
        merged['trend_direction'] = np.where(
            merged['returns_20d'] > trend_threshold,
            'up',
            np.where(merged['returns_20d'] < -trend_threshold, 'down', 'flat')
        )
        
        # 计算各环境下的指标
        regimes = ['trending', 'sideways']
        regime_metrics = {}
        
        for regime in regimes:
            regime_data = merged[merged['market_regime'] == regime]
            
            if len(regime_data) > 0:
                rmse = np.sqrt(mean_squared_error(
                    regime_data['actual'],
                    regime_data['predicted']
                ))
                mae = mean_absolute_error(
                    regime_data['actual'],
                    regime_data['predicted']
                )
                
                # 方向准确率
                if len(regime_data) > 1:
                    pred_dir = np.sign(regime_data['predicted'].values[1:] - 
                                     regime_data['predicted'].values[:-1])
                    actual_dir = np.sign(regime_data['actual'].values[1:] - 
                                        regime_data['actual'].values[:-1])
                    dir_acc = np.mean(pred_dir == actual_dir)
                else:
                    dir_acc = 0.0
                
                regime_metrics[regime] = {
                    'count': len(regime_data),
                    'rmse': rmse,
                    'mae': mae,
                    'directional_accuracy': dir_acc
                }
                
                print(f"\n{regime.upper()}市场 ({len(regime_data)}个样本):")
                print(f"  RMSE: {rmse:.2f}")
                print(f"  MAE: {mae:.2f}")
                print(f"  方向准确率: {dir_acc*100:.2f}%")
        
        return {
            'regime_metrics': regime_metrics,
            'predictions_with_regime': merged
        }


class StressTester:
    """压力测试器"""
    
    def __init__(self, config: StressTestConfig = None):
        self.config = config or StressTestConfig()
    
    def test_china_demand_shock(self, model, base_data: pd.DataFrame,
                                base_pred: float) -> Dict:
        """
        测试中国需求断崖情景
        
        Args:
            model: 预测模型
            base_data: 基础数据
            base_pred: 基础预测值
            
        Returns:
            压力测试结果
        """
        print("\n" + "="*60)
        print("⚠️ 压力测试: 中国需求断崖")
        print("="*60)
        print(f"情景: 地产新开工下降{self.config.china_demand_drop*100:.0f}%")
        
        # 模拟需求下降对价格的影响
        # 铜价对需求的弹性约为0.6-0.8
        demand_elasticity = 0.7
        price_impact = self.config.china_demand_drop * demand_elasticity
        
        shocked_price = base_pred * (1 + price_impact)
        price_change_pct = price_impact * 100
        
        print(f"  基础预测价格: ¥{base_pred:,.2f}")
        print(f"  需求弹性系数: {demand_elasticity}")
        print(f"  价格冲击: {price_change_pct:+.2f}%")
        print(f"  冲击后价格: ¥{shocked_price:,.2f}")
        
        # 评估风险等级
        if abs(price_change_pct) > 20:
            risk_level = "极高风险"
        elif abs(price_change_pct) > 10:
            risk_level = "高风险"
        elif abs(price_change_pct) > 5:
            risk_level = "中风险"
        else:
            risk_level = "低风险"
        
        print(f"  风险等级: {risk_level}")
        
        return {
            'scenario': 'china_demand_shock',
            'demand_drop_pct': self.config.china_demand_drop * 100,
            'demand_elasticity': demand_elasticity,
            'base_price': base_pred,
            'shocked_price': shocked_price,
            'price_change_pct': price_change_pct,
            'risk_level': risk_level
        }
    
    def test_usd_liquidity_crisis(self, model, base_data: pd.DataFrame,
                                   base_pred: float) -> Dict:
        """
        测试美元流动性危机情景
        
        Args:
            model: 预测模型
            base_data: 基础数据
            base_pred: 基础预测值
            
        Returns:
            压力测试结果
        """
        print("\n" + "="*60)
        print("⚠️ 压力测试: 美元流动性危机")
        print("="*60)
        
        # 根据场景设置参数
        if self.config.usd_spike_scenario == '2020-03':
            # 2020年3月: 美元指数上涨8%, 铜价下跌30%
            usd_spike_pct = 0.08
            copper_drop_pct = -0.30
            reference = "2020年3月新冠疫情恐慌"
        elif self.config.usd_spike_scenario == '2022-09':
            # 2022年9月: 美元指数上涨5%, 铜价下跌20%
            usd_spike_pct = 0.05
            copper_drop_pct = -0.20
            reference = "2022年9月激进加息"
        else:
            # 默认使用2020年3月
            usd_spike_pct = 0.08
            copper_drop_pct = -0.30
            reference = "2020年3月新冠疫情恐慌"
        
        # 美元与铜价的负相关系数
        usd_copper_correlation = -0.7
        
        # 计算冲击
        usd_impact = usd_copper_correlation * usd_spike_pct
        total_impact = max(usd_impact, copper_drop_pct)  # 取更坏的情况
        
        shocked_price = base_pred * (1 + total_impact)
        price_change_pct = total_impact * 100
        
        print(f"  参考情景: {reference}")
        print(f"  美元指数飙升: +{usd_spike_pct*100:.1f}%")
        print(f"  美元-铜价相关系数: {usd_copper_correlation}")
        print(f"  基础预测价格: ¥{base_pred:,.2f}")
        print(f"  价格冲击: {price_change_pct:+.2f}%")
        print(f"  冲击后价格: ¥{shocked_price:,.2f}")
        
        # 评估风险等级
        if abs(price_change_pct) > 20:
            risk_level = "极高风险"
        elif abs(price_change_pct) > 10:
            risk_level = "高风险"
        elif abs(price_change_pct) > 5:
            risk_level = "中风险"
        else:
            risk_level = "低风险"
        
        print(f"  风险等级: {risk_level}")
        
        return {
            'scenario': 'usd_liquidity_crisis',
            'reference': reference,
            'usd_spike_pct': usd_spike_pct * 100,
            'usd_copper_correlation': usd_copper_correlation,
            'base_price': base_pred,
            'shocked_price': shocked_price,
            'price_change_pct': price_change_pct,
            'risk_level': risk_level
        }
    
    def test_supply_shock(self, model, base_data: pd.DataFrame,
                         base_pred: float) -> Dict:
        """
        测试供应端黑天鹅情景
        
        Args:
            model: 预测模型
            base_data: 基础数据
            base_pred: 基础预测值
            
        Returns:
            压力测试结果
        """
        print("\n" + "="*60)
        print("⚠️ 压力测试: 供应端黑天鹅")
        print("="*60)
        
        results = []
        
        for shock_type in self.config.supply_shock_types:
            if shock_type == 'chile_earthquake':
                # 智利地震: 全球铜供应下降5-10%
                name = "智利地震"
                supply_drop_pct = -0.07
                # 供应下降导致价格上涨
                supply_elasticity = 2.0  # 供应弹性大于需求弹性
            elif shock_type == 'panama_drought':
                # 巴拿马运河干旱: 影响约15%的铜运输
                name = "巴拿马运河干旱"
                supply_drop_pct = -0.03  # 对全球供应的影响较小
                supply_elasticity = 1.5
            else:
                continue
            
            price_impact = abs(supply_drop_pct) * supply_elasticity
            shocked_price = base_pred * (1 + price_impact)
            price_change_pct = price_impact * 100
            
            print(f"\n  {name}:")
            print(f"    供应影响: {supply_drop_pct*100:.1f}%")
            print(f"    供应弹性: {supply_elasticity}")
            print(f"    价格冲击: +{price_change_pct:.2f}%")
            print(f"    冲击后价格: ¥{shocked_price:,.2f}")
            
            results.append({
                'shock_type': shock_type,
                'name': name,
                'supply_drop_pct': supply_drop_pct * 100,
                'supply_elasticity': supply_elasticity,
                'base_price': base_pred,
                'shocked_price': shocked_price,
                'price_change_pct': price_change_pct
            })
        
        # 取最严重的情景
        worst_scenario = max(results, key=lambda x: x['price_change_pct'])
        
        return {
            'scenario': 'supply_shock',
            'all_scenarios': results,
            'worst_scenario': worst_scenario
        }
    
    def run_all_stress_tests(self, model, base_data: pd.DataFrame,
                            base_pred: float) -> Dict:
        """
        运行所有压力测试
        
        Args:
            model: 预测模型
            base_data: 基础数据
            base_pred: 基础预测值
            
        Returns:
            所有压力测试结果
        """
        print("\n" + "="*60)
        print("🚨 运行全面压力测试")
        print("="*60)
        
        results = {}
        
        # 1. 中国需求断崖
        results['china_demand'] = self.test_china_demand_shock(
            model, base_data, base_pred
        )
        
        # 2. 美元流动性危机
        results['usd_liquidity'] = self.test_usd_liquidity_crisis(
            model, base_data, base_pred
        )
        
        # 3. 供应端黑天鹅
        results['supply_shock'] = self.test_supply_shock(
            model, base_data, base_pred
        )
        
        # 汇总最坏情况
        worst_shock = min(
            results['china_demand']['price_change_pct'],
            results['usd_liquidity']['price_change_pct'],
            results['supply_shock']['worst_scenario']['price_change_pct']
        )
        
        worst_price = base_pred * (1 + worst_shock / 100)
        
        print("\n" + "="*60)
        print("📊 压力测试汇总")
        print("="*60)
        print(f"  基础预测: ¥{base_pred:,.2f}")
        print(f"  最坏情景: ¥{worst_price:,.2f} ({worst_shock:+.2f}%)")
        print(f"  最大潜在损失: {abs(worst_shock):.2f}%")
        
        return {
            'all_results': results,
            'worst_case': {
                'price': worst_price,
                'change_pct': worst_shock,
                'scenario': '综合最坏情景'
            }
        }


class ConfidenceAnalyzer:
    """模型置信度分析器"""
    
    def __init__(self, config: RiskMetricsConfig = None):
        self.config = config or RiskMetricsConfig()
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                          returns: np.ndarray = None) -> Dict:
        """
        计算置信度指标
        
        Args:
            y_true: 真实值
            y_pred: 预测值
            returns: 收益率序列（可选）
            
        Returns:
            置信度指标字典
        """
        print("="*60)
        print("📊 模型置信度分析")
        print("="*60)
        
        metrics = {}
        
        # 1. R²（解释力）
        r2 = r2_score(y_true, y_pred)
        metrics['r2'] = r2
        print(f"  R² (解释力): {r2:.4f}")
        
        if r2 > 0.6:
            print(f"    → 解释力较强")
        elif r2 > 0.3:
            print(f"    → 解释力一般")
        else:
            print(f"    → 解释力较弱")
        
        # 2. 方向准确率（关键指标）
        if len(y_pred) > 1:
            pred_direction = np.sign(y_pred[1:] - y_pred[:-1])
            actual_direction = np.sign(y_true[1:] - y_true[:-1])
            directional_accuracy = np.mean(pred_direction == actual_direction)
            metrics['directional_accuracy'] = directional_accuracy
            print(f"  方向准确率: {directional_accuracy*100:.2f}%")
            
            if directional_accuracy >= self.config.directional_accuracy_threshold:
                print(f"    → 优秀 (≥{self.config.directional_accuracy_threshold*100:.0f}%)")
            elif directional_accuracy >= 0.55:
                print(f"    → 良好 (≥55%)")
            else:
                print(f"    → 需改进 (<55%)")
        else:
            metrics['directional_accuracy'] = 0.0
            print(f"  方向准确率: N/A (样本不足)")
        
        # 3. RMSE（预测精度）
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        
        # 归一化RMSE（相对于均值）
        mean_y = np.mean(y_true)
        nrmse = rmse / mean_y if mean_y != 0 else 0
        metrics['rmse'] = rmse
        metrics['mae'] = mae
        metrics['nrmse'] = nrmse
        print(f"  RMSE: {rmse:.2f} (归一化: {nrmse*100:.2f}%)")
        print(f"  MAE: {mae:.2f}")
        
        # 4. 最大误差
        max_error = np.max(np.abs(y_true - y_pred))
        max_error_pct = max_error / mean_y * 100 if mean_y != 0 else 0
        metrics['max_error'] = max_error
        metrics['max_error_pct'] = max_error_pct
        print(f"  最大误差: {max_error:.2f} ({max_error_pct:.2f}%)")
        
        # 5. 预测误差分布
        errors = y_pred - y_true
        error_std = np.std(errors)
        metrics['error_std'] = error_std
        print(f"  误差标准差: {error_std:.2f}")
        
        # 6. 综合置信度评分
        confidence_score = self._calculate_confidence_score(metrics)
        metrics['confidence_score'] = confidence_score
        print(f"\n  综合置信度评分: {confidence_score:.2f}/100")
        
        if confidence_score >= 80:
            print(f"    → 置信度: 高")
        elif confidence_score >= 60:
            print(f"    → 置信度: 中")
        else:
            print(f"    → 置信度: 低")
        
        return metrics
    
    def _calculate_confidence_score(self, metrics: Dict) -> float:
        """
        计算综合置信度评分
        
        Args:
            metrics: 指标字典
            
        Returns:
            置信度评分 (0-100)
        """
        score = 0.0
        
        # R²权重30%
        r2 = metrics.get('r2', 0)
        score += max(0, r2) * 30
        
        # 方向准确率权重40%（最重要）
        dir_acc = metrics.get('directional_accuracy', 0)
        score += dir_acc * 40
        
        # 归一化RMSE权重20%（越小越好）
        nrmse = metrics.get('nrmse', 1)
        score += max(0, 1 - nrmse) * 20
        
        # 误差稳定性权重10%
        error_std = metrics.get('error_std', float('inf'))
        mean_y = np.mean(metrics.get('actuals', [100000]))
        cv = error_std / mean_y if mean_y != 0 else 1
        score += max(0, 1 - cv) * 10
        
        return min(100, score)


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: RiskMetricsConfig = None):
        self.config = config or RiskMetricsConfig()
    
    def calculate_position_size(self, account_value: float,
                                confidence_score: float,
                                volatility: float) -> float:
        """
        计算建议仓位大小（基于凯利公式改进版）
        
        Args:
            account_value: 账户价值
            confidence_score: 置信度评分 (0-100)
            volatility: 波动率
            
        Returns:
            建议仓位大小
        """
        # 基础仓位比例
        base_position = 0.02  # 基础2%
        
        # 根据置信度调整
        confidence_factor = confidence_score / 100.0
        
        # 根据波动率调整（波动越大，仓位越小）
        vol_adjustment = min(1.0, 0.05 / volatility) if volatility > 0 else 1.0
        
        # 最终仓位比例
        position_ratio = base_position * confidence_factor * vol_adjustment
        
        # 限制最大仓位
        position_ratio = min(0.10, position_ratio)  # 最多10%
        
        return account_value * position_ratio
    
    def calculate_stop_loss(self, entry_price: float,
                           volatility: float = None) -> Tuple[float, float]:
        """
        计算止损和止盈价格
        
        Args:
            entry_price: 入场价格
            volatility: 波动率（可选）
            
        Returns:
            (止损价格, 止盈价格)
        """
        # 使用固定止损止盈比例
        stop_loss_price = entry_price * (1 - self.config.stop_loss_pct)
        take_profit_price = entry_price * (1 + self.config.take_profit_pct)
        
        # 如果提供了波动率，可以动态调整
        if volatility and volatility > 0:
            # 波动越大，止损越宽
            vol_adjustment = min(2.0, volatility * 100)
            adjusted_stop_loss = self.config.stop_loss_pct * vol_adjustment
            stop_loss_price = entry_price * (1 - adjusted_stop_loss)
        
        return stop_loss_price, take_profit_price
    
    def check_risk_limit(self, current_price: float, entry_price: float,
                        stop_loss_price: float) -> Dict:
        """
        检查是否触发风险限制
        
        Args:
            current_price: 当前价格
            entry_price: 入场价格
            stop_loss_price: 止损价格
            
        Returns:
            风险状态字典
        """
        pnl_pct = (current_price - entry_price) / entry_price * 100
        
        # 判断是否触发止损
        stop_loss_triggered = current_price <= stop_loss_price
        
        # 判断是否达到止盈
        take_profit_price = entry_price * (1 + self.config.take_profit_pct)
        take_profit_reached = current_price >= take_profit_price
        
        # 最大回撤检查
        if current_price < entry_price:
            drawdown_pct = (current_price - entry_price) / entry_price * 100
        else:
            drawdown_pct = 0
        
        return {
            'pnl_pct': pnl_pct,
            'drawdown_pct': drawdown_pct,
            'stop_loss_triggered': stop_loss_triggered,
            'take_profit_reached': take_profit_reached,
            'action': '止损' if stop_loss_triggered else 
                     '止盈' if take_profit_reached else '持有'
        }
    
    def generate_risk_report(self, model_metrics: Dict,
                            stress_test_results: Dict) -> str:
        """
        生成风险报告
        
        Args:
            model_metrics: 模型性能指标
            stress_test_results: 压力测试结果
            
        Returns:
            风险报告文本
        """
        report = f"""
{'='*60}
🚨 风险管理报告
{'='*60}

【模型置信度】
"""
        # 模型置信度
        if 'r2' in model_metrics:
            report += f"  R² (解释力): {model_metrics['r2']:.4f}\n"
            if model_metrics['r2'] > 0.6:
                report += "    ⚠️ 注意: R² > 0.6 仅说明解释力强,不保证预测力\n"
        
        if 'directional_accuracy' in model_metrics:
            report += f"  方向准确率: {model_metrics['directional_accuracy']*100:.2f}%\n"
            if model_metrics['directional_accuracy'] >= 0.65:
                report += "    ✓ 优秀: 方向准确率达到优秀标准(≥65%)\n"
            elif model_metrics['directional_accuracy'] >= 0.55:
                report += "    ⚠️ 良好: 方向准确率尚可,但仍有提升空间\n"
            else:
                report += "    ✗ 较差: 方向准确率低于55%,建议优化模型\n"
        
        # 压力测试结果
        report += f"\n【压力测试】\n"
        if 'worst_case' in stress_test_results:
            worst = stress_test_results['worst_case']
            report += f"  最坏情景: {worst['scenario']}\n"
            report += f"  潜在最大损失: {abs(worst['change_pct']):.2f}%\n"
            
            if abs(worst['change_pct']) > 20:
                report += "    🚨 极高风险: 必须严格控制仓位\n"
            elif abs(worst['change_pct']) > 10:
                report += "    ⚠️ 高风险: 建议降低仓位\n"
            else:
                report += "    ✓ 风险可控\n"
        
        # 止损建议
        report += f"\n【风险管理建议】\n"
        report += f"  1. 单日最大止损: {self.config.stop_loss_pct*100:.1f}%\n"
        report += f"     (铜价单日波动可达5%,必须设置止损)\n"
        report += f"  2. 目标止盈: {self.config.take_profit_pct*100:.1f}%\n"
        report += f"  3. 建议最大仓位: 10% (根据模型置信度调整)\n"
        report += f"  4. 分批建仓,分散风险\n"
        
        report += f"\n{'='*60}"
        return report


# 统一的风险验证接口
class ModelValidator:
    """模型验证器（统一接口）"""
    
    def __init__(self, walk_forward_config: WalkForwardConfig = None,
                 stress_test_config: StressTestConfig = None,
                 risk_metrics_config: RiskMetricsConfig = None):
        self.walk_forward = WalkForwardAnalyzer(walk_forward_config)
        self.stress_tester = StressTester(stress_test_config)
        self.confidence_analyzer = ConfidenceAnalyzer(risk_metrics_config)
        self.risk_manager = RiskManager(risk_metrics_config)
    
    def validate(self, model, data: pd.DataFrame, features: pd.DataFrame,
                target_col: str = 'close', base_prediction: float = None) -> Dict:
        """
        完整的模型验证流程
        
        Args:
            model: 预测模型
            data: 价格数据
            features: 特征数据
            target_col: 目标列名
            base_prediction: 基础预测值（用于压力测试）
            
        Returns:
            验证结果字典
        """
        print("="*60)
        print("🔍 模型验证与风险管理")
        print("="*60)
        
        results = {}
        
        # 1. 滚动窗口回测
        print("\n【1. 样本外测试】")
        walk_forward_results = self.walk_forward.run(model, data, features, target_col)
        results['walk_forward'] = walk_forward_results
        
        # 2. 市场环境分析
        if walk_forward_results:
            print("\n【2. 市场环境分析】")
            regime_analysis = self.walk_forward.analyze_market_regimes(
                data, walk_forward_results
            )
            results['regime_analysis'] = regime_analysis
        
        # 3. 压力测试
        if base_prediction:
            print("\n【3. 压力测试】")
            stress_results = self.stress_tester.run_all_stress_tests(
                model, data, base_prediction
            )
            results['stress_test'] = stress_results
        
        # 4. 置信度分析
        if walk_forward_results and 'predictions' in walk_forward_results:
            print("\n【4. 模型置信度】")
            confidence_metrics = self.confidence_analyzer.calculate_metrics(
                walk_forward_results['actuals'],
                walk_forward_results['predictions']
            )
            results['confidence'] = confidence_metrics
        
        # 5. 风险报告
        print("\n【5. 风险管理】")
        risk_report = self.risk_manager.generate_risk_report(
            confidence_metrics if 'confidence' in results else {},
            stress_results if 'stress_test' in results else {}
        )
        print(risk_report)
        results['risk_report'] = risk_report
        
        return results


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("模型验证与风险管理模块测试")
    print("="*60)
    
    # 生成测试数据
    from data.data_sources import MockDataSource
    from models.copper_model_v2 import FeatureEngineer, XGBoostModel
    
    mock_source = MockDataSource()
    data = mock_source.fetch_copper_price(
        start_date="2023-01-01",
        end_date="2024-12-31"
    )
    
    print(f"\n测试数据: {len(data)} 条记录")
    
    # 创建特征
    feature_engineer = FeatureEngineer()
    features = feature_engineer.create_features(data)
    
    print(f"特征数量: {len(features.columns)}")
    
    # 简单的测试模型
    class SimpleModel:
        def fit(self, X, y):
            pass
        
        def predict(self, X):
            return X['close'].values if 'close' in X.columns else np.full(len(X), 100000)
    
    model = SimpleModel()
    
    # 运行验证
    validator = ModelValidator()
    results = validator.validate(model, data, features, base_prediction=100000)
    
    print("\n" + "="*60)
    print("✓ 验证完成!")
    print("="*60)
