"""
真实数据管理器 - 管理多种真实数据源
"""

import pandas as pd
from typing import Dict, Optional
from data.data_sources import AKShareDataSource
import warnings
warnings.filterwarnings('ignore')


class RealDataManager:
    """真实数据管理器"""

    def __init__(self):
        """初始化数据管理器"""
        self.ak = AKShareDataSource()
        self.yahoo = None  # Yahoo Finance (可选)

    def get_full_data(self, days: int = 365) -> pd.DataFrame:
        """
        获取完整数据（包括价格和宏观指标）

        Args:
            days: 获取多少天的历史数据

        Returns:
            完整的数据DataFrame
        """
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 尝试从AKShare获取数据
        if self.ak.available:
            try:
                data = self.ak.fetch_copper_price(
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d")
                )
                return data
            except Exception as e:
                print(f"AKShare数据获取失败: {e}")

        # 如果所有真实数据源都失败,返回空DataFrame
        return pd.DataFrame()

    def get_realtime_price(self) -> Dict:
        """
        获取实时价格

        Returns:
            包含实时价格信息的字典
        """
        result = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'sources': {}
        }

        # 尝试从AKShare获取实时数据
        if self.ak.available:
            try:
                import akshare as ak
                df = ak.futures_zh_spot_sina()
                # 查找铜相关品种
                copper_data = df[df['symbol'].str.contains('铜', na=False)]
                if not copper_data.empty:
                    result['sources']['AKShare'] = {
                        'price': float(copper_data.iloc[0]['price']) if 'price' in copper_data.columns else None,
                        'symbol': copper_data.iloc[0]['symbol'] if 'symbol' in copper_data.columns else 'Unknown'
                    }
            except Exception as e:
                result['sources']['AKShare'] = {'error': str(e)}

        return result


def get_data_source(source_type: str = 'auto'):
    """
    获取数据源

    Args:
        source_type: 'auto', 'akshare', 'mock'

    Returns:
        数据源实例
    """
    if source_type == 'akshare':
        return AKShareDataSource()
    elif source_type == 'mock':
        from data.data_sources import MockDataSource
        return MockDataSource()
    else:  # auto
        # 先尝试AKShare,不可用则使用模拟数据
        ak_source = AKShareDataSource()
        if ak_source.available:
            return ak_source
        else:
            from data.data_sources import MockDataSource
            return MockDataSource()
