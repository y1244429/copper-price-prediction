"""
数据接入模块 - 支持多种数据源
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import warnings
warnings.filterwarnings('ignore')

class DataSourceBase:
    """数据源基类"""
    
    def fetch_copper_price(self, start_date: str, end_date: str) -> pd.DataFrame:
        raise NotImplementedError
    
    def fetch_inventory(self) -> pd.DataFrame:
        raise NotImplementedError
    
    def fetch_macro_data(self) -> pd.DataFrame:
        raise NotImplementedError


class AKShareDataSource(DataSourceBase):
    """
    AKShare数据源 - 免费中文财经数据
    安装: pip install akshare
    """
    
    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
            self.available = True
        except ImportError:
            self.available = False
            print("警告: 未安装akshare，请运行: pip install akshare")
    
    def fetch_copper_price(self, start_date: str, end_date: str, 
                          symbol: str = "CU") -> pd.DataFrame:
        """
        获取铜期货价格
        
        symbol: CU=沪铜主力, AL=沪铝, ZN=沪锌
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            # 获取上海期货交易所铜数据
            # 注意: akshare接口可能会变化
            df = self.ak.futures_zh_realtime(symbol=symbol)
            
            # 或者使用历史数据接口
            # df = self.ak.futures_zh_daily_sina(symbol=f"{symbol}0")
            
            return df
        except Exception as e:
            print(f"获取数据失败: {e}")
            return pd.DataFrame()
    
    def fetch_inventory_shfe(self) -> pd.DataFrame:
        """获取上期所库存数据"""
        if not self.available:
            return pd.DataFrame()
        
        try:
            # 获取上期所库存周报
            df = self.ak.futures_inventory_99(symbol="cu")
            return df
        except Exception as e:
            print(f"获取库存数据失败: {e}")
            return pd.DataFrame()
    
    def fetch_macro_china_pmi(self) -> pd.DataFrame:
        """获取中国PMI数据"""
        if not self.available:
            return pd.DataFrame()
        
        try:
            df = self.ak.macro_china_pmi()
            return df
        except Exception as e:
            print(f"获取PMI数据失败: {e}")
            return pd.DataFrame()


