"""
Wind数据源接入模块
支持Wind API和模拟数据（用于演示）
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class WindDataSource:
    """
    Wind金融终端数据接入
    
    注意：需要安装Wind API并登录账号
    pip install WindPy
    
    如果没有Wind账号，可以使用模拟模式
    """
    
    def __init__(self, mock_mode: bool = True):
        """
        Args:
            mock_mode: True=使用模拟数据, False=连接真实Wind
        """
        self.mock_mode = mock_mode
        self.w = None
        self.available = False
        
        if not mock_mode:
            self._init_wind()
        else:
            print("Wind数据源: 模拟模式")
    
    def _init_wind(self):
        """初始化Wind连接"""
        try:
            from WindPy import w
            self.w = w
            
            # 启动Wind
            result = w.start()
            if result.ErrorCode == 0:
                self.available = True
                print("✓ Wind连接成功")
            else:
                print(f"✗ Wind连接失败: {result.Data}")
                self.mock_mode = True
                
        except ImportError:
            print("✗ WindPy未安装，切换到模拟模式")
            print("  安装: pip install WindPy")
            self.mock_mode = True
    
    def get_future_daily(self, symbol: str = "CU.SHF", 
                        start_date: str = None,
                        end_date: str = None) -> pd.DataFrame:
        """
        获取期货日线数据
        
        Args:
            symbol: Wind代码
                - CU.SHF: 沪铜主力
                - AL.SHF: 沪铝主力
                - AU.SHF: 沪金主力
        """
        if self.mock_mode:
            return self._mock_future_daily(symbol, start_date, end_date)
        
        if not self.available:
            return pd.DataFrame()
        
        try:
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            # Wind API调用
            result = self.w.wsd(symbol, 
                               "open,high,low,close,volume,amt,oi",
                               start_date, end_date, "")
            
            if result.ErrorCode != 0:
                print(f"Wind查询错误: {result.Data}")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame({
                'open': result.Data[0],
                'high': result.Data[1],
                'low': result.Data[2],
                'close': result.Data[3],
                'volume': result.Data[4],
                'amount': result.Data[5],
                'open_interest': result.Data[6]
            }, index=pd.to_datetime(result.Times))
            
            return df
            
        except Exception as e:
            print(f"Wind获取数据失败: {e}")
            return pd.DataFrame()
    
    def get_inventory(self, variety: str = "CU") -> pd.DataFrame:
        """
        获取期货库存数据
        
        Args:
            variety: 品种代码 (CU=铜, AL=铝, ZN=锌)
        """
        if self.mock_mode:
            return self._mock_inventory(variety)
        
        if not self.available:
            return pd.DataFrame()
        
        try:
            # Wind库存代码
            symbol = f"{variety}库存量.SHFE"
            
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            result = self.w.wsd(symbol, "close", start_date, end_date, "")
            
            if result.ErrorCode != 0:
                return pd.DataFrame()
            
            df = pd.DataFrame({
                'inventory': result.Data[0]
            }, index=pd.to_datetime(result.Times))
            
            return df
            
        except Exception as e:
            print(f"Wind获取库存失败: {e}")
            return pd.DataFrame()
    
    def get_spot_price(self, variety: str = "铜") -> pd.DataFrame:
        """
        获取现货价格
        
        Args:
            variety: 品种名称 (铜、铝、锌等)
        """
        if self.mock_mode:
            return self._mock_spot_price(variety)
        
        if not self.available:
            return pd.DataFrame()
        
        try:
            # 长江有色现货价格
            symbol = f"{variety}现货价格(长江有色).SHF"
            
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            result = self.w.wsd(symbol, "close", start_date, end_date, "")
            
            if result.ErrorCode != 0:
                return pd.DataFrame()
            
            df = pd.DataFrame({
                'spot_price': result.Data[0]
            }, index=pd.to_datetime(result.Times))
            
            return df
            
        except Exception as e:
            print(f"Wind获取现货价格失败: {e}")
            return pd.DataFrame()
    
    def get_macro_data(self, indicator: str = "PMI") -> pd.DataFrame:
        """
        获取宏观数据
        
        Args:
            indicator: 指标名称
                - PMI: 制造业PMI
                - CPI: 消费者物价指数
                - PPI: 生产者物价指数
                - M1: M1货币供应
                - M2: M2货币供应
        """
        if self.mock_mode:
            return self._mock_macro_data(indicator)
        
        if not self.available:
            return pd.DataFrame()
        
        try:
            # Wind宏观指标代码映射
            indicator_map = {
                'PMI': 'M0000138',
                'CPI': 'M0000612',
                'PPI': 'M0000705',
                'M1': 'M0001383',
                'M2': 'M0001384'
            }
            
            code = indicator_map.get(indicator, indicator)
            
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365*2)).strftime("%Y-%m-%d")
            
            result = self.w.edb(code, start_date, end_date)
            
            if result.ErrorCode != 0:
                return pd.DataFrame()
            
            df = pd.DataFrame({
                indicator: result.Data[0]
            }, index=pd.to_datetime(result.Times))
            
            return df
            
        except Exception as e:
            print(f"Wind获取宏观数据失败: {e}")
            return pd.DataFrame()
    
    def get_fund_holdings(self, symbol: str = "CU") -> pd.DataFrame:
        """
        获取期货基金持仓 (CFTC)
        
        Args:
            symbol: 品种代码
        """
        if self.mock_mode:
            return self._mock_fund_holdings(symbol)
        
        if not self.available:
            return pd.DataFrame()
        
        try:
            # CFTC持仓数据
            result = self.w.wsd(f"{symbol}CFTC持仓.NYM",
                               "cftc_long,cftc_short,cftc_spread",
                               "", "", "")
            
            if result.ErrorCode != 0:
                return pd.DataFrame()
            
            df = pd.DataFrame({
                'long': result.Data[0],
                'short': result.Data[1],
                'spread': result.Data[2],
                'net_long': np.array(result.Data[0]) - np.array(result.Data[1])
            }, index=pd.to_datetime(result.Times))
            
            return df
            
        except Exception as e:
            print(f"Wind获取持仓数据失败: {e}")
            return pd.DataFrame()
    
    def get_options_data(self, underlying: str = "CU") -> pd.DataFrame:
        """
        获取期权数据 (波动率曲面、PCR等)
        
        Args:
            underlying: 标的代码
        """
        if self.mock_mode:
            return self._mock_options_data(underlying)
        
        if not self.available:
            return pd.DataFrame()
        
        # 期权数据需要更复杂的处理
        # 这里提供简化版本
        print("期权数据需要Wind专业版")
        return pd.DataFrame()
    
    # ========== 模拟数据生成 ==========
    
    def _mock_future_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟期货数据"""
        if start_date is None:
            start = datetime.now() - timedelta(days=365)
        else:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            
        if end_date is None:
            end = datetime.now()
        else:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        
        days = (end - start).days + 1
        dates = pd.date_range(start=start, periods=days, freq='D')
        
        # 基于真实价格特征生成模拟数据
        np.random.seed(hash(symbol) % 2**32)
        
        base_price = 70000 if 'CU' in symbol else 50000
        returns = np.random.randn(days) * 0.015
        trend = np.linspace(0, 0.05, days)
        
        prices = base_price * np.exp(np.cumsum(returns + trend))
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.randn(days) * 0.005),
            'high': prices * (1 + abs(np.random.randn(days)) * 0.008),
            'low': prices * (1 - abs(np.random.randn(days)) * 0.008),
            'close': prices,
            'volume': np.random.randint(50000, 150000, days),
            'amount': np.random.randint(5e8, 1.5e9, days),
            'open_interest': np.random.randint(100000, 200000, days)
        }, index=dates)
        
        return df
    
    def _mock_inventory(self, variety: str) -> pd.DataFrame:
        """生成模拟库存数据"""
        end = datetime.now()
        start = end - timedelta(days=365)
        days = (end - start).days + 1
        dates = pd.date_range(start=start, periods=days, freq='D')
        
        base_inv = 250000 if variety == 'CU' else 200000
        
        df = pd.DataFrame({
            'inventory': base_inv + np.cumsum(np.random.randn(days) * 500)
        }, index=dates)
        
        return df
    
    def _mock_spot_price(self, variety: str) -> pd.DataFrame:
        """生成模拟现货价格"""
        end = datetime.now()
        start = end - timedelta(days=365)
        days = (end - start).days + 1
        dates = pd.date_range(start=start, periods=days, freq='D')
        
        base_price = 70000 if variety == '铜' else 50000
        
        df = pd.DataFrame({
            'spot_price': base_price * (1 + np.cumsum(np.random.randn(days) * 0.001))
        }, index=dates)
        
        return df
    
    def _mock_macro_data(self, indicator: str) -> pd.DataFrame:
        """生成模拟宏观数据"""
        end = datetime.now()
        start = end - timedelta(days=365*2)
        
        # 月度数据
        dates = pd.date_range(start=start, end=end, freq='M')
        
        if indicator == 'PMI':
            values = 50 + np.random.randn(len(dates)) * 1.5
        elif indicator == 'CPI':
            values = 2 + np.random.randn(len(dates)) * 0.5
        elif indicator == 'PPI':
            values = np.random.randn(len(dates)) * 2
        elif indicator in ['M1', 'M2']:
            values = 8 + np.random.randn(len(dates)) * 2
        else:
            values = np.random.randn(len(dates))
        
        df = pd.DataFrame({
            indicator: values
        }, index=dates)
        
        return df
    
    def _mock_fund_holdings(self, symbol: str) -> pd.DataFrame:
        """生成模拟基金持仓数据"""
        end = datetime.now()
        start = end - timedelta(days=365)
        
        # 周度数据
        dates = pd.date_range(start=start, end=end, freq='W')
        
        base_long = 50000
        base_short = 30000
        
        df = pd.DataFrame({
            'long': base_long + np.cumsum(np.random.randn(len(dates)) * 1000),
            'short': base_short + np.cumsum(np.random.randn(len(dates)) * 500),
            'spread': np.random.randint(5000, 15000, len(dates))
        }, index=dates)
        
        df['net_long'] = df['long'] - df['short']
        
        return df
    
    def _mock_options_data(self, underlying: str) -> pd.DataFrame:
        """生成模拟期权数据"""
        end = datetime.now()
        start = end - timedelta(days=90)
        dates = pd.date_range(start=start, end=end, freq='D')
        
        df = pd.DataFrame({
            'iv_25delta_call': 0.2 + np.random.randn(len(dates)) * 0.02,
            'iv_25delta_put': 0.22 + np.random.randn(len(dates)) * 0.02,
            'iv_atm': 0.21 + np.random.randn(len(dates)) * 0.015,
            'pcr_volume': 0.8 + np.random.randn(len(dates)) * 0.1,
            'pcr_oi': 0.9 + np.random.randn(len(dates)) * 0.1
        }, index=dates)
        
        return df


