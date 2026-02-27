"""
Copper Price Prediction v2 - 改进版铜价预测系统
基于XGBoost + LSTM集成模型
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    StandardScaler = None
    print("警告: 未安装机器学习库，将使用简化版模型")

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class ModelConfig:
    """模型配置"""
    # XGBoost参数
    xgb_n_estimators: int = 500
    xgb_max_depth: int = 6
    xgb_learning_rate: float = 0.05
    
    # LSTM参数
    lstm_hidden_dim: int = 128
    lstm_num_layers: int = 2
    lstm_dropout: float = 0.2
    
    # 回测参数
    initial_capital: float = 1_000_000
    commission_rate: float = 0.0002
    slippage: float = 0.0001
    
    # 特征参数
    lookback_window: int = 60
    forecast_horizon: int = 5


class DataLoader:
    """数据加载器 - 支持多种数据源"""
    
    def __init__(self):
        self.cache = {}
        
    def load_mock_data(self, days: int = 500) -> pd.DataFrame:
        """生成模拟数据用于测试"""
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # 生成价格数据（带趋势和季节性的随机游走）
        returns = np.random.randn(days) * 0.015  # 日收益率
        trend = np.linspace(0, 0.05, days)  # 轻微上升趋势
        seasonal = 0.01 * np.sin(np.arange(days) * 2 * np.pi / 30)  # 月度季节性
        
        # 使用对数收益率避免数值爆炸
        log_returns = returns + trend / days + seasonal
        prices = 80000 * np.exp(np.cumsum(log_returns))
        
        # 限制价格范围在合理区间
        prices = np.clip(prices, 50000, 150000)
        
        df = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.randn(days) * 0.005),
            'high': prices * (1 + abs(np.random.randn(days)) * 0.008),
            'low': prices * (1 - abs(np.random.randn(days)) * 0.008),
            'close': prices,
            'volume': np.random.randint(10000, 100000, days),
            # 宏观指标
            'dollar_index': 100 + np.cumsum(np.random.randn(days) * 0.2),
            'china_pmi': 50 + np.random.randn(days) * 1.5,
            # 库存数据
            'lme_inventory': 250000 + np.cumsum(np.random.randn(days) * 500),
            'shfe_inventory': 280000 + np.cumsum(np.random.randn(days) * 400),
        })
        
        df.set_index('date', inplace=True)
        return df
    
    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        """从CSV加载数据"""
        df = pd.read_csv(filepath, parse_dates=['date'])
        df.set_index('date', inplace=True)
        return df


class FeatureEngineer:
    """特征工程 - 生成技术指标和统计特征"""
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.scaler = StandardScaler() if StandardScaler else None
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建完整特征集"""
        features = pd.DataFrame(index=df.index)
        
        # 1. 价格特征
        features = self._add_price_features(df, features)
        
        # 2. 技术指标
        features = self._add_technical_indicators(df, features)
        
        # 3. 宏观特征
        features = self._add_macro_features(df, features)
        
        # 4. 统计特征
        features = self._add_statistical_features(df, features)
        
        # 5. 交互特征
        features = self._add_interaction_features(df, features)
        
        return features.dropna()
    
    def _add_price_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """价格相关特征"""
        close = df['close']
        
        # 收益率
        features['returns_1d'] = close.pct_change(1)
        features['returns_5d'] = close.pct_change(5)
        features['returns_20d'] = close.pct_change(20)
        
        # 波动率
        features['volatility_5d'] = close.pct_change().rolling(5).std()
        features['volatility_20d'] = close.pct_change().rolling(20).std()
        
        # 价格位置
        features['price_to_ma20'] = close / close.rolling(20).mean()
        features['price_to_ma60'] = close / close.rolling(60).mean()
        
        # 高低点
        features['high_low_ratio'] = df['high'] / df['low']
        features['close_to_high'] = close / df['high'].rolling(20).max()
        features['close_to_low'] = close / df['low'].rolling(20).min()
        
        return features
    
    def _add_technical_indicators(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """技术指标"""
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        features['macd'] = ema_12 - ema_26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        # 布林带
        ma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        features['bb_upper'] = ma_20 + (std_20 * 2)
        features['bb_lower'] = ma_20 - (std_20 * 2)
        features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / ma_20
        features['bb_position'] = (close - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
        
        # OBV (能量潮)
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])
        features['obv'] = obv
        features['obv_ma20'] = features['obv'].rolling(20).mean()
        
        return features
    
    def _add_macro_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """宏观指标特征"""
        if 'dollar_index' in df.columns:
            features['dollar_change_5d'] = df['dollar_index'].pct_change(5)
            features['dollar_ma20'] = df['dollar_index'] / df['dollar_index'].rolling(20).mean()
        
        if 'china_pmi' in df.columns:
            features['pmi_diff'] = df['china_pmi'] - 50
            features['pmi_ma3'] = df['china_pmi'].rolling(3).mean() - 50
        
        if 'lme_inventory' in df.columns:
            features['inventory_change_1w'] = df['lme_inventory'].pct_change(5)
            features['inventory_change_1m'] = df['lme_inventory'].pct_change(20)
            features['inventory_to_price'] = df['lme_inventory'] / df['close']
        
        if 'shfe_inventory' in df.columns:
            features['shfe_inventory_change'] = df['shfe_inventory'].pct_change(5)
        
        return features
    
    def _add_statistical_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """统计特征"""
        close = df['close']
        
        # 分布统计
        features['skewness_20'] = close.rolling(20).skew()
        features['kurtosis_20'] = close.rolling(20).kurt()
        
        # 动量
        for window in [5, 10, 20]:
            features[f'momentum_{window}'] = (close - close.shift(window)) / close.shift(window)
        
        # 均线排列
        ma_5 = close.rolling(5).mean()
        ma_10 = close.rolling(10).mean()
        ma_20 = close.rolling(20).mean()
        ma_60 = close.rolling(60).mean()
        
        features['ma_alignment'] = (
            (close > ma_5).astype(int) +
            (ma_5 > ma_10).astype(int) +
            (ma_10 > ma_20).astype(int) +
            (ma_20 > ma_60).astype(int)
        ) / 4
        
        return features
    
    def _add_interaction_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """交互特征"""
        if 'dollar_index' in df.columns:
            features['price_x_dollar'] = df['close'] * df['dollar_index'] / 100000
        
        if 'volume' in df.columns:
            features['price_x_volume'] = df['close'] * df['volume'] / 1e9
        
        # 库存与价格的非线性关系
        if 'lme_inventory' in df.columns:
            features['inventory_sq'] = (df['lme_inventory'] / 100000) ** 2
        
        return features


