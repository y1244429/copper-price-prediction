"""
高级技术指标模块
包含MACD、KDJ、RSI、布林带、均线系统等
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        MACD指标
        
        Returns:
            macd: MACD线
            signal: 信号线
            histogram: 柱状图
        """
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })
    
    @staticmethod
    def kdj(high: pd.Series, low: pd.Series, close: pd.Series, 
            n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """
        KDJ随机指标
        
        Args:
            n: RSV计算周期
            m1: K平滑因子
            m2: D平滑因子
        """
        lowest_low = low.rolling(window=n).min()
        highest_high = high.rolling(window=n).max()
        
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return pd.DataFrame({
            'k': k,
            'd': d,
            'j': j
        })
    
    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI相对强弱指标
        """
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def bollinger_bands(close: pd.Series, window: int = 20, 
                        num_std: float = 2.0) -> pd.DataFrame:
        """
        布林带
        
        Returns:
            middle: 中轨(MA)
            upper: 上轨
            lower: 下轨
            bandwidth: 带宽
            percent_b: %B指标
        """
        middle = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        bandwidth = (upper - lower) / middle
        percent_b = (close - lower) / (upper - lower)
        
        return pd.DataFrame({
            'middle': middle,
            'upper': upper,
            'lower': lower,
            'bandwidth': bandwidth,
            'percent_b': percent_b
        })
    
    @staticmethod
    def moving_averages(close: pd.Series) -> pd.DataFrame:
        """
        多周期均线系统
        """
        return pd.DataFrame({
            'ma5': close.rolling(window=5).mean(),
            'ma10': close.rolling(window=10).mean(),
            'ma20': close.rolling(window=20).mean(),
            'ma60': close.rolling(window=60).mean(),
            'ma120': close.rolling(window=120).mean(),
            'ma250': close.rolling(window=250).mean(),
            'ema12': close.ewm(span=12, adjust=False).mean(),
            'ema26': close.ewm(span=26, adjust=False).mean()
        })
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, 
            period: int = 14) -> pd.Series:
        """
        ATR真实波幅
        """
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        OBV能量潮
        """
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])
        
        return pd.Series(obv, index=close.index)
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, 
            period: int = 14) -> pd.DataFrame:
        """
        ADX平均趋向指标
        
        Returns:
            adx: ADX值
            plus_di: +DI
            minus_di: -DI
        """
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # +DM和-DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        plus_dm[plus_dm <= minus_dm] = 0
        minus_dm[minus_dm <= plus_dm] = 0
        
        # 平滑
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * plus_dm.rolling(window=period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=period).mean() / atr
        
        # DX和ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return pd.DataFrame({
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        })
    
    @staticmethod
    def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        """
        一目均衡表 (Ichimoku Cloud)
        """
        # 转换线 (Tenkan-sen): (9-period high + 9-period low)/2
        tenkan_sen = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
        
        # 基准线 (Kijun-sen): (26-period high + 26-period low)/2
        kijun_sen = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
        
        # 先行带1 (Senkou Span A): (转换线 + 基准线)/2, 前移26日
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        
        # 先行带2 (Senkou Span B): (52-period high + 52-period low)/2, 前移26日
        senkou_span_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
        
        # 延迟线 (Chikou Span): 收盘价后移26日
        chikou_span = close.shift(-26)
        
        return pd.DataFrame({
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        })
    
    @staticmethod
    def volume_profile(close: pd.Series, volume: pd.Series, 
                      bins: int = 20) -> pd.DataFrame:
        """
        成交量分布 (Volume Profile)
        
        计算不同价格区间的成交量分布
        """
        # 计算价格区间
        price_min = close.min()
        price_max = close.max()
        bin_edges = np.linspace(price_min, price_max, bins + 1)
        
        # 分配每个价格到区间
        bin_indices = np.digitize(close, bin_edges)
        
        # 计算每个区间的成交量
        volume_dist = pd.Series(index=range(1, bins + 1), dtype=float)
        for i in range(1, bins + 1):
            mask = bin_indices == i
            volume_dist.loc[i] = volume[mask].sum()
        
        # 找到POC (Point of Control - 最大成交量价格)
        poc_bin = volume_dist.idxmax()
        poc_price = (bin_edges[poc_bin - 1] + bin_edges[poc_bin]) / 2
        
        # 找到Value Area (70%成交量分布区间)
        total_volume = volume_dist.sum()
        cumsum = volume_dist.sort_values(ascending=False).cumsum()
        value_area_bins = cumsum[cumsum <= total_volume * 0.7].index
        
        return pd.DataFrame({
            'bin_edges': bin_edges[:-1],
            'volume': volume_dist.values,
            'poc_price': poc_price,
            'value_area_low': bin_edges[value_area_bins.min() - 1] if len(value_area_bins) > 0 else price_min,
            'value_area_high': bin_edges[value_area_bins.max()] if len(value_area_bins) > 0 else price_max
        })