# Wind数据管理器
class WindDataManager:
    """整合Wind多源数据"""
    
    def __init__(self, mock_mode: bool = True):
        self.wind = WindDataSource(mock_mode=mock_mode)
        self.cache = {}
    
    def get_full_dataset(self, days: int = 365) -> pd.DataFrame:
        """获取完整数据集"""
        print("\n[Wind数据] 获取完整数据集...")
        
        # 1. 期货价格
        print("  → 期货价格...")
        price_df = self.wind.get_future_daily("CU.SHF")
        
        if price_df.empty:
            print("  ✗ 价格数据为空")
            return pd.DataFrame()
        
        # 2. 库存数据
        print("  → 库存数据...")
        inv_df = self.wind.get_inventory("CU")
        if not inv_df.empty:
            inv_df = inv_df.reindex(price_df.index, method='ffill')
            price_df['inventory'] = inv_df['inventory']
        
        # 3. 现货价格
        print("  → 现货价格...")
        spot_df = self.wind.get_spot_price("铜")
        if not spot_df.empty:
            spot_df = spot_df.reindex(price_df.index, method='ffill')
            price_df['spot_price'] = spot_df['spot_price']
        
        # 4. 宏观数据
        print("  → 宏观数据...")
        pmi_df = self.wind.get_macro_data("PMI")
        if not pmi_df.empty:
            pmi_df = pmi_df.reindex(price_df.index, method='ffill')
            price_df['china_pmi'] = pmi_df['PMI']
        
        # 5. 持仓数据
        print("  → 持仓数据...")
        hold_df = self.wind.get_fund_holdings("CU")
        if not hold_df.empty:
            hold_df = hold_df.reindex(price_df.index, method='ffill')
            price_df = price_df.join(hold_df, how='left')
        
        print(f"✓ 数据获取完成: {len(price_df)} 条, {len(price_df.columns)} 字段")
        
        return price_df


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("Wind数据源测试")
    print("="*60)
    
    # 使用模拟模式
    wind = WindDataSource(mock_mode=True)
    
    # 1. 期货价格
    print("\n1. 期货价格数据")
    df = wind.get_future_daily("CU.SHF", days=30)
    print(f"   获取 {len(df)} 条记录")
    print(df.tail())
    
    # 2. 库存数据
    print("\n2. 库存数据")
    inv = wind.get_inventory("CU")
    print(f"   获取 {len(inv)} 条记录")
    print(inv.tail())
    
    # 3. 现货价格
    print("\n3. 现货价格")
    spot = wind.get_spot_price("铜")
    print(f"   获取 {len(spot)} 条记录")
    print(spot.tail())
    
    # 4. 宏观数据
    print("\n4. 宏观数据")
    pmi = wind.get_macro_data("PMI")
    print(f"   获取 {len(pmi)} 条记录")
    print(pmi.tail())
    
    # 5. 持仓数据
    print("\n5. 持仓数据")
    hold = wind.get_fund_holdings("CU")
    print(f"   获取 {len(hold)} 条记录")
    print(hold.tail())
    
    # 6. 完整数据集
    print("\n6. 完整数据集")
    manager = WindDataManager(mock_mode=True)
    full = manager.get_full_dataset(days=90)
    print(f"\n字段: {list(full.columns)}")
    print(full.tail())
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