class XGBoostModel:
    """XGBoost预测模型"""
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.model = None
        self.feature_importance = None
        
        if ML_AVAILABLE:
            self.model = xgb.XGBRegressor(
                n_estimators=self.config.xgb_n_estimators,
                max_depth=self.config.xgb_max_depth,
                learning_rate=self.config.xgb_learning_rate,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='reg:squarederror',
                eval_metric='rmse',
                random_state=42,
                n_jobs=-1
            )
    
    def train(self, X: pd.DataFrame, y: pd.Series, validation_split: float = 0.2):
        """训练模型"""
        if not ML_AVAILABLE:
            print("XGBoost不可用，跳过训练")
            return
        
        # 时序分割
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # 训练
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=50,
            verbose=False
        )
        
        # 特征重要性
        self.feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # 评估
        val_pred = self.model.predict(X_val)
        rmse = np.sqrt(mean_squared_error(y_val, val_pred))
        mae = mean_absolute_error(y_val, val_pred)
        
        print(f"验证集 RMSE: {rmse:.4f}, MAE: {mae:.4f}")
        
        return {'rmse': rmse, 'mae': mae}
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        if not ML_AVAILABLE or self.model is None:
            return np.zeros(len(X))
        return self.model.predict(X)
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """获取特征重要性"""
        if self.feature_importance is not None:
            return self.feature_importance.head(top_n)
        return None