class MockDataSource(DataSourceBase):
    """
    模拟数据源 - 用于测试和演示
    生成更真实的铜价数据
    """
    
    def __init__(self):
        self.base_price = 80000  # 基准价格
        self.volatility = 0.015  # 日波动率
        
    def fetch_copper_price(self, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟铜价数据"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        
        dates = pd.date_range(start=start, periods=days, freq='D')
        
        # 生成更真实的价格走势
        np.random.seed(42)
        
        # 1. 基础随机游走
        returns = np.random.normal(0, self.volatility, days)
        
        # 2. 添加趋势
        trend = np.linspace(0, 0.1, days)
        
        # 3. 添加季节性 (铜通常在Q2-Q3旺季)
        day_of_year = np.array([d.dayofyear for d in dates])
        seasonal = 0.02 * np.sin((day_of_year - 60) * 2 * np.pi / 365)
        
        # 4. 添加均值回归
        prices = [self.base_price]
        for i in range(1, days):
            # 均值回归因子
            mean_reversion = -0.001 * (prices[-1] / self.base_price - 1)
            
            # 计算今日收益率
            daily_return = returns[i] + trend[i]/days + seasonal[i]/30 + mean_reversion
            
            new_price = prices[-1] * (1 + daily_return)
            prices.append(new_price)
        
        prices = np.array(prices)
        
        # 生成OHLC数据
        df = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.randn(days) * 0.003),
            'high': prices * (1 + abs(np.random.randn(days)) * 0.008),
            'low': prices * (1 - abs(np.random.randn(days)) * 0.008),
            'close': prices,
            'volume': np.random.randint(50000, 150000, days) + 
                     (np.sin(day_of_year * 2 * np.pi / 365) * 20000).astype(int)
        })
        
        df.set_index('date', inplace=True)
        return df
    
    def fetch_inventory(self, days: int = 365) -> pd.DataFrame:
        """生成模拟库存数据"""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # 库存通常与价格负相关
        np.random.seed(43)
        base_inventory = 250000
        
        # 添加趋势和波动
        trend = np.cumsum(np.random.randn(days) * 100)
        inventory = base_inventory + trend
        inventory = np.maximum(inventory, 100000)  # 最低库存
        
        df = pd.DataFrame({
            'date': dates,
            'lme_inventory': inventory,
            'shfe_inventory': inventory * 1.1 + np.random.randn(days) * 5000,
            'comex_inventory': inventory * 0.9 + np.random.randn(days) * 3000,
        })
        
        df.set_index('date', inplace=True)
        return df
    
    def fetch_macro_data(self, days: int = 365) -> pd.DataFrame:
        """生成模拟宏观数据"""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        np.random.seed(44)
        
        # 美元指数 (与铜价负相关)
        dollar_base = 100
        dollar_trend = np.cumsum(np.random.randn(days) * 0.1)
        dollar_index = dollar_base + dollar_trend
        dollar_index = np.clip(dollar_index, 90, 110)
        
        # 中国PMI (月度数据插值到日度)
        pmi_monthly = 50 + np.random.randn(days // 30 + 1) * 1.5
        pmi_daily = np.repeat(pmi_monthly, 30)[:days]
        
        # 实际利率
        real_rate = 1.5 + np.random.randn(days) * 0.3
        
        df = pd.DataFrame({
            'date': dates,
            'dollar_index': dollar_index,
            'china_pmi': pmi_daily,
            'us_real_rate': real_rate,
        })
        
        df.set_index('date', inplace=True)
        return df


class DataMerger:
    """数据合并器 - 整合多源数据"""
    
    def __init__(self, price_source: DataSourceBase, 
                 inventory_source: Optional[DataSourceBase] = None,
                 macro_source: Optional[DataSourceBase] = None):
        self.price_source = price_source
        self.inventory_source = inventory_source or price_source
        self.macro_source = macro_source or price_source
    
    def get_full_dataset(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取完整数据集"""
        # 1. 获取价格数据
        price_df = self.price_source.fetch_copper_price(start_date, end_date)
        
        if price_df.empty:
            return pd.DataFrame()
        
        # 2. 获取库存数据
        days = len(price_df)
        inventory_df = self.inventory_source.fetch_inventory(days)
        
        # 3. 获取宏观数据
        macro_df = self.macro_source.fetch_macro_data(days)
        
        # 4. 合并数据
        df = price_df.copy()
        
        # 对齐日期后合并
        if not inventory_df.empty:
            # 使用前向填充对齐库存数据
            inventory_df = inventory_df.reindex(df.index, method='ffill')
            df = df.join(inventory_df, how='left')
        
        if not macro_df.empty:
            macro_df = macro_df.reindex(df.index, method='ffill')
            df = df.join(macro_df, how='left')
        
        return df


# 便捷函数
def get_data_source(source_type: str = "mock") -> DataSourceBase:
    """
    获取数据源
    
    source_type: mock, akshare
    """
    if source_type == "akshare":
        return AKShareDataSource()
    else:
        return MockDataSource()


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("数据接入模块测试")
    print("="*60)
    
    # 使用模拟数据源
    source = MockDataSource()
    
    # 获取价格数据
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    print(f"\n获取价格数据: {start_date} 至 {end_date}")
    price_df = source.fetch_copper_price(start_date, end_date)
    print(f"数据条数: {len(price_df)}")
    print(f"价格范围: ¥{price_df['close'].min():.2f} - ¥{price_df['close'].max():.2f}")
    print(f"最新价格: ¥{price_df['close'].iloc[-1]:.2f}")
    
    # 获取库存数据
    print("\n获取库存数据...")
    inv_df = source.fetch_inventory(365)
    print(f"最新LME库存: {inv_df['lme_inventory'].iloc[-1]:,.0f} 吨")
    
    # 获取宏观数据
    print("\n获取宏观数据...")
    macro_df = source.fetch_macro_data(365)
    print(f"最新美元指数: {macro_df['dollar_index'].iloc[-1]:.2f}")
    print(f"最新中国PMI: {macro_df['china_pmi'].iloc[-1]:.2f}")
    
    # 数据合并测试
    print("\n合并数据测试...")
    merger = DataMerger(source)
    full_df = merger.get_full_dataset(start_date, end_date)
    print(f"合并后数据列: {list(full_df.columns)}")
    print(f"数据形状: {full_df.shape}")
    print("\n前5行数据:")
    print(full_df.head())
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