class AdvancedFeatureEngineer:
    """高级特征工程 - 整合所有技术指标"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        创建完整的技术指标特征集
        """
        features = pd.DataFrame(index=df.index)
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df.get('volume', pd.Series(index=df.index, dtype=float))
        
        # 1. MACD
        print("  计算 MACD...")
        macd_df = self.indicators.macd(close)
        features = features.join(macd_df)
        
        # 2. KDJ
        print("  计算 KDJ...")
        kdj_df = self.indicators.kdj(high, low, close)
        features = features.join(kdj_df)
        
        # 3. RSI
        print("  计算 RSI...")
        features['rsi'] = self.indicators.rsi(close)
        features['rsi_6'] = self.indicators.rsi(close, period=6)
        features['rsi_24'] = self.indicators.rsi(close, period=24)
        
        # 4. 布林带
        print("  计算 布林带...")
        bb_df = self.indicators.bollinger_bands(close)
        features = features.join(bb_df)
        
        # 5. 均线系统
        print("  计算 均线系统...")
        ma_df = self.indicators.moving_averages(close)
        features = features.join(ma_df)
        
        # 6. ATR
        print("  计算 ATR...")
        features['atr'] = self.indicators.atr(high, low, close)
        features['atr_ratio'] = features['atr'] / close
        
        # 7. OBV
        if not volume.empty:
            print("  计算 OBV...")
            features['obv'] = self.indicators.obv(close, volume)
            features['obv_ma20'] = features['obv'].rolling(20).mean()
        
        # 8. ADX
        print("  计算 ADX...")
        adx_df = self.indicators.adx(high, low, close)
        features = features.join(adx_df)
        
        # 9. 一目均衡表
        print("  计算 一目均衡表...")
        ichi_df = self.indicators.ichimoku(high, low, close)
        features = features.join(ichi_df)
        
        # 10. 派生特征
        print("  计算 派生特征...")
        
        # 价格与均线关系
        features['price_to_ma20'] = close / features['ma20']
        features['price_to_ma60'] = close / features['ma60']
        
        # MACD信号
        features['macd_cross'] = np.where(
            features['macd'] > features['signal'], 1, 
            np.where(features['macd'] < features['signal'], -1, 0)
        )
        
        # KDJ信号
        features['kdj_overbought'] = (features['k'] > 80) & (features['d'] > 80)
        features['kdj_oversold'] = (features['k'] < 20) & (features['d'] < 20)
        
        # 均线排列
        features['ma_bullish'] = (
            (features['ma5'] > features['ma10']) &
            (features['ma10'] > features['ma20']) &
            (features['ma20'] > features['ma60'])
        ).astype(int)
        
        # 波动率
        features['volatility_20'] = close.pct_change().rolling(20).std()
        
        # 价格动量
        for window in [5, 10, 20]:
            features[f'momentum_{window}'] = (close / close.shift(window) - 1)
        
        return features.dropna()