class EnsembleModel:
    """集成模型 - 融合多个模型预测"""
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.models = {}
        self.weights = {}
        
    def add_model(self, name: str, model, weight: float = 1.0):
        """添加模型"""
        self.models[name] = model
        self.weights[name] = weight
        
    def train(self, X: pd.DataFrame, y: pd.Series):
        """训练所有模型"""
        for name, model in self.models.items():
            print(f"\n训练模型: {name}")
            if hasattr(model, 'train'):
                model.train(X, y)
            else:
                model.fit(X, y)
    
    def predict(self, X: pd.DataFrame) -> Dict:
        """集成预测"""
        predictions = {}
        
        for name, model in self.models.items():
            if hasattr(model, 'predict'):
                pred = model.predict(X)
                predictions[name] = pred
        
        # 加权平均
        total_weight = sum(self.weights.values())
        weighted_pred = np.zeros(len(X))
        
        for name, pred in predictions.items():
            weighted_pred += pred * self.weights[name] / total_weight
        
        # 计算模型分歧度（不确定性）
        pred_std = np.std(list(predictions.values()), axis=0) if len(predictions) > 1 else np.zeros(len(X))
        
        return {
            'ensemble_prediction': weighted_pred,
            'model_predictions': predictions,
            'uncertainty': pred_std,
            'confidence_interval': (
                weighted_pred - 1.96 * pred_std,
                weighted_pred + 1.96 * pred_std
            )
        }


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.trades = []
        self.positions = []
        
    def run(self, model, data: pd.DataFrame, features: pd.DataFrame, 
            strategy: str = 'trend_following') -> Dict:
        """
        运行回测
        
        strategy:
        - trend_following: 趋势跟踪
        - mean_reversion: 均值回归
        - target_position: 目标仓位
        """
        capital = self.config.initial_capital
        position = 0
        portfolio_values = [capital]
        
        # 生成预测
        if model is not None and hasattr(model, 'predict'):
            predictions = model.predict(features)
            if isinstance(predictions, dict):
                predictions = predictions['ensemble_prediction']
        else:
            # 使用简单移动平均策略作为回退
            close_prices = data['close'].values
            ma20 = pd.Series(close_prices).rolling(20).mean().values
            predictions = []
            for i in range(len(close_prices)):
                if i < 20 or pd.isna(ma20[i]):
                    predictions.append(0)
                else:
                    # 价格高于均线为正信号
                    predictions.append((close_prices[i] / ma20[i] - 1) * 10)
            predictions = np.array(predictions)
        
        # 转换为价格方向预测
        current_prices = data['close'].values
        forecast_returns = predictions
        
        for i in range(self.config.lookback_window, len(data) - 1):
            price = current_prices[i]
            next_price = current_prices[i + 1]
            pred_return = forecast_returns[i] if i < len(forecast_returns) else 0
            
            # 生成交易信号
            if strategy == 'trend_following':
                signal = self._trend_signal(pred_return)
            elif strategy == 'mean_reversion':
                signal = self._mean_reversion_signal(pred_return, price, np.mean(current_prices[max(0,i-20):i]))
            else:
                signal = self._target_position_signal(pred_return)
            
            # 执行交易
            if signal != 0 and position == 0:
                # 开仓
                shares = capital * 0.3 / price  # 30%仓位
                cost = shares * price * (1 + self.config.commission_rate + self.config.slippage)
                if cost <= capital:
                    position = shares * signal
                    capital -= abs(cost)
                    self.trades.append({
                        'date': data.index[i],
                        'action': 'buy' if signal > 0 else 'sell',
                        'price': price,
                        'shares': abs(shares)
                    })
            
            elif position != 0 and signal == 0:
                # 平仓
                proceeds = abs(position) * price * (1 - self.config.commission_rate - self.config.slippage)
                capital += proceeds
                entry_price = self.trades[-1]['price'] if self.trades else price
                self.trades.append({
                    'date': data.index[i],
                    'action': 'close',
                    'price': price,
                    'pnl': proceeds - abs(position) * entry_price
                })
                position = 0
            
            # 计算组合价值
            portfolio_value = capital + position * price if position != 0 else capital
            portfolio_values.append(portfolio_value)
        
        return self._calculate_metrics(portfolio_values, data)
    
    def _trend_signal(self, pred_return: float) -> int:
        """趋势跟踪信号"""
        if pred_return > 0.01:
            return 1  # 做多
        elif pred_return < -0.01:
            return -1  # 做空
        return 0
    
    def _mean_reversion_signal(self, pred_return: float, price: float, ma: float) -> int:
        """均值回归信号"""
        deviation = (price - ma) / ma
        if deviation < -0.02 and pred_return > 0:
            return 1
        elif deviation > 0.02 and pred_return < 0:
            return -1
        return 0
    
    def _target_position_signal(self, pred_return: float) -> int:
        """目标仓位信号"""
        if abs(pred_return) > 0.005:
            return 1 if pred_return > 0 else -1
        return 0
    
    def _calculate_metrics(self, portfolio_values: List[float], data: pd.DataFrame) -> Dict:
        """计算回测指标"""
        values = np.array(portfolio_values)
        returns = pd.Series(values).pct_change().dropna()
        
        # 基本指标
        total_return = (values[-1] / values[0] - 1) * 100
        n_days = len(values)
        annual_return = ((values[-1] / values[0]) ** (252 / n_days) - 1) * 100
        
        # 风险指标
        volatility = returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        
        # 最大回撤
        peak = np.maximum.accumulate(values)
        drawdown = (values - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # Calmar比率
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 胜率
        win_rate = (returns > 0).sum() / len(returns) * 100
        
        # 与基准比较（买入持有）
        benchmark_return = (data['close'].iloc[-1] / data['close'].iloc[self.config.lookback_window] - 1) * 100
        alpha = total_return - benchmark_return
        
        return {
            'total_return_pct': round(total_return, 2),
            'annual_return_pct': round(annual_return, 2),
            'volatility_pct': round(volatility, 2),
            'sharpe_ratio': round(sharpe_ratio, 3),
            'max_drawdown_pct': round(max_drawdown, 2),
            'calmar_ratio': round(calmar, 3),
            'win_rate_pct': round(win_rate, 2),
            'benchmark_return_pct': round(benchmark_return, 2),
            'alpha_pct': round(alpha, 2),
            'final_capital': round(values[-1], 2),
            'num_trades': len(self.trades)
        }


class CopperPredictionV2:
    """主控制类 - 整合所有模块"""
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.data_loader = DataLoader()
        self.feature_engineer = FeatureEngineer(self.config)
        self.models = {}
        self.backtest_engine = BacktestEngine(self.config)
        
    def load_data(self, source: str = 'mock', **kwargs) -> pd.DataFrame:
        """加载数据"""
        if source == 'mock':
            return self.data_loader.load_mock_data(**kwargs)
        elif source == 'csv':
            return self.data_loader.load_from_csv(**kwargs)
        else:
            raise ValueError(f"未知数据源: {source}")
    
    def prepare_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """准备特征和标签"""
        # 生成特征
        features = self.feature_engineer.create_features(data)
        
        # 生成标签（未来5日收益率）
        close = data['close']
        target = (close.shift(-self.config.forecast_horizon) / close - 1).loc[features.index]
        
        return features, target
    
    def train_model(self, features: pd.DataFrame, target: pd.Series, model_type: str = 'xgboost'):
        """训练模型"""
        if model_type == 'xgboost':
            model = XGBoostModel(self.config)
        else:
            raise ValueError(f"未知模型类型: {model_type}")
        
        model.train(features, target)
        self.models[model_type] = model
        return model
    
    def create_ensemble(self) -> EnsembleModel:
        """创建集成模型"""
        ensemble = EnsembleModel(self.config)
        
        for name, model in self.models.items():
            ensemble.add_model(name, model, weight=1.0)
        
        return ensemble
    
    def backtest(self, model, data: pd.DataFrame, features: pd.DataFrame) -> Dict:
        """运行回测"""
        return self.backtest_engine.run(model, data, features)
    
    def predict(self, model, features: pd.DataFrame) -> Dict:
        """生成预测"""
        return model.predict(features)
    
    def full_pipeline(self, data: pd.DataFrame = None) -> Dict:
        """完整流程"""
        print("=" * 60)
        print("铜价预测 v2 - 完整流程")
        print("=" * 60)
        
        # 1. 加载数据
        if data is None:
            print("\n[1/5] 加载模拟数据...")
            data = self.load_data('mock', days=500)
        else:
            print("\n[1/5] 使用提供的数据...")
        print(f"数据范围: {data.index[0]} 至 {data.index[-1]}")
        print(f"数据条数: {len(data)}")
        
        # 2. 特征工程
        print("\n[2/5] 生成特征...")
        features, target = self.prepare_features(data)
        print(f"特征数量: {len(features.columns)}")
        print(f"特征样例: {list(features.columns[:5])}")
        
        # 3. 训练模型
        print("\n[3/5] 训练模型...")
        if ML_AVAILABLE:
            model = self.train_model(features, target, 'xgboost')
            
            # 特征重要性
            importance = model.get_feature_importance(10)
            if importance is not None:
                print("\nTop 10 重要特征:")
                for _, row in importance.iterrows():
                    print(f"  {row['feature']}: {row['importance']:.4f}")
        else:
            print("ML库不可用，跳过模型训练")
            model = None
        
        # 4. 回测
        print("\n[4/5] 运行回测...")
        if model:
            results = self.backtest(model, data, features)
            print("\n回测结果:")
            for key, value in results.items():
                print(f"  {key}: {value}")
        
        # 5. 最新预测
        print("\n[5/5] 生成最新预测...")
        if model:
            latest_features = features.iloc[[-1]]
            prediction = self.predict(model, latest_features)
            
            current_price = data['close'].iloc[-1]
            if isinstance(prediction, dict):
                pred_return = prediction['ensemble_prediction'][0]
            else:
                pred_return = prediction[0]
            
            pred_price = current_price * (1 + pred_return)
            
            print(f"\n当前价格: ¥{current_price:,.2f}")
            print(f"预测价格({self.config.forecast_horizon}日后): ¥{pred_price:,.2f}")
            print(f"预测涨跌: {pred_return*100:.2f}%")
        
        print("\n" + "=" * 60)
        
        return {
            'data': data,
            'features': features,
            'target': target,
            'model': model,
            'backtest_results': results if model else None
        }


# 简化版API（兼容原接口）
class CopperPriceModel(CopperPredictionV2):
    """兼容原版的API接口"""
    
    def __init__(self):
        super().__init__()
        self._init_mock_data()
    
    def _init_mock_data(self):
        """初始化模拟数据用于演示"""
        self.data = self.load_data('mock', days=500)
        self.features, self.target = self.prepare_features(self.data)
        
        # 训练模型
        if ML_AVAILABLE:
            self.model = self.train_model(self.features, self.target, 'xgboost')
        else:
            self.model = None
    
    def predict_short_term(self, days: int = 5) -> Dict:
        """短期预测 - 兼容原接口"""
        current_price = self.data['close'].iloc[-1]
        
        if self.model:
            pred = self.model.predict(self.features.iloc[[-1]])[0]
        else:
            pred = 0
        
        predicted_price = current_price * (1 + pred)
        
        return {
            'period': f'{days}天',
            'current_price': round(current_price, 2),
            'predicted_price': round(predicted_price, 2),
            'predicted_change': round(pred * 100, 2),
            'trend': '上涨' if pred > 0 else '下跌',
            'confidence': '中等'
        }
    
    def predict_medium_term(self, months: int = 3) -> Dict:
        """中期预测 - 兼容原接口"""
        return self.predict_short_term(days=months*30)
    
    def predict_long_term(self, years: int = 1) -> Dict:
        """长期预测 - 兼容原接口"""
        return self.predict_short_term(days=years*365)


if __name__ == '__main__':
    # 运行完整流程
    predictor = CopperPredictionV2()
    results = predictor.full_pipeline()
