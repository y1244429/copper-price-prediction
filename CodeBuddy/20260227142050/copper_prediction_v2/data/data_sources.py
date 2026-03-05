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
            print("✅ AKShare 已安装，将使用真实数据")
        except ImportError:
            self.available = False
            print("⚠️  AKShare 未安装，将使用模拟数据")

    def fetch_copper_price(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        从AKShare获取铜价数据（支持多种数据源）

        Args:
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)

        Returns:
            包含OHLCV数据的DataFrame
        """
        if not self.available:
            raise ImportError("AKShare未安装，请运行: pip install akshare")

        try:
            import akshare as ak
            import warnings
            warnings.filterwarnings('ignore')

            print(f"正在从AKShare获取铜价数据 ({start_date} 至 {end_date})...")

            # 尝试多个数据源 - 优先使用中国上期所数据
            data_sources = [
                ("上期所铜期货（主力）", self._fetch_shfe_copper),
                ("备用铜期货数据", self._fetch_copper_fallback)
            ]

            for source_name, fetch_func in data_sources:
                try:
                    print(f"  尝试数据源: {source_name}")
                    df = fetch_func(start_date, end_date)

                    if df is not None and len(df) > 0:
                        print(f"✅ {source_name}成功获取 {len(df)} 条数据")
                        return df

                except Exception as e:
                    print(f"  ⚠️  {source_name}失败: {e}")
                    continue

            # 所有数据源都失败
            raise Exception("所有数据源均无法获取数据")

        except Exception as e:
            print(f"❌ AKShare数据获取失败: {e}")
            raise

    def _fetch_shfe_copper(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取上期所铜期货数据"""
        import akshare as ak

        try:
            # 获取上海期货交易所铜期货主力合约数据
            df = ak.futures_zh_daily_sina(symbol="CU0")
            return self._standardize_copper_data(df, start_date, end_date)
        except:
            raise Exception("上期所数据获取失败")

    def _fetch_comex_copper(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取COMEX铜期货数据"""
        import akshare as ak

        try:
            # 尝试获取COMEX铜期货数据（通过新浪期货）
            # COMEX铜在新浪期货的代码通常是 HG0（铜主力合约）
            try:
                df = ak.futures_zh_daily_sina(symbol="HG0")
                return self._standardize_copper_data(df, start_date, end_date)
            except:
                # 尝试其他可能的代码
                for symbol in ["HG8890", "HG", "COMEX_HG"]:
                    try:
                        df = ak.futures_zh_daily_sina(symbol=symbol)
                        return self._standardize_copper_data(df, start_date, end_date)
                    except:
                        continue
                raise Exception("COMEX数据获取失败")
        except:
            raise Exception("COMEX数据获取失败")

    def _fetch_lme_copper(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取伦敦金属交易所铜数据"""
        import akshare as ak

        try:
            # 尝试获取LME铜数据
            try:
                df = ak.futures_zh_daily_sina(symbol="LME_CU")
                return self._standardize_copper_data(df, start_date, end_date)
            except:
                raise Exception("LME数据获取失败")
        except:
            raise Exception("LME数据获取失败")

    def _standardize_copper_data(self, df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """标准化铜价数据格式"""
        if df is None or len(df) == 0:
            raise Exception("数据为空")

        # 确保有日期列
        if 'date' in df.columns:
            df.index = pd.to_datetime(df['date'])
            df = df.drop('date', axis=1)
        elif 'trade_date' in df.columns:
            df.index = pd.to_datetime(df['trade_date'])
            df = df.drop('trade_date', axis=1)
        elif not isinstance(df.index, pd.DatetimeIndex):
            # 尝试将索引转换为日期
            try:
                df.index = pd.to_datetime(df.index)
            except:
                raise Exception("无法解析日期索引")

        # 标准化列名
        column_map = {
            'OPEN': 'open',
            'HIGH': 'high',
            'LOW': 'low',
            'CLOSE': 'close',
            'VOLUME': 'volume',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        }
        df = df.rename(columns=column_map)

        # 确保必要的列存在
        required_columns = ['open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"⚠️  数据缺少列: {missing_columns}")
            raise Exception(f"数据缺少必要列: {missing_columns}")

        # 添加成交额
        if 'volume' not in df.columns:
            df['volume'] = 0

        if 'volume' in df.columns and 'close' in df.columns:
            df['turnover'] = df['close'] * df['volume']

        # 添加VWAP
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            df['vwap'] = (df['high'] + df['low'] + 2 * df['close']) / 4

        # 筛选日期范围
        df = df[(df.index >= start_date) & (df.index <= end_date)]

        # 按日期排序
        df = df.sort_index()

        # 删除重复行
        df = df[~df.index.duplicated(keep='last')]

        return df

    def _fetch_copper_fallback(self, start_date: str, end_date: str) -> pd.DataFrame:
        """备用数据获取方法"""
        import akshare as ak

        # 尝试多个备用数据源
        fallback_sources = [
            "LME_CU",
            "CU8888",
            "CU2406",  # 特定期货合约
            "CU2407"
        ]

        for symbol in fallback_sources:
            try:
                df = ak.futures_zh_daily_sina(symbol=symbol)
                return self._standardize_copper_data(df, start_date, end_date)
            except:
                continue

        raise Exception(f"所有备用数据源均失败")

    def fetch_macro_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        从AKShare获取宏观经济数据

        Args:
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)

        Returns:
            包含宏观数据的DataFrame，包括：
                - pmi: 中国制造业PMI
                - pmi_caixin: 财新中国制造业PMI
                - usd_cny: 美元兑人民币汇率
                - dxy: 美元指数（如果可用）
        """
        if not self.available:
            raise ImportError("AKShare未安装")

        try:
            import akshare as ak
            import warnings
            warnings.filterwarnings('ignore')

            print(f"正在从AKShare获取宏观数据 ({start_date} 至 {end_date})...")

            # 初始化DataFrame
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            df = pd.DataFrame(index=date_range)

            # 1. 获取中国制造业PMI（官方）
            print("  [1/3] 获取中国制造业PMI...")
            try:
                pmi = ak.macro_china_pmi()
                if not pmi.empty:
                    print(f"    PMI数据列: {list(pmi.columns)}")
                    print(f"    PMI数据形状: {pmi.shape}")

                    # 标准化列名
                    if '制造业-指数' in pmi.columns:
                        pmi_data = pmi[['月份', '制造业-指数']].copy()
                        pmi_data.columns = ['date', 'pmi']
                    elif '制造业PMI' in pmi.columns:
                        pmi_data = pmi[['月份', '制造业PMI']].copy()
                        pmi_data.columns = ['date', 'pmi']
                    else:
                        # 使用第一列和第二列
                        pmi_data = pmi.iloc[:, [0, 1]].copy()
                        pmi_data.columns = ['date', 'pmi']

                    # 处理中文日期格式 (如 "2026年01月份")
                    def parse_chinese_date(date_str):
                        import re
                        match = re.match(r'(\d{4})年(\d{1,2})月份?', str(date_str))
                        if match:
                            year = match.group(1)
                            month = match.group(2).zfill(2)
                            return pd.to_datetime(f"{year}-{month}-01")
                        return pd.to_datetime(date_str)

                    pmi_data['date'] = pmi_data['date'].apply(parse_chinese_date)
                    pmi_data.index = pmi_data['date']
                    pmi_data = pmi_data[['pmi']]

                    # 前向填充到日频
                    df['pmi'] = pmi_data['pmi'].reindex(df.index, method='ffill')
                    print(f"    ✅ PMI获取成功，最新值: {df['pmi'].iloc[-1]:.2f}")
                else:
                    df['pmi'] = 50.5
                    print(f"    ⚠️  PMI为空，使用默认值")
            except Exception as e:
                print(f"    ⚠️  PMI获取失败: {e}，使用默认值")
                import traceback
                traceback.print_exc()
                df['pmi'] = 50.5

            # 2. 获取财新PMI
            print("  [2/3] 获取财新制造业PMI...")
            try:
                pmi_caixin = ak.index_pmi_man_cx()
                if not pmi_caixin.empty:
                    print(f"    财新PMI数据列: {list(pmi_caixin.columns)}")
                    print(f"    财新PMI数据形状: {pmi_caixin.shape}")

                    # 标准化列名
                    pmi_caixin_columns = {
                        '财新中国制造业PMI': 'pmi_caixin',
                        '财新制造业PMI': 'pmi_caixin',
                        'PMI': 'pmi_caixin',
                        '月份': 'date'
                    }
                    pmi_caixin = pmi_caixin.rename(columns=pmi_caixin_columns)

                    # 处理日期
                    if 'date' in pmi_caixin.columns:
                        pmi_caixin.index = pd.to_datetime(pmi_caixin['date'])
                        pmi_caixin = pmi_caixin[['pmi_caixin']]
                    elif '月份' in pmi_caixin.columns:
                        pmi_caixin.index = pd.to_datetime(pmi_caixin['月份'])
                        pmi_caixin = pmi_caixin[['pmi_caixin']]
                    else:
                        pmi_caixin.index = pd.to_datetime(pmi_caixin.iloc[:, 0])
                        pmi_caixin = pmi_caixin.iloc[:, [1]]
                        pmi_caixin.columns = ['pmi_caixin']

                    # 前向填充到日频
                    df['pmi_caixin'] = pmi_caixin['pmi_caixin'].reindex(df.index, method='ffill')
                    print(f"    ✅ 财新PMI获取成功，最新值: {df['pmi_caixin'].iloc[-1]:.2f}")
                else:
                    df['pmi_caixin'] = 50.5
                    print(f"    ⚠️  财新PMI为空，使用默认值")
            except Exception as e:
                print(f"    ⚠️  财新PMI获取失败: {e}，使用默认值")
                import traceback
                traceback.print_exc()
                df['pmi_caixin'] = 50.5

            # 3. 获取美元兑人民币汇率
            print("  [3/3] 获取美元兑人民币汇率...")
            try:
                # 尝试获取汇率数据
                usd_cny = ak.fx_spot_quote()
                if not usd_cny.empty:
                    print(f"    汇率数据列: {list(usd_cny.columns)}")
                    print(f"    汇率数据形状: {usd_cny.shape}")

                    # 查找美元兑人民币的汇率
                    latest_rate = None
                    if '货币对' in usd_cny.columns:
                        # 查找包含美元/人民币的行
                        usd_cny_row = usd_cny[usd_cny['货币对'].str.contains('美元|USD|USDCNY', case=False, na=False)]
                        if not usd_cny_row.empty:
                            if '买报价' in usd_cny_row.columns:
                                latest_rate = usd_cny_row['买报价'].iloc[0]
                            elif '卖报价' in usd_cny_row.columns:
                                latest_rate = usd_cny_row['卖报价'].iloc[0]
                            elif len(usd_cny_row.columns) > 1:
                                latest_rate = usd_cny_row.iloc[0, 1]
                                print(f"    找到汇率行，值: {latest_rate}")

                    if latest_rate is None:
                        # 备用：查看所有货币对
                        print(f"    所有货币对: {usd_cny['货币对'].tolist()}")
                        # 尝试第一行
                        if len(usd_cny.columns) > 1 and len(usd_cny) > 0:
                            latest_rate = usd_cny.iloc[0, 1]
                            print(f"    使用第一行汇率: {latest_rate}")

                    # 尝试转换为浮点数
                    if latest_rate is not None:
                        try:
                            latest_rate = float(str(latest_rate).replace(',', '').strip())
                            if latest_rate > 0:
                                df['usd_cny'] = latest_rate
                                print(f"    ✅ 美元兑人民币汇率获取成功: {df['usd_cny'].iloc[-1]:.4f}")
                            else:
                                df['usd_cny'] = 7.2
                                print(f"    ⚠️  汇率值异常，使用默认值")
                        except Exception as convert_error:
                            print(f"    ⚠️  汇率值转换失败: {convert_error}，使用默认值")
                            df['usd_cny'] = 7.2
                    else:
                        df['usd_cny'] = 7.2
                        print(f"    ⚠️  未找到美元兑人民币汇率，使用默认值")
                else:
                    df['usd_cny'] = 7.2
                    print(f"    ⚠️  汇率为空，使用默认值")
            except Exception as e:
                print(f"    ⚠️  汇率获取失败: {e}，使用默认值")
                import traceback
                traceback.print_exc()
                df['usd_cny'] = 7.2

            # 填充缺失值
            df = df.fillna(method='ffill').fillna(method='bfill')

            print(f"✅ 宏观数据获取成功，共 {len(df)} 条记录")

            return df

        except Exception as e:
            print(f"❌ 宏观数据获取失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回默认宏观数据
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            df = pd.DataFrame({
                'pmi': 50.5,
                'pmi_caixin': 50.5,
                'usd_cny': 7.2
            }, index=date_range)
            print(f"✅ 使用默认宏观数据")
            return df


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
