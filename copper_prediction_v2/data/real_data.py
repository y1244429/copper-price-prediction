"""
真实数据接入模块
支持: AKShare(免费)、Yahoo Finance、Web Scraping
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time
import warnings
warnings.filterwarnings('ignore')


class AKShareDataSource:
    """
    AKShare数据源 - 免费中文财经数据
    安装: pip install akshare
    文档: https://www.akshare.xyz/
    """
    
    def __init__(self):
        self.ak = None
        self.available = False
        self._init()
    
    def _init(self):
        """初始化AKShare"""
        try:
            import akshare as ak
            self.ak = ak
            self.available = True
            print("✓ AKShare已加载")
        except ImportError:
            print("✗ AKShare未安装: pip install akshare")
    
    def get_futures_daily(self, symbol: str = "CU0", 
                         start_date: str = None, 
                         end_date: str = None) -> pd.DataFrame:
        """
        获取期货日线数据
        
        symbol: 合约代码
            - CU0: 沪铜连续
            - AL0: 沪铝连续
            - ZN0: 沪锌连续
            - SN0: 沪锡连续
            - AU0: 沪金连续
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            # 获取期货历史数据
            df = self.ak.futures_zh_daily_sina(symbol=symbol)
            
            # 转换日期为索引
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 重命名列以匹配系统
            df = df.rename(columns={
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            # 日期筛选
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]
            
            # 确保数值类型
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df.sort_index()
            
        except Exception as e:
            print(f"获取期货数据失败: {e}")
            return pd.DataFrame()
    
    def get_shfe_inventory(self) -> pd.DataFrame:
        """获取上期所库存数据"""
        if not self.available:
            return pd.DataFrame()
        
        try:
            # 获取期货库存数据
            df = self.ak.futures_inventory_99(symbol="cu")
            
            df = df.rename(columns={
                'date': 'date',
                'inventory': 'shfe_inventory'
            })
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df.sort_index()
            
        except Exception as e:
            print(f"获取库存数据失败: {e}")
            return pd.DataFrame()
    
    def get_macro_pmi(self) -> pd.DataFrame:
        """获取中国制造业PMI"""
        if not self.available:
            return pd.DataFrame()
        
        try:
            df = self.ak.macro_china_pmi()
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df = df.rename(columns={'value': 'china_pmi'})
            return df.sort_index()
            
        except Exception as e:
            print(f"获取PMI数据失败: {e}")
            return pd.DataFrame()
    
    def get_macro_cpi(self) -> pd.DataFrame:
        """获取CPI数据"""
        if not self.available:
            return pd.DataFrame()
        
        try:
            df = self.ak.macro_china_cpi()
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df.sort_index()
            
        except Exception as e:
            print(f"获取CPI数据失败: {e}")
            return pd.DataFrame()
    
    def get_usd_cny_exchange_rate(self) -> pd.DataFrame:
        """获取美元兑人民币汇率"""
        if not self.available:
            return pd.DataFrame()
        
        try:
            df = self.ak.currency_boc_safe(symbol='USD')
            df = df.rename(columns={
                '中间价': 'usd_cny',
                '日期': 'date'
            })
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df.sort_index()
            
        except Exception as e:
            print(f"获取汇率数据失败: {e}")
            return pd.DataFrame()
    
    def get_spot_price_smm(self) -> pd.DataFrame:
        """
        获取上海有色网(SMM)现货价格
        需要额外的cookie或token
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            # SMM铜现货价格
            df = self.ak.futures_sgx_daily(symbol="CU", exchange="smm")
            return df
        except Exception as e:
            print(f"获取SMM数据失败: {e}")
            return pd.DataFrame()


class YahooFinanceDataSource:
    """
    Yahoo Finance数据源 - 国际商品数据
    安装: pip install yfinance
    """
    
    def __init__(self):
        self.yf = None
        self.available = False
        self._init()
    
    def _init(self):
        """初始化yfinance"""
        try:
            import yfinance as yf
            self.yf = yf
            self.available = True
            print("✓ Yahoo Finance已加载")
        except ImportError:
            print("✗ yfinance未安装: pip install yfinance")
    
    def get_copper_price(self, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        获取铜期货数据
        
        HG=F: 美铜连续期货 (COMEX Copper)
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            # 下载铜期货数据
            ticker = self.yf.Ticker("HG=F")
            df = ticker.history(period=period, interval=interval)
            
            # 重命名列
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 去除时区
            df.index = df.index.tz_localize(None)
            
            return df
            
        except Exception as e:
            print(f"获取Yahoo数据失败: {e}")
            return pd.DataFrame()
    
    def get_dollar_index(self, period: str = "1y") -> pd.DataFrame:
        """
        获取美元指数
        DX-Y.NYB: 美元指数期货
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            ticker = self.yf.Ticker("DX-Y.NYB")
            df = ticker.history(period=period)
            
            df = df.rename(columns={'Close': 'dollar_index'})
            df.index = df.index.tz_localize(None)
            
            return df[['dollar_index']]
            
        except Exception as e:
            print(f"获取美元指数失败: {e}")
            return pd.DataFrame()
    
    def get_gold_price(self, period: str = "1y") -> pd.DataFrame:
        """获取黄金价格 (铜金比参考)"""
        if not self.available:
            return pd.DataFrame()
        
        try:
            ticker = self.yf.Ticker("GC=F")
            df = ticker.history(period=period)
            
            df = df.rename(columns={'Close': 'gold_price'})
            df.index = df.index.tz_localize(None)
            
            return df[['gold_price']]
            
        except Exception as e:
            print(f"获取黄金价格失败: {e}")
            return pd.DataFrame()
    
    def get_copper_etf(self, period: str = "1y") -> pd.DataFrame:
        """
        获取铜ETF数据 (投资情绪指标)
        
        CPER: United States Copper Index Fund
        JJC: iPath Series B Bloomberg Copper Subindex Total Return ETN
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            ticker = self.yf.Ticker("CPER")
            df = ticker.history(period=period)
            
            df = df.rename(columns={
                'Close': 'etf_close',
                'Volume': 'etf_volume'
            })
            df.index = df.index.tz_localize(None)
            
            return df[['etf_close', 'etf_volume']]
            
        except Exception as e:
            print(f"获取ETF数据失败: {e}")
            return pd.DataFrame()


class WebScrapingDataSource:
    """
    网页抓取数据源 - 备用方案
    从公开网站抓取数据
    """
    
    def __init__(self):
        self.session = None
        try:
            import requests
            from bs4 import BeautifulSoup
            self.requests = requests
            self.bs4 = BeautifulSoup
            self.available = True
        except ImportError:
            self.available = False
            print("网页抓取需要: pip install requests beautifulsoup4")
    
    def get_smm_price(self) -> Optional[Dict]:
        """
        获取SMM现货报价
        注意: 网站结构可能变化，需要定期更新selector
        """
        if not self.available:
            return None
        
        try:
            url = "https://www.smm.cn/copper"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.requests.get(url, headers=headers, timeout=10)
            soup = self.bs4(response.content, 'html.parser')
            
            # 这里需要根据实际网页结构编写解析逻辑
            # 示例返回
            return {
                'spot_price': None,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'SMM'
            }
            
        except Exception as e:
            print(f"抓取SMM数据失败: {e}")
            return None


class RealDataManager:
    """
    真实数据管理器 - 整合多源数据
    """
    
    def __init__(self):
        self.ak = AKShareDataSource()
        self.yahoo = YahooFinanceDataSource()
        self.web = WebScrapingDataSource()
        
        # 数据缓存
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 3600  # 1小时缓存
    
    def get_full_data(self, days: int = 365, use_cache: bool = True) -> pd.DataFrame:
        """
        获取完整数据集
        
        优先级:
        1. 国内数据: AKShare
        2. 国际数据: Yahoo Finance
        3. 补充数据: Web Scraping
        """
        cache_key = f"full_data_{days}"
        
        # 检查缓存
        if use_cache and cache_key in self.cache:
            if time.time() - self.cache_time.get(cache_key, 0) < self.cache_duration:
                print("使用缓存数据")
                return self.cache[cache_key]
        
        print("\n[数据获取] 从多个源获取数据...")
        
        # 1. 获取期货价格 (优先AKShare)
        df = pd.DataFrame()
        
        if self.ak.available:
            try:
                print("  → 从AKShare获取沪铜数据...")
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                df = self.ak.get_futures_daily(
                    symbol="CU0",
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d")
                )
            except Exception as e:
                print(f"  AKShare获取失败: {e}")
        
        # 如果AKShare失败，使用Yahoo Finance
        if df.empty and self.yahoo.available:
            try:
                print("  → 从Yahoo Finance获取美铜数据...")
                df = self.yahoo.get_copper_price(period=f"{days}d")
                # 转换价格单位 (美元/磅 → 元/吨)
                df['close'] = df['close'] * 2204.62 * 7.2
                df['open'] = df['open'] * 2204.62 * 7.2
                df['high'] = df['high'] * 2204.62 * 7.2
                df['low'] = df['low'] * 2204.62 * 7.2
            except Exception as e:
                print(f"  Yahoo获取失败: {e}")
        
        if df.empty:
            return df
        
        # 2. 添加宏观数据
        print("  → 添加宏观数据...")
        
        if self.ak.available:
            try:
                # 添加PMI
                pmi_df = self.ak.get_macro_pmi()
                if not pmi_df.empty:
                    pmi_df = pmi_df.reindex(df.index, method='ffill')
                    df['china_pmi'] = pmi_df['china_pmi']
            except Exception as e:
                print(f"    PMI获取失败: {e}")
        
        if self.yahoo.available:
            try:
                # 添加美元指数
                dollar_df = self.yahoo.get_dollar_index(period=f"{days}d")
                if not dollar_df.empty:
                    dollar_df = dollar_df.reindex(df.index, method='ffill')
                    df['dollar_index'] = dollar_df['dollar_index']
            except Exception as e:
                print(f"    美元指数获取失败: {e}")
        
        # 3. 添加库存数据
        print("  → 添加库存数据...")
        
        if self.ak.available:
            try:
                inv_df = self.ak.get_shfe_inventory()
                if not inv_df.empty:
                    inv_df = inv_df.reindex(df.index, method='ffill')
                    df['shfe_inventory'] = inv_df['shfe_inventory']
            except Exception as e:
                print(f"    库存获取失败: {e}")
        
        # 填充缺失值
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # 保存缓存
        self.cache[cache_key] = df
        self.cache_time[cache_key] = time.time()
        
        print(f"✓ 数据获取完成: {len(df)} 条记录, {len(df.columns)} 个字段")
        
        return df
    
    def get_realtime_price(self) -> Dict:
        """获取实时价格"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        # AKShare实时数据
        if self.ak.available:
            try:
                df = self.ak.get_futures_daily(symbol="CU0")
                if not df.empty:
                    latest = df.iloc[-1]
                    result['sources']['akshare'] = {
                        'price': float(latest['close']),
                        'change': float(latest.get('change', 0)),
                        'volume': float(latest.get('volume', 0))
                    }
            except Exception as e:
                result['sources']['akshare'] = {'error': str(e)}
        
        # Yahoo Finance实时数据
        if self.yahoo.available:
            try:
                df = self.yahoo.get_copper_price(period="5d", interval="1m")
                if not df.empty:
                    latest = df.iloc[-1]
                    result['sources']['yahoo'] = {
                        'price': float(latest['close']),
                        'volume': float(latest.get('volume', 0))
                    }
            except Exception as e:
                result['sources']['yahoo'] = {'error': str(e)}
        
        return result
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        self.cache_time.clear()
        print("缓存已清除")


# 便捷函数
def get_data_source(source_type: str = "auto"):
    """
    获取数据源
    
    source_type: 'auto', 'akshare', 'yahoo', 'mock'
    """
    if source_type == "auto":
        manager = RealDataManager()
        if manager.ak.available or manager.yahoo.available:
            return manager
        else:
            print("真实数据源不可用，回退到模拟数据")
            from data.data_sources import MockDataSource
            return MockDataSource()
    elif source_type == "akshare":
        return AKShareDataSource()
    elif source_type == "yahoo":
        return YahooFinanceDataSource()
    else:
        from data.data_sources import MockDataSource
        return MockDataSource()


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("真实数据接入测试")
    print("="*60)
    
    # 创建数据管理器
    manager = RealDataManager()
    
    # 检查可用数据源
    print("\n数据源状态:")
    print(f"  AKShare: {'✓ 可用' if manager.ak.available else '✗ 不可用'}")
    print(f"  Yahoo Finance: {'✓ 可用' if manager.yahoo.available else '✗ 不可用'}")
    print(f"  Web Scraping: {'✓ 可用' if manager.web.available else '✗ 不可用'}")
    
    # 获取完整数据
    print("\n获取历史数据...")
    df = manager.get_full_data(days=90)
    
    if not df.empty:
        print(f"\n数据概览:")
        print(f"  记录数: {len(df)}")
        print(f"  字段: {list(df.columns)}")
        print(f"\n最近5天数据:")
        print(df.tail())
        
        # 实时价格
        print("\n实时价格:")
        realtime = manager.get_realtime_price()
        print(realtime)
    else:
        print("\n✗ 无法获取数据，请检查网络或安装依赖")
        print("  pip install akshare yfinance")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