# 技术分析信号生成器
class TechnicalSignals:
    """基于技术指标的交易信号生成"""
    
    @staticmethod
    def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        生成综合交易信号
        """
        signals = pd.DataFrame(index=df.index)
        
        # 1. MACD信号
        signals['macd_signal'] = np.where(
            (df['macd'] > df['signal']) & (df['macd'].shift(1) <= df['signal'].shift(1)), 1,  # 金叉
            np.where(
                (df['macd'] < df['signal']) & (df['macd'].shift(1) >= df['signal'].shift(1)), -1,  # 死叉
                0
            )
        )
        
        # 2. KDJ信号
        signals['kdj_signal'] = np.where(
            (df['k'] > df['d']) & (df['k'].shift(1) <= df['d'].shift(1)) & (df['k'] < 30), 1,
            np.where(
                (df['k'] < df['d']) & (df['k'].shift(1) >= df['d'].shift(1)) & (df['k'] > 70), -1,
                0
            )
        )
        
        # 3. RSI信号
        signals['rsi_signal'] = np.where(
            (df['rsi'] < 30) & (df['rsi'].shift(1) >= 30), 1,  # 超卖反弹
            np.where(
                (df['rsi'] > 70) & (df['rsi'].shift(1) <= 70), -1,  # 超买回调
                0
            )
        )
        
        # 4. 布林带信号
        signals['bb_signal'] = np.where(
            df['close'] < df['lower'], 1,  # 触及下轨，买入
            np.where(df['close'] > df['upper'], -1, 0)  # 触及上轨，卖出
        )
        
        # 5. 均线信号
        signals['ma_signal'] = np.where(
            (df['close'] > df['ma20']) & (df['close'].shift(1) <= df['ma20'].shift(1)), 1,
            np.where(
                (df['close'] < df['ma20']) & (df['close'].shift(1) >= df['ma20'].shift(1)), -1,
                0
            )
        )
        
        # 综合信号 (投票制)
        signal_sum = (signals['macd_signal'] + signals['kdj_signal'] + 
                     signals['rsi_signal'] + signals['bb_signal'] + signals['ma_signal'])
        
        signals['composite_signal'] = np.where(signal_sum >= 2, 1,
                                               np.where(signal_sum <= -2, -1, 0))
        
        return signals


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("技术指标模块测试")
    print("="*60)
    
    # 生成测试数据
    np.random.seed(42)
    n = 100
    
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq='D')
    
    # 生成价格数据
    returns = np.random.randn(n) * 0.02
    prices = 80000 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.randn(n) * 0.005),
        'high': prices * (1 + abs(np.random.randn(n)) * 0.008),
        'low': prices * (1 - abs(np.random.randn(n)) * 0.008),
        'close': prices,
        'volume': np.random.randint(10000, 100000, n)
    })
    df.set_index('date', inplace=True)
    
    print(f"\n测试数据: {len(df)} 条")
    print(df.tail())
    
    # 计算所有指标
    print("\n" + "="*60)
    print("计算技术指标...")
    print("="*60)
    
    engineer = AdvancedFeatureEngineer()
    features = engineer.create_all_features(df)
    
    print(f"\n✓ 生成特征: {len(features.columns)} 个")
    print("特征列表:")
    for col in features.columns:
        print(f"  - {col}")
    
    # 生成信号
    print("\n" + "="*60)
    print("生成交易信号...")
    print("="*60)
    
    # 合并价格和特征
    full_df = df.join(features, how='inner')
    
    signals = TechnicalSignals.generate_signals(full_df)
    
    print("\n信号统计:")
    print(f"  MACD金叉: {(signals['macd_signal'] == 1).sum()}")
    print(f"  MACD死叉: {(signals['macd_signal'] == -1).sum()}")
    print(f"  综合买入: {(signals['composite_signal'] == 1).sum()}")
    print(f"  综合卖出: {(signals['composite_signal'] == -1).sum()}")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
