"""
数据源管理 - 模拟数据和真实数据获取
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class MockDataSource:
    """模拟数据源 - 生成模拟的铜价数据"""

    def __init__(self, start_date: str = None, end_date: str = None):
        if start_date is None:
            self.start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        else:
            self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")

    def fetch_copper_price(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取模拟铜价数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含OHLCV数据的DataFrame
        """
        # 生成日期范围
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        # 生成模拟价格数据
        np.random.seed(42)
        base_price = 70000  # 铜价基准
        n = len(date_range)

        # 使用随机游走生成价格序列
        returns = np.random.normal(0, 0.02, n)  # 日收益率
        returns[0] = 0

        # 计算价格
        price = base_price * np.cumprod(1 + returns)

        # 生成OHLCV数据
        data = {
            'open': price * (1 + np.random.uniform(-0.005, 0.005, n)),
            'high': price * (1 + np.random.uniform(0, 0.01, n)),
            'low': price * (1 + np.random.uniform(-0.01, 0, n)),
            'close': price,
            'volume': np.random.randint(100000, 500000, n),
            'turnover': price * np.random.randint(100000, 500000, n)
        }

        # 确保high >= max(open, close) 且 low <= min(open, close)
        df = pd.DataFrame(data, index=date_range)
        df['high'] = df[['open', 'close', 'high']].max(axis=1)
        df['low'] = df[['open', 'close', 'low']].min(axis=1)

        # 添加一些技术指标作为辅助数据
        df['vwap'] = (df['high'] + df['low'] + 2 * df['close']) / 4

        return df

    def fetch_macro_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取模拟宏观经济数据"""
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        n = len(date_range)
        np.random.seed(43)

        data = {
            'usd_index': np.random.uniform(100, 105, n),
            'pmi': np.random.uniform(48, 52, n),
            'inventory_change': np.random.normal(0, 1000, n)
        }

        return pd.DataFrame(data, index=date_range)


class AKShareDataSource:
    """AKShare数据源 - 从AKShare获取真实数据"""

    def __init__(self):
        self.available = False
        self._check_availability()

    def _check_availability(self):
        """检查AKShare是否可用"""
        try:
            import akshare as ak
            self.available = True
        except ImportError:
            self.available = False
            print("提示: 安装AKShare可获取真实数据: pip install akshare")

    def fetch_copper_price(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        从AKShare获取铜价数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含铜价数据的DataFrame
        """
        if not self.available:
            raise ImportError("AKShare未安装")

        try:
            import akshare as ak

            # 尝试获取上海铜期货数据
            df = ak.futures_zh_daily_sina(symbol="CU0")  # 上海铜期货

            # 数据清洗
            df.index = pd.to_datetime(df['date'])
            df = df[['open', 'high', 'low', 'close', 'volume']]

            # 添加成交额
            df['turnover'] = df['close'] * df['volume']

            # 筛选日期范围
            df = df[(df.index >= start_date) & (df.index <= end_date)]

            return df

        except Exception as e:
            print(f"AKShare数据获取失败: {e}")
            raise


class DataMerger:
    """数据合并器 - 合并多源数据"""

    @staticmethod
    def merge_dataframes(dfs: Dict[str, pd.DataFrame], method: str = 'outer') -> pd.DataFrame:
        """
        合并多个DataFrame

        Args:
            dfs: 数据源字典 {name: dataframe}
            method: 合并方法 ('inner', 'outer')

        Returns:
            合并后的DataFrame
        """
        if not dfs:
            return pd.DataFrame()

        # 使用第一个DataFrame作为基础
        keys = list(dfs.keys())
        merged = dfs[keys[0]]

        # 依次合并其他DataFrame
        for key in keys[1:]:
            merged = pd.merge(
                merged,
                dfs[key],
                left_index=True,
                right_index=True,
                how=method,
                suffixes=('', f'_{key}')
            )

        return merged

    @staticmethod
    def handle_missing_values(df: pd.DataFrame, method: str = 'ffill') -> pd.DataFrame:
        """
        处理缺失值

        Args:
            df: 输入DataFrame
            method: 填充方法 ('ffill', 'bfill', 'interpolate', 'drop')

        Returns:
            处理后的DataFrame
        """
        df = df.copy()

        if method == 'ffill':
            df = df.fillna(method='ffill').fillna(method='bfill')
        elif method == 'bfill':
            df = df.fillna(method='bfill').fillna(method='ffill')
        elif method == 'interpolate':
            df = df.interpolate(method='linear').fillna(method='ffill')
        elif method == 'drop':
            df = df.dropna()

        return df
