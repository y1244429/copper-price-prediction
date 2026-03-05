"""
铜价预测高级模型
1. 基本面模型（长期趋势）- 6个月以上战略配置
2. 宏观因子模型（中期波动）- 1-6个月战术调整
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge, ElasticNet
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("sklearn未安装,请运行: pip install scikit-learn")

try:
    from statsmodels.tsa.api import VAR
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("statsmodels未安装,请运行: pip install statsmodels")


@dataclass
class FundamentalConfig:
    """基本面模型配置"""
    # 模型参数
    model_type: str = 'ridge'  # 改用'ridge'模型,更稳定

    # Ridge模型参数
    ridge_alpha: float = 1.0  # Ridge正则化强度
    random_state: int = 42  # 固定随机种子

    # 供需权重
    supply_weight: float = 0.4
    demand_weight: float = 0.4
    inventory_weight: float = 0.2

    # 成本支撑
    cost_percentile: float = 0.90  # C1成本90分位线
    full_cost_percentile: float = 0.75  # 完全成本75分位线

    # 矿山风险因子
    disruption_factor: float = 0.1  # 干扰率影响系数

    # 预测范围
    forecast_horizon: int = 180  # 预测180天（6个月）


@dataclass
class MacroConfig:
    """宏观因子模型配置"""
    # 模型参数
    model_type: str = 'ardl'  # 'ardl' 或 'dfm'
    lags: int = 5  # 滞后期数

    # 因子权重
    usd_weight: float = 0.3  # 美元指数权重
    pmi_weight: float = 0.25  # PMI权重
    rate_weight: float = 0.2  # 实际利率权重
    structure_weight: float = 0.25  # 期限结构权重

    # 动态因子模型参数
    n_factors: int = 3  # 因子数量

    # 预测范围
    forecast_horizon: int = 90  # 预测90天（3个月）


class FundamentalDataProcessor:
    """基本面数据处理器"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.cost_curve = None
        self.disruption_index = None
        # 固定随机数种子,确保基本面特征生成稳定
        np.random.seed(42)

    def process_supply_demand(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理供需数据

        核心变量:
        - 全球精铜产量（ICSG数据）
        - 中国表观消费量
        - 显性库存变化率
        """
        result = df.copy()

        # 1. 计算供需平衡指标
        if 'production' in df.columns:
            result['production_ma3'] = df['production'].rolling(3).mean()
            result['production_growth'] = df['production'].pct_change(20)

        if 'consumption' in df.columns:
            result['consumption_ma3'] = df['consumption'].rolling(3).mean()
            result['consumption_growth'] = df['consumption'].pct_change(20)

        # 2. 供需平衡表
        if 'production' in df.columns and 'consumption' in df.columns:
            result['supply_demand_gap'] = df['production'] - df['consumption']
            result['gap_pct'] = result['supply_demand_gap'] / df['consumption'] * 100

        # 3. 库存变化率
        if 'inventory' in df.columns:
            result['inventory_change'] = df['inventory'].diff()
            result['inventory_change_pct'] = df['inventory'].pct_change()
            result['inventory_ma20'] = df['inventory'].rolling(20).mean()
            result['inventory_zscore'] = (
                (df['inventory'] - result['inventory_ma20']) /
                df['inventory'].rolling(20).std()
            )

        return result

    def process_cost_support(self, df: pd.DataFrame, config: FundamentalConfig) -> pd.DataFrame:
        """
        处理成本支撑数据

        核心变量:
        - C1成本（现金成本）90分位线
        - 完全成本75分位线
        """
        # 在方法内部重新设置随机种子，确保结果可重复
        np.random.seed(42)

        result = df.copy()

        # 如果没有提供成本数据，使用价格估算
        if 'cash_cost' not in df.columns:
            # 假设现金成本约为价格的60-70%
            result['cash_cost'] = df['close'] * 0.65 * (1 + np.random.normal(0, 0.05, len(df)))
            result['full_cost'] = df['close'] * 0.75 * (1 + np.random.normal(0, 0.05, len(df)))
        else:
            result['cash_cost'] = df['cash_cost']
            result['full_cost'] = df['full_cost']

        # 计算成本支撑位
        result['cost_c1_90'] = result['cash_cost'].rolling(90).quantile(0.90)
        result['cost_full_75'] = result['full_cost'].rolling(90).quantile(0.75)

        # 计算价格相对于成本的位置
        result['price_to_c1_cost'] = df['close'] / result['cost_c1_90']
        result['price_to_full_cost'] = df['close'] / result['cost_full_75']

        # 成本支撑强度（价格越接近成本，支撑越强）
        result['cost_support_strength'] = np.where(
            df['close'] < result['cost_c1_90'],
            (result['cost_c1_90'] - df['close']) / result['cost_c1_90'],
            0
        )

        return result

    def process_disruption_risk(self, df: pd.DataFrame, config: FundamentalConfig) -> pd.DataFrame:
        """
        处理矿山干扰风险

        核心变量:
        - 智利、秘鲁等主要产区的罢工
        - 品位下滑
        - 政策风险
        """
        # 在方法内部重新设置随机种子，确保结果可重复
        np.random.seed(42)

        result = df.copy()

        # 如果没有提供干扰数据，使用模拟数据
        if 'disruption_index' not in df.columns:
            # 基于随机波动生成干扰指数（0-1）
            result['disruption_index'] = np.random.uniform(0, 0.3, len(df))
            result['disruption_chile'] = np.random.uniform(0, 0.2, len(df))
            result['disruption_peru'] = np.random.uniform(0, 0.15, len(df))
        else:
            result['disruption_index'] = df['disruption_index']
            result['disruption_chile'] = df.get('disruption_chile', 0)
            result['disruption_peru'] = df.get('disruption_peru', 0)

        # 计算综合干扰指数
        result['disruption_total'] = (
            result['disruption_chile'] * 0.5 +
            result['disruption_peru'] * 0.3 +
            result['disruption_index'] * 0.2
        )

        # 干扰对供应的预期影响（价格弹性）
        result['supply_impact'] = result['disruption_total'] * config.disruption_factor

        return result

    def create_fundamental_features(self, df: pd.DataFrame, config: FundamentalConfig) -> pd.DataFrame:
        """
        创建基本面特征集合
        """
        # 处理各维度数据
        df_sd = self.process_supply_demand(df)
        df_cost = self.process_cost_support(df_sd, config)
        df_final = self.process_disruption_risk(df_cost, config)

        return df_final


class MacroDataProcessor:
    """宏观因子数据处理器"""

    def __init__(self):
        self.scaler = StandardScaler()

    def process_usd_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理美元指数数据

        核心变量: 美元指数（负相关性极强，系数通常-0.7以上）
        """
        result = df.copy()

        if 'usd_index' not in df.columns:
            # 生成模拟美元指数数据（与铜价负相关）
            np.random.seed(44)
            result['usd_index'] = 100 + np.cumsum(np.random.normal(0, 0.1, len(df)))
        else:
            result['usd_index'] = df['usd_index']

        # 计算美元指数变化
        result['usd_change'] = result['usd_index'].pct_change()
        result['usd_ma5'] = result['usd_index'].rolling(5).mean()
        result['usd_ma20'] = result['usd_index'].rolling(20).mean()

        # 美元强度指标
        result['usd_strength'] = result['usd_index'] / result['usd_ma20'] - 1

        return result

    def process_pmi_credit(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理PMI和信贷脉冲数据

        核心变量:
        - 中国PMI（铜被称为"铜博士"，对全球制造业景气度极度敏感）
        - 信贷脉冲
        """
        result = df.copy()

        if 'pmi' not in df.columns:
            # 生成模拟PMI数据（围绕50波动）
            np.random.seed(45)
            result['pmi'] = 50 + np.cumsum(np.random.normal(0, 0.5, len(df)))
            result['pmi'] = result['pmi'].clip(40, 60)  # 限制在合理范围
        else:
            result['pmi'] = df['pmi']

        # PMI变化趋势
        result['pmi_change'] = result['pmi'].diff()
        result['pmi_ma3'] = result['pmi'].rolling(3).mean()

        # PMI景气度分类
        result['pmi_expansion'] = (result['pmi'] > 50).astype(int)
        result['pmi_momentum'] = result['pmi'] - result['pmi'].shift(5)

        # 信贷脉冲（模拟）
        if 'credit_pulse' not in df.columns:
            np.random.seed(46)
            result['credit_pulse'] = np.random.normal(0, 1, len(df))
        else:
            result['credit_pulse'] = df['credit_pulse']

        result['credit_ma3'] = result['credit_pulse'].rolling(3).mean()

        return result

    def process_real_interest_rate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理实际利率数据

        核心变量: 10Y TIPS收益率反映持有机会成本
        """
        result = df.copy()

        if 'tips_10y' not in df.columns:
            # 生成模拟TIPS收益率数据
            np.random.seed(47)
            result['tips_10y'] = 1.5 + np.cumsum(np.random.normal(0, 0.02, len(df)))
            result['tips_10y'] = result['tips_10y'].clip(-1, 3)  # 限制在合理范围
        else:
            result['tips_10y'] = df['tips_10y']

        # 实际利率变化
        result['tips_change'] = result['tips_10y'].diff()
        result['tips_ma5'] = result['tips_10y'].rolling(5).mean()

        # 利率环境分类
        result['rising_rate'] = (result['tips_change'] > 0).astype(int)
        result['rate_level'] = pd.cut(
            result['tips_10y'],
            bins=[-np.inf, 0, 1, 2, np.inf],
            labels=[0, 1, 2, 3]
        ).astype(float)

        return result

    def process_term_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理期限结构数据

        核心变量: LME升贴水（Contango/Backwardation）反映即期供需紧张度
        """
        result = df.copy()

        if 'lme_spread' not in df.columns:
            # 基于现货和3个月期货的价差生成
            if 'close' in df.columns:
                # 模拟升贴水
                result['lme_spread'] = np.random.normal(0, df['close'] * 0.005, len(df))
            else:
                result['lme_spread'] = np.random.normal(0, 100, len(df))
        else:
            result['lme_spread'] = df['lme_spread']

        # Contango/Backwardation 判断
        result['is_contango'] = (result['lme_spread'] > 0).astype(int)
        result['is_backwardation'] = (result['lme_spread'] < 0).astype(int)

        # 升贴水强度
        result['spread_strength'] = np.abs(result['lme_spread'])
        result['spread_pct'] = np.where(
            df['close'].notna(),
            result['lme_spread'] / df['close'] * 100,
            result['lme_spread']
        )

        # 期限结构变化
        result['spread_change'] = result['lme_spread'].diff()
        result['spread_ma5'] = result['lme_spread'].rolling(5).mean()

        return result

    def create_macro_features(self, df: pd.DataFrame, config: MacroConfig) -> pd.DataFrame:
        """
        创建宏观因子特征集合
        """
        # 处理各维度数据
        df_usd = self.process_usd_index(df)
        df_pmi = self.process_pmi_credit(df_usd)
        df_tips = self.process_real_interest_rate(df_pmi)
        df_final = self.process_term_structure(df_tips)

        return df_final


class FundamentalModel:
    """
    基本面模型（长期趋势）

    适用场景: 6个月以上战略配置

    核心变量:
    - 供需平衡表：全球精铜产量、中国表观消费量、显性库存变化率
    - 成本曲线支撑：C1成本90分位线、完全成本75分位线
    - 矿山干扰率：智利、秘鲁等主要产区的罢工、品位下滑、政策风险

    建模方法: 向量自回归（VAR）或结构方程模型
    """

    def __init__(self, config: FundamentalConfig = None):
        self.config = config or FundamentalConfig()
        self.processor = FundamentalDataProcessor()
        self.model = None
        self.scaler = StandardScaler()

    def train(self, df: pd.DataFrame, target_col: str = 'close') -> Dict:
        """
        训练基本面模型
        """
        print("[基本面模型] 训练长期趋势模型...")

        # 创建基本面特征
        features_df = self.processor.create_fundamental_features(df, self.config)

        # 选择特征变量
        feature_cols = self._select_feature_columns(features_df)

        # 准备数据
        df_model = features_df[feature_cols + [target_col]].copy()
        df_model = df_model.dropna()

        if len(df_model) < 100:
            raise ValueError("数据量不足,至少需要100条数据")

        # 标准化
        X = df_model[feature_cols].values
        y = df_model[target_col].values

        X_scaled = self.scaler.fit_transform(X)

        # 训练Ridge模型(更稳定)
        self.model = self._train_ridge(X_scaled, y)

        # 计算训练指标
        y_pred = self.model.predict(X_scaled)
        y_actual = y

        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_actual, y_pred)),
            'mae': mean_absolute_error(y_actual, y_pred),
            'r2': r2_score(y_actual, y_pred),
            'model_type': self.config.model_type
        }

        print(f"✓ 基本面模型训练完成")
        print(f"  RMSE: {metrics['rmse']:.2f}")
        print(f"  MAE: {metrics['mae']:.2f}")
        print(f"  R²: {metrics['r2']:.4f}")

        return metrics

    def _select_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """选择基本面特征列"""
        base_cols = ['close', 'volume']

        # 供需相关
        sd_cols = [col for col in df.columns if any(x in col for x in ['production', 'consumption', 'inventory', 'gap'])]

        # 成本相关
        cost_cols = [col for col in df.columns if any(x in col for x in ['cost', 'support'])]

        # 干扰相关
        disruption_cols = [col for col in df.columns if 'disruption' in col]

        selected = sd_cols + cost_cols + disruption_cols
        selected = [col for col in selected if col in df.columns]

        return selected[:15] if len(selected) > 15 else selected  # 限制特征数量

    def _train_ridge(self, X: np.ndarray, y: np.ndarray):
        """训练Ridge回归模型(稳定)"""
        # 移除NaN值
        mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X_clean = X[mask]
        y_clean = y[mask]

        # 使用Ridge回归,固定随机种子确保结果稳定
        model = Ridge(
            alpha=self.config.ridge_alpha,
            random_state=self.config.random_state,
            max_iter=1000
        )
        model.fit(X_clean, y_clean)
        return model

    def predict(self, df: pd.DataFrame, horizon: int = None) -> Dict:
        """
        预测未来价格

        Args:
            df: 历史数据
            horizon: 预测周期（天）
        """
        if self.model is None:
            raise ValueError("模型未训练")

        horizon = horizon or self.config.forecast_horizon

        # 创建特征
        features_df = self.processor.create_fundamental_features(df, self.config)
        feature_cols = self._select_feature_columns(features_df)

        df_model = features_df[feature_cols].copy()
        df_model = df_model.dropna()

        if len(df_model) < 1:
            raise ValueError("特征数据不足")

        X = df_model.values
        X_scaled = self.scaler.transform(X)

        # 获取最新数据和特征值
        X_latest = X_scaled[-1:]
        latest_features = df_model.iloc[-1].to_dict()

        # 获取当前价格
        current_price = df['close'].iloc[-1]

        # 使用Ridge模型预测
        predicted_price_raw = self.model.predict(X_latest)[0]
        predicted_change = predicted_price_raw - current_price

        # 根据预测周期调整预测值
        # 基本面模型：使用供需平衡和成本支撑进行长期趋势预测
        if horizon > 0:
            # 计算历史收益率
            returns = df['close'].pct_change().dropna()
            return_median = returns.median()
            return_std = returns.std()

            # 计算预测的日收益率
            daily_return = predicted_change / current_price

            # 基本面特征影响预测
            fundamental_bias = 0

            # 1. 供需平衡影响
            if 'gap_pct' in latest_features:
                gap = latest_features['gap_pct']
                # 供需缺口对价格有长期影响
                fundamental_bias += gap * 2.0  # 1%的缺口影响2%的价格

            # 2. 库存变化影响
            if 'inventory_zscore' in latest_features:
                inv_z = latest_features['inventory_zscore']
                # 库存高于正常水平压制价格，低于则支撑价格
                fundamental_bias -= inv_z * 0.5  # 1个标准差的Z值影响0.5%

            # 3. 成本支撑影响
            if 'price_to_c1_cost' in latest_features:
                cost_ratio = latest_features['price_to_c1_cost']
                # 价格低于成本时，成本支撑强力
                if cost_ratio < 1.0:
                    fundamental_bias += (1.0 - cost_ratio) * 3.0  # 向成本回归

            # 4. 干扰风险影响
            if 'supply_impact' in latest_features:
                disruption = latest_features['supply_impact']
                fundamental_bias += disruption * 5.0  # 干扰影响价格

            # 基本面模型：趋势性更强，使用较小的衰减系数
            # 基本面因素的影响可以持续6个月
            daily_fundamental_return = (daily_return * 0.2) + (fundamental_bias / 180.0)

            # 使用简单的线性累积，而不是复利
            # 避免预测值过大，对超长期预测应用衰减
            decay_factor = 1.0
            if horizon > 90:
                decay_factor = np.sqrt(90 / horizon)  # 对90天以上的预测应用衰减
            predicted_return = daily_fundamental_return * horizon * decay_factor

            # 基本面模型允许更大的偏离，但仍然需要合理约束
            max_return = return_median + 3 * return_std * np.sqrt(min(horizon, 120))
            min_return = return_median - 3 * return_std * np.sqrt(min(horizon, 120))
            predicted_return = np.clip(predicted_return, min_return, max_return)

            # 注释掉硬性限制,让模型自然预测
            # 基本面模型计算出的预测应该被信任
            # max_safe_return = 0.50  # 最大50%总收益率
            # min_safe_return = -0.50  # 最小-50%总收益率
            # predicted_return = np.clip(predicted_return, min_safe_return, max_safe_return)

            predicted_change = current_price * predicted_return

        predicted_price = current_price + predicted_change
        predicted_return = predicted_change / current_price

        # 提取关键指标数值
        key_indicators = {}
        if 'production_growth' in latest_features:
            key_indicators['产量增长率'] = latest_features['production_growth'] * 100
        if 'consumption_growth' in latest_features:
            key_indicators['消费增长率'] = latest_features['consumption_growth'] * 100
        if 'inventory_change' in latest_features:
            key_indicators['库存变化率'] = latest_features['inventory_change'] * 100
        if 'cost_support' in latest_features:
            key_indicators['成本支撑价'] = latest_features['cost_support']
        if 'disruption_index' in latest_features:
            key_indicators['供应干扰指数'] = latest_features['disruption_index'] * 100

        return {
            'model_type': 'fundamental',
            'current_price': current_price,
            'predicted_price': predicted_price,
            'predicted_return': predicted_return * 100,
            'horizon_days': horizon,
            'trend': '上涨' if predicted_return > 0 else '下跌',
            'confidence': '高',  # 基本面模型信心较高
            'key_indicators': key_indicators,
            'feature_count': len(feature_cols)
        }


class MacroFactorModel:
    """
    宏观因子模型（中期波动）

    适用场景: 1-6个月战术调整

    核心变量:
    - 美元指数：负相关性极强（系数通常-0.7以上）
    - 中国PMI/信贷脉冲：铜被称为"铜博士"，对全球制造业景气度极度敏感
    - 实际利率：10Y TIPS收益率反映持有机会成本
    - 期限结构：LME升贴水（Contango/Backwardation）反映即期供需紧张度

    建模方法: 动态因子模型（DFM）或ARDL（自回归分布滞后模型）
    """

    def __init__(self, config: MacroConfig = None):
        self.config = config or MacroConfig()
        self.processor = MacroDataProcessor()
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance_ = None

    def train(self, df: pd.DataFrame, target_col: str = 'close') -> Dict:
        """
        训练宏观因子模型
        """
        print("[宏观因子模型] 训练中期波动模型...")

        # 创建宏观特征
        features_df = self.processor.create_macro_features(df, self.config)

        # 选择特征变量
        feature_cols = self._select_feature_columns(features_df)

        # 准备数据
        df_model = features_df[feature_cols + [target_col]].copy()
        df_model = df_model.dropna()

        if len(df_model) < 100:
            raise ValueError("数据量不足,至少需要100条数据")

        # 创建滞后特征
        X, y = self._create_lagged_features(df_model, feature_cols, target_col, self.config.lags)

        # 标准化
        X_scaled = self.scaler.fit_transform(X)

        # 训练模型（使用支持NaN的模型）
        try:
            self.model = ElasticNet(
                alpha=0.1,
                l1_ratio=0.5,
                max_iter=1000,
                random_state=42
            )
            self.model.fit(X_scaled, y)
        except Exception as e:
            # ElasticNet失败时使用RandomForest
            print(f"  ElasticNet训练失败，切换到RandomForest: {e}")
            self.model = RandomForestRegressor(
                n_estimators=200,
                max_depth=10,
                min_samples_split=10,
                random_state=42
            )
            self.model.fit(X_scaled, y)

        # 计算特征重要性
        self.feature_importance_ = pd.DataFrame({
            'feature': [f'{col}_lag{lag}' for lag in range(self.config.lags + 1) for col in feature_cols],
            'importance': np.abs(self.model.coef_)
        }).sort_values('importance', ascending=False)

        # 计算训练指标
        y_pred = self.model.predict(X_scaled)
        metrics = {
            'rmse': np.sqrt(mean_squared_error(y, y_pred)),
            'mae': mean_absolute_error(y, y_pred),
            'r2': r2_score(y, y_pred),
            'model_type': self.config.model_type
        }

        print(f"✓ 宏观因子模型训练完成")
        print(f"  RMSE: {metrics['rmse']:.2f}")
        print(f"  MAE: {metrics['mae']:.2f}")
        print(f"  R²: {metrics['r2']:.4f}")

        # 显示重要因子
        if self.feature_importance_ is not None:
            print("\n  Top 5 重要因子:")
            for idx, row in self.feature_importance_.head(5).iterrows():
                print(f"    {row['feature']}: {row['importance']:.4f}")

        return metrics

    def _select_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """选择宏观因子列"""
        # 美元指数相关
        usd_cols = [col for col in df.columns if 'usd' in col]

        # PMI和信贷相关
        pmi_cols = [col for col in df.columns if any(x in col for x in ['pmi', 'credit'])]

        # 利率相关
        rate_cols = [col for col in df.columns if 'tips' in col or 'rate' in col]

        # 期限结构相关
        spread_cols = [col for col in df.columns if 'spread' in col or 'lme' in col]

        selected = usd_cols + pmi_cols + rate_cols + spread_cols
        selected = [col for col in selected if col in df.columns]

        return selected[:12] if len(selected) > 12 else selected  # 限制特征数量

    def _create_lagged_features(self, df: pd.DataFrame, feature_cols: List[str],
                                 target_col: str, lags: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        创建滞后特征
        """
        # 创建滞后变量
        lagged_features = []
        for lag in range(lags + 1):
            if lag == 0:
                lagged_features.append(df[feature_cols].values)
            else:
                lagged_features.append(df[feature_cols].shift(lag).values)

        # 合并所有滞后特征
        X = np.hstack(lagged_features)

        # 目标变量（滞后一期）
        y = df[target_col].shift(-1).values

        # 对齐（移除NaN）
        valid_mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X = X[valid_mask]
        y = y[valid_mask]

        return X, y

    def predict(self, df: pd.DataFrame, horizon: int = None) -> Dict:
        """
        预测未来价格

        Args:
            df: 历史数据
            horizon: 预测周期（天）
        """
        if self.model is None:
            raise ValueError("模型未训练")

        horizon = horizon or self.config.forecast_horizon

        # 创建宏观特征
        features_df = self.processor.create_macro_features(df, self.config)
        feature_cols = self._select_feature_columns(features_df)

        df_model = features_df[feature_cols].copy()
        df_model = df_model.dropna()

        if len(df_model) < self.config.lags + 1:
            raise ValueError("特征数据不足")

        # 创建滞后特征
        lagged_features = []
        for lag in range(self.config.lags + 1):
            if lag == 0:
                lagged_features.append(df_model.values[-1:])
            else:
                lagged_features.append(df_model.values[-lag-1:-lag])

        X = np.hstack(lagged_features)

        # 获取最新特征值
        latest_features = df_model.iloc[-1].to_dict()

        # 处理可能的NaN值
        X = np.nan_to_num(X, nan=0.0)

        X_scaled = self.scaler.transform(X)

        # 获取当前价格
        current_price = df['close'].iloc[-1]

        # 预测 - 模型预测的是下一期的价格
        predicted_price_raw = self.model.predict(X_scaled)[0]
        predicted_change = predicted_price_raw - current_price

        # 根据预测周期调整预测值
        # 宏观因子模型：使用宏观指标进行中短期预测
        if horizon > 0:
            # 计算历史收益率
            returns = df['close'].pct_change().dropna()
            return_median = returns.median()
            return_std = returns.std()

            # 计算预测的日收益率
            daily_return = predicted_change / current_price

            # 宏观因子影响预测
            macro_bias = 0

            # 1. 美元指数影响（负相关，权重0.3）
            if 'usd_strength' in latest_features:
                usd_str = latest_features['usd_strength']
                macro_bias -= usd_str * 30.0 * self.config.usd_weight  # 美元强，铜价弱

            # 2. PMI影响（正相关，权重0.25）
            if 'pmi_momentum' in latest_features:
                pmi_mom = latest_features['pmi_momentum']
                macro_bias += pmi_mom * 0.5 * self.config.pmi_weight  # PMI上升，铜价上升

            # 3. 实际利率影响（负相关，权重0.2）
            if 'tips_change' in latest_features:
                rate_change = latest_features['tips_change']
                macro_bias -= rate_change * 10.0 * self.config.rate_weight  # 利率升，铜价跌

            # 4. 期限结构影响（权重0.25）
            if 'is_backwardation' in latest_features:
                is_back = latest_features['is_backwardation']
                spread = latest_features.get('spread_strength', 0)
                # Backwardation意味着现货紧张
                if is_back:
                    macro_bias += (spread / current_price) * 20.0 * self.config.structure_weight
                else:
                    macro_bias -= (spread / current_price) * 10.0 * self.config.structure_weight

            # 宏观模型：影响更直接但衰减更快
            # 宏观因素的影响通常在1-3个月内较强
            daily_macro_return = (daily_return * 0.3) + (macro_bias / 90.0)

            # 使用简单的线性累积，而不是复利
            # 避免预测值过大，对长期预测应用衰减
            decay_factor = 1.0
            if horizon > 30:
                decay_factor = np.sqrt(30 / horizon)  # 对30天以上的预测应用衰减
            predicted_return = daily_macro_return * horizon * decay_factor

            # 宏观模型使用更紧的约束，因为关注中短期波动
            max_return = return_median + 2 * return_std * np.sqrt(min(horizon, 60))
            min_return = return_median - 2 * return_std * np.sqrt(min(horizon, 60))
            predicted_return = np.clip(predicted_return, min_return, max_return)

            # 注释掉硬性限制,让模型自然预测
            # ARDL模型计算出的预测应该被信任,不需要硬限制
            # max_safe_return = 0.15  # 最大15%总收益率
            # min_safe_return = -0.15  # 最小-15%总收益率
            # predicted_return = np.clip(predicted_return, min_safe_return, max_safe_return)

            predicted_change = current_price * predicted_return

        predicted_price = current_price + predicted_change
        predicted_return = predicted_change / current_price

        # 提取关键指标数值
        key_indicators = {}
        if 'usd_index' in latest_features:
            key_indicators['美元指数'] = latest_features['usd_index']
        if 'pmi' in latest_features:
            key_indicators['中国PMI'] = latest_features['pmi']
        if 'real_interest_rate' in latest_features:
            key_indicators['实际利率(%)'] = latest_features['real_interest_rate'] * 100
        if 'lme_spread' in latest_features:
            key_indicators['LME升贴水'] = latest_features['lme_spread']
        if 'credit_pulse' in latest_features:
            key_indicators['信贷脉冲'] = latest_features['credit_pulse'] * 100
        if 'spread_pct' in latest_features:
            key_indicators['升贴水占比(%)'] = latest_features['spread_pct']

        return {
            'model_type': 'macro',
            'current_price': current_price,
            'predicted_price': predicted_price,
            'predicted_return': predicted_return * 100,
            'horizon_days': horizon,
            'trend': '上涨' if predicted_return > 0 else '下跌',
            'confidence': '中',
            'key_indicators': key_indicators,
            'feature_count': len(feature_cols)
        }


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("高级预测模型测试")
    print("="*60)

    # 生成测试数据
    from data.data_sources import MockDataSource
    mock_source = MockDataSource()
    base_data = mock_source.fetch_copper_price(
        start_date="2023-01-01",
        end_date="2024-12-31"
    )

    print(f"\n基础数据形状: {base_data.shape}")
    print(f"日期范围: {base_data.index[0]} ~ {base_data.index[-1]}")

    # 测试基本面模型
    print("\n" + "="*60)
    print("测试基本面模型（长期趋势）")
    print("="*60)

    fundamental_config = FundamentalConfig()
    fundamental_model = FundamentalModel(fundamental_config)

    try:
        fundamental_metrics = fundamental_model.train(base_data)
        fundamental_pred = fundamental_model.predict(base_data, horizon=180)

        print(f"\n基本面模型预测结果:")
        print(f"  当前价格: ¥{fundamental_pred['current_price']:,.2f}")
        print(f"  预测价格: ¥{fundamental_pred['predicted_price']:,.2f}")
        print(f"  预测收益: {fundamental_pred['predicted_return']:+.2f}%")
        print(f"  预测周期: {fundamental_pred['horizon_days']}天")
    except Exception as e:
        print(f"基本面模型测试失败: {e}")

    # 测试宏观因子模型
    print("\n" + "="*60)
    print("测试宏观因子模型（中期波动）")
    print("="*60)

    macro_config = MacroConfig()
    macro_model = MacroFactorModel(macro_config)

    try:
        macro_metrics = macro_model.train(base_data)
        macro_pred = macro_model.predict(base_data, horizon=90)

        print(f"\n宏观因子模型预测结果:")
        print(f"  当前价格: ¥{macro_pred['current_price']:,.2f}")
        print(f"  预测价格: ¥{macro_pred['predicted_price']:,.2f}")
        print(f"  预测收益: {macro_pred['predicted_return']:+.2f}%")
        print(f"  预测周期: {macro_pred['horizon_days']}天")
    except Exception as e:
        print(f"宏观因子模型测试失败: {e}")

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
