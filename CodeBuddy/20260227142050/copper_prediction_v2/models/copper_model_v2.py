"""
铜价预测模型 v2 - XGBoost + 技术指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("XGBoost未安装,请运行: pip install xgboost")

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class ModelConfig:
    """模型配置"""
    n_estimators: int = 500
    max_depth: int = 6
    learning_rate: float = 0.05
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    min_child_weight: int = 1
    reg_alpha: float = 0.1
    reg_lambda: float = 1.0
    random_state: int = 42


class FeatureEngineer:
    """特征工程器"""

    def __init__(self):
        self.feature_names = []

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        创建技术特征

        Args:
            data: 原始价格数据 (OHLCV)

        Returns:
            包含特征的DataFrame
        """
        df = data.copy()

        # 1. 基础价格特征
        df['returns_1d'] = df['close'].pct_change()
        df['returns_5d'] = df['close'].pct_change(5)
        df['returns_20d'] = df['close'].pct_change(20)

        # 2. 移动平均
        for window in [5, 10, 20, 30, 60]:
            df[f'ma_{window}'] = df['close'].rolling(window).mean()
            df[f'ma_ratio_{window}'] = df['close'] / df[f'ma_{window}']

        # 3. 波动率
        df['volatility_5d'] = df['returns_1d'].rolling(5).std()
        df['volatility_20d'] = df['returns_1d'].rolling(20).std()

        # 4. RSI (相对强弱指数)
        df['rsi_14'] = self._calculate_rsi(df['close'], 14)

        # 5. MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # 6. 布林带
        df['bb_middle'] = df['close'].rolling(20).mean()
        df['bb_std'] = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # 7. 成交量特征
        df['volume_ma_5'] = df['volume'].rolling(5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_5']

        # 8. 价格动量
        df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_20'] = df['close'] / df['close'].shift(20) - 1

        # 9. 高低价特征
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']

        # 10. 趋势特征
        df['trend_5'] = df['close'] / df['close'].shift(5) - 1
        df['trend_20'] = df['close'] / df['close'].shift(20) - 1

        # 删除包含NaN的行
        df = df.dropna()

        # 保存特征名称
        self.feature_names = df.columns.tolist()

        return df

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class XGBoostModel:
    """XGBoost预测模型"""

    def __init__(self, config: ModelConfig = None):
        """
        初始化模型

        Args:
            config: 模型配置
        """
        if not XGB_AVAILABLE:
            raise ImportError("XGBoost未安装: pip install xgboost")

        self.config = config or ModelConfig()
        self.model = None
        self.feature_names = []
        self.scaler = None

    def train(self, features: pd.DataFrame, target: pd.Series) -> Dict:
        """
        训练模型

        Args:
            features: 特征数据
            target: 目标变量

        Returns:
            训练指标
        """
        # 数据分割
        split_idx = int(len(features) * 0.8)
        X_train, X_val = features.iloc[:split_idx], features.iloc[split_idx:]
        y_train, y_val = target.iloc[:split_idx], target.iloc[split_idx:]

        # 保存特征名称
        self.feature_names = features.columns.tolist()

        # 创建DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        # 训练参数
        params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'max_depth': self.config.max_depth,
            'eta': self.config.learning_rate,
            'subsample': self.config.subsample,
            'colsample_bytree': self.config.colsample_bytree,
            'min_child_weight': self.config.min_child_weight,
            'alpha': self.config.reg_alpha,
            'lambda': self.config.reg_lambda,
            'seed': self.config.random_state
        }

        # 训练
        evals_result = {}
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=self.config.n_estimators,
            evals=[(dtrain, 'train'), (dval, 'val')],
            verbose_eval=False,
            evals_result=evals_result
        )

        # 计算指标
        y_pred = self.model.predict(dval)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        mae = mean_absolute_error(y_val, y_pred)

        return {
            'rmse': rmse,
            'mae': mae,
            'train_losses': evals_result['train']['rmse'],
            'val_losses': evals_result['val']['rmse']
        }

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """
        预测

        Args:
            features: 特征数据

        Returns:
            预测结果
        """
        if self.model is None:
            raise ValueError("模型未训练")

        dtest = xgb.DMatrix(features)
        predictions = self.model.predict(dtest)

        return predictions

    def get_feature_importance(self) -> pd.DataFrame:
        """
        获取特征重要性

        Returns:
            特征重要性DataFrame
        """
        if self.model is None:
            raise ValueError("模型未训练")

        importance = self.model.get_score(importance_type='gain')

        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': [importance.get(f'f{i}', 0) for i in range(len(self.feature_names))]
        })

        df = df.sort_values('importance', ascending=False)

        return df


class CopperPriceModel:
    """兼容旧版的铜价预测模型"""

    def __init__(self):
        """初始化模型"""
        self.xgb_model = None
        self.feature_engineer = FeatureEngineer()

    def predict(self, data: pd.DataFrame) -> Dict:
        """
        生成预测

        Args:
            data: 价格数据

        Returns:
            预测结果字典
        """
        # 创建特征
        features = self.feature_engineer.create_features(data)

        # 使用简单的趋势预测作为备用
        close = data['close']
        ma20 = close.rolling(20).mean().iloc[-1]
        pred_return = (close.iloc[-1] / ma20 - 1) * 0.1

        return {
            'predicted_return': pred_return,
            'confidence': 0.5
        }


class BacktestEngine:
    """回测引擎"""

    def __init__(self, config: ModelConfig = None):
        """
        初始化回测引擎

        Args:
            config: 模型配置
        """
        self.config = config or ModelConfig()

    def run(self, model, data: pd.DataFrame, features: pd.DataFrame,
            strategy: str = 'trend_following') -> Dict:
        """
        运行回测

        Args:
            model: 预测模型
            data: 价格数据
            features: 特征数据
            strategy: 交易策略

        Returns:
            回测结果
        """
        # 使用简单的趋势跟踪策略
        close = data['close']
        returns = close.pct_change().fillna(0)

        # 策略信号
        ma20 = close.rolling(20).mean()
        signals = np.where(close > ma20, 1, -1)
        signals = pd.Series(signals, index=close.index).shift(1).fillna(0)

        # 策略收益
        strategy_returns = signals * returns

        # 计算指标
        total_return = (1 + strategy_returns).prod() - 1
        mean_return = strategy_returns.mean()
        std_return = strategy_returns.std()
        sharpe_ratio = mean_return / std_return * np.sqrt(252) if std_return > 0 else 0

        # 最大回撤
        cumulative = (1 + strategy_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        return {
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'returns': strategy_returns
        }


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("XGBoost模型测试")
    print("="*60)

    # 生成测试数据
    from data.data_sources import MockDataSource
    mock_source = MockDataSource()
    data = mock_source.fetch_copper_price(
        start_date="2023-01-01",
        end_date="2024-01-01"
    )

    print(f"\n数据形状: {data.shape}")

    # 特征工程
    feature_engineer = FeatureEngineer()
    features = feature_engineer.create_features(data)
    print(f"特征数量: {len(features.columns)}")

    # 生成目标
    target = (data['close'].shift(-5) / data['close'] - 1).loc[features.index]

    # 训练模型
    print("\n训练XGBoost模型...")
    model = XGBoostModel()
    metrics = model.train(features, target)

    print(f"RMSE: {metrics['rmse']:.4f}")
    print(f"MAE: {metrics['mae']:.4f}")

    # 特征重要性
    importance = model.get_feature_importance()
    print("\nTop 10 特征:")
    print(importance.head(10))

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
