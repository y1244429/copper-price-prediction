"""
增强数据源模块 - 实时宏观、资金流向、新闻情绪
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedMacroData:
    """实时宏观数据获取"""

    def __init__(self):
        self.api_key = "6D092BQN6LS3J2D7"  # Alpha Vantage API Key

    def get_dollar_index_realtime(self) -> Dict:
        """
        获取实时美元指数
        数据源: Alpha Vantage API (USD/JPY汇率作为美元指数代理)
        """
        try:
            # 使用 Alpha Vantage API 获取USD/JPY汇率作为美元指数代理
            # USD/JPY汇率升高表示美元走强,可以反映美元指数趋势
            url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=USD&to_symbol=JPY&apikey={self.api_key}"

            response = requests.get(url, timeout=10)
            data = response.json()

            if 'Time Series FX (Daily)' in data:
                time_series = data['Time Series FX (Daily)']
                latest_date = list(time_series.keys())[0]
                latest_value = float(time_series[latest_date]['4. close'])

                # 将USD/JPY汇率转换为美元指数风格
                # 基准: USD/JPY 150 ≈ 美元指数 100
                dollar_index = (latest_value / 150) * 100

                logger.info(f"✓ 获取美元指数 (Alpha Vantage USD/JPY): {dollar_index:.2f}")
                return {
                    'timestamp': datetime.now(),
                    'value': round(dollar_index, 2),
                    'source': 'Alpha Vantage (USD/JPY汇率)',
                    'date': latest_date
                }

            # 模拟数据（如果API失败）
            return self._get_mock_dollar_index()

        except Exception as e:
            logger.error(f"获取美元指数失败: {e}")
            return self._get_mock_dollar_index()
    
    def _get_mock_dollar_index(self) -> Dict:
        """模拟美元指数数据"""
        np.random.seed(int(datetime.now().timestamp()))
        base_value = 98.97
        variation = np.random.normal(0, 0.2)
        return {
            'timestamp': datetime.now(),
            'value': round(base_value + variation, 2),
            'source': 'Mock Data',
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def get_pmi_latest(self) -> Dict:
        """
        获取最新PMI数据
        数据源: FRED API (ISM PMI, Markit PMI)
        """
        try:
            # ISM 制造业PMI
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=NAPM&api_key={self.api_key}&file_type=json&limit=1"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][0]
                value = float(obs['value']) if obs['value'] != '.' else None
                
                return {
                    'timestamp': datetime.now(),
                    'value': value,
                    'date': obs['date'],
                    'source': 'FRED (ISM PMI)',
                    'type': 'Manufacturing PMI'
                }
            
            return self._get_mock_pmi()
            
        except Exception as e:
            logger.error(f"获取PMI数据失败: {e}")
            return self._get_mock_pmi()
    
    def _get_mock_pmi(self) -> Dict:
        """模拟PMI数据"""
        base_value = 54.04
        variation = np.random.normal(0, 0.5)
        return {
            'timestamp': datetime.now(),
            'value': round(base_value + variation, 1),
            'date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            'source': 'Mock Data',
            'type': 'Manufacturing PMI'
        }
    
    def get_interest_rate_realtime(self) -> Dict:
        """
        获取实时利率数据
        数据源: FRED API (Federal Funds Rate, 10-Year Treasury)
        """
        try:
            # 联邦基金利率
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={self.api_key}&file_type=json&limit=1"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][0]
                value = float(obs['value']) if obs['value'] != '.' else None
                
                return {
                    'timestamp': datetime.now(),
                    'federal_funds_rate': value,
                    'date': obs['date'],
                    'source': 'FRED',
                    'type': 'Federal Funds Rate'
                }
            
            return self._get_mock_interest_rate()
            
        except Exception as e:
            logger.error(f"获取利率数据失败: {e}")
            return self._get_mock_interest_rate()
    
    def _get_mock_interest_rate(self) -> Dict:
        """模拟利率数据"""
        base_value = 5.25  # 当前美联储利率
        return {
            'timestamp': datetime.now(),
            'federal_funds_rate': base_value,
            'date': datetime.now().strftime('%Y-%m'),
            'source': 'Mock Data',
            'type': 'Federal Funds Rate'
        }
    
    def get_vix_realtime(self) -> Dict:
        """
        获取实时VIX恐慌指数
        数据源: Alpha Vantage 或 Yahoo Finance
        """
        try:
            # 使用 Alpha Vantage
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=VIX&apikey={self.api_key}"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                latest_date = list(time_series.keys())[0]
                latest_value = float(time_series[latest_date]['4. close'])
                
                return {
                    'timestamp': datetime.now(),
                    'value': latest_value,
                    'date': latest_date,
                    'source': 'Alpha Vantage',
                    'type': 'VIX Index'
                }
            
            return self._get_mock_vix()
            
        except Exception as e:
            logger.error(f"获取VIX数据失败: {e}")
            return self._get_mock_vix()
    
    def _get_mock_vix(self) -> Dict:
        """模拟VIX数据"""
        base_value = 18.5
        variation = np.random.normal(0, 1.0)
        return {
            'timestamp': datetime.now(),
            'value': round(base_value + variation, 1),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'source': 'Mock Data',
            'type': 'VIX Index'
        }
    
    def get_all_macro_data(self) -> Dict:
        """获取所有宏观数据"""
        return {
            'dollar_index': self.get_dollar_index_realtime(),
            'pmi': self.get_pmi_latest(),
            'interest_rate': self.get_interest_rate_realtime(),
            'vix': self.get_vix_realtime(),
            'fetch_time': datetime.now()
        }


class CapitalFlowData:
    """资金流向数据获取"""
    
    def __init__(self):
        self.api_key = "YOUR_API_KEY"
    
    def get_cftc_report(self) -> Dict:
        """
        获取CFTC持仓报告
        数据源: CFTC 官方API 或第三方数据源
        """
        try:
            # CFTC 数据需要从官方网站下载
            # 这里使用模拟数据
            return self._get_mock_cftc_report()
            
        except Exception as e:
            logger.error(f"获取CFTC报告失败: {e}")
            return self._get_mock_cftc_report()
    
    def _get_mock_cftc_report(self) -> Dict:
        """模拟CFTC持仓报告"""
        np.random.seed(int(datetime.now().timestamp()))
        
        # 商业头寸
        commercial_long = np.random.randint(150000, 180000)
        commercial_short = np.random.randint(180000, 220000)
        
        # 投机头寸
        speculative_long = np.random.randint(80000, 120000)
        speculative_short = np.random.randint(60000, 90000)
        
        # 净头寸
        net_commercial = commercial_long - commercial_short
        net_speculative = speculative_long - speculative_short
        
        return {
            'timestamp': datetime.now(),
            'report_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'commercial': {
                'long': commercial_long,
                'short': commercial_short,
                'net': net_commercial
            },
            'speculative': {
                'long': speculative_long,
                'short': speculative_short,
                'net': net_speculative
            },
            'commercial_net_ratio': net_commercial / commercial_long,
            'speculative_net_ratio': net_speculative / speculative_long,
            'source': 'Mock CFTC Data'
        }
    
    def get_futures_open_interest(self, days: int = 30) -> pd.DataFrame:
        """
        获取期货持仓量数据
        数据源: 交易所API (SHFE, LME, COMEX)
        """
        try:
            # 使用模拟数据
            dates = pd.date_range(end=datetime.now(), periods=days)
            
            # 模拟持仓量数据
            base_oi = 500000
            oi_values = []
            
            for i, date in enumerate(dates):
                variation = np.random.normal(0, 5000)
                oi = base_oi + variation + i * 100  # 轻微趋势
                oi_values.append(int(oi))
            
            df = pd.DataFrame({
                'date': dates,
                'open_interest': oi_values,
                'long_position': [int(v * 0.52) for v in oi_values],
                'short_position': [int(v * 0.48) for v in oi_values],
                'net_position': [int(v * 0.04) for v in oi_values]
            })
            
            return df
            
        except Exception as e:
            logger.error(f"获取期货持仓量失败: {e}")
            return pd.DataFrame()
    
    def get_volume_distribution(self) -> Dict:
        """
        获取成交量分布（分时数据）
        数据源: 交易所API
        """
        try:
            # 模拟分时成交量
            time_slots = ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00']
            volumes = []
            
            base_volume = 100000
            for i, time_slot in enumerate(time_slots):
                # 早盘和尾盘成交量较大
                if i < 2 or i >= 4:
                    volume = base_volume * np.random.uniform(1.2, 1.5)
                else:
                    volume = base_volume * np.random.uniform(0.6, 0.9)
                volumes.append(int(volume))
            
            return {
                'timestamp': datetime.now(),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time_slots': time_slots,
                'volumes': volumes,
                'total_volume': sum(volumes),
                'volume_peak_time': time_slots[volumes.index(max(volumes))],
                'source': 'Mock Data'
            }
            
        except Exception as e:
            logger.error(f"获取成交量分布失败: {e}")
            return {}
    
    def get_all_capital_flow_data(self) -> Dict:
        """获取所有资金流向数据"""
        return {
            'cftc': self.get_cftc_report(),
            'open_interest': self.get_futures_open_interest(),
            'volume_distribution': self.get_volume_distribution(),
            'fetch_time': datetime.now()
        }


class NewsSentimentAnalyzer:
    """新闻情绪分析"""
    
    def __init__(self):
        self.news_sources = [
            'https://finance.sina.com.cn',
            'https://www.cnbc.com',
            'https://www.bloomberg.com',
            'https://www.reuters.com'
        ]
        
    def fetch_financial_news(self, num_articles: int = 10) -> List[Dict]:
        """
        爬取财经新闻
        """
        try:
            # 模拟新闻数据
            news_list = [
                {
                    'title': '美联储暗示可能暂停加息进程',
                    'url': 'https://example.com/news/1',
                    'source': 'Reuters',
                    'timestamp': datetime.now() - timedelta(hours=2),
                    'sentiment': 'neutral'
                },
                {
                    'title': '中国制造业PMI超预期增长至54.5',
                    'url': 'https://example.com/news/2',
                    'source': 'CNBC',
                    'timestamp': datetime.now() - timedelta(hours=4),
                    'sentiment': 'positive'
                },
                {
                    'title': '地缘政治紧张局势加剧，市场避险情绪升温',
                    'url': 'https://example.com/news/3',
                    'source': 'Bloomberg',
                    'timestamp': datetime.now() - timedelta(hours=6),
                    'sentiment': 'negative'
                },
                {
                    'title': 'LME铜库存周度下降1.2万吨',
                    'url': 'https://example.com/news/4',
                    'source': 'LME',
                    'timestamp': datetime.now() - timedelta(hours=8),
                    'sentiment': 'positive'
                },
                {
                    'title': '美元指数走强，大宗商品承压',
                    'url': 'https://example.com/news/5',
                    'source': 'Reuters',
                    'timestamp': datetime.now() - timedelta(hours=12),
                    'sentiment': 'negative'
                }
            ]
            
            return news_list[:num_articles]
            
        except Exception as e:
            logger.error(f"爬取新闻失败: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        使用NLP分析情绪
        """
        # 简单情绪分析（实际应使用BERT或专门的NLP模型）
        positive_words = ['增长', '上涨', '利好', '超预期', '反弹', '恢复', '强劲', '乐观']
        negative_words = ['下跌', '暴跌', '利空', '不及预期', '承压', '放缓', '悲观', '风险', '紧张']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        total = positive_count + negative_count
        
        if total == 0:
            sentiment_score = 0
            sentiment = 'neutral'
        else:
            sentiment_score = (positive_count - negative_count) / total
            if sentiment_score > 0.2:
                sentiment = 'positive'
            elif sentiment_score < -0.2:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': sentiment_score,
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    def detect_emergency_events(self, news_list: List[Dict]) -> List[Dict]:
        """
        检测突发事件
        关键词: 暴跌、熔断、危机、制裁、战争、疫情等
        """
        emergency_keywords = [
            '暴跌', '熔断', '危机', '制裁', '战争', '疫情',
            'crash', 'meltdown', 'crisis', 'sanction', 'war',
            'emergency', 'shutdown', 'default'
        ]
        
        emergency_events = []
        
        for news in news_list:
            text = news['title'].lower()
            
            for keyword in emergency_keywords:
                if keyword in text:
                    emergency_events.append({
                        'title': news['title'],
                        'url': news['url'],
                        'source': news['source'],
                        'timestamp': news['timestamp'],
                        'keyword': keyword,
                        'severity': 'high' if keyword in ['暴跌', 'crash', 'war'] else 'medium'
                    })
                    break
        
        return emergency_events
    
    def get_news_sentiment_summary(self) -> Dict:
        """
        获取新闻情绪汇总
        """
        try:
            # 获取新闻
            news_list = self.fetch_financial_news(num_articles=10)
            
            if not news_list:
                return {
                    'timestamp': datetime.now(),
                    'total_articles': 0,
                    'sentiment_distribution': {},
                    'emergency_events': []
                }
            
            # 分析每条新闻的情绪
            sentiments = []
            for news in news_list:
                sentiment_result = self.analyze_sentiment(news['title'])
                news['sentiment'] = sentiment_result['sentiment']
                news['sentiment_score'] = sentiment_result['score']
                sentiments.append(sentiment_result['sentiment'])
            
            # 统计情绪分布
            sentiment_counts = {
                'positive': sentiments.count('positive'),
                'negative': sentiments.count('negative'),
                'neutral': sentiments.count('neutral')
            }
            
            # 计算整体情绪分数
            total_scores = [n.get('sentiment_score', 0) for n in news_list]
            overall_score = np.mean(total_scores) if total_scores else 0
            
            # 检测突发事件
            emergency_events = self.detect_emergency_events(news_list)
            
            return {
                'timestamp': datetime.now(),
                'total_articles': len(news_list),
                'sentiment_distribution': sentiment_counts,
                'overall_sentiment_score': overall_score,
                'overall_sentiment': 'positive' if overall_score > 0.1 else ('negative' if overall_score < -0.1 else 'neutral'),
                'news_list': news_list,
                'emergency_events': emergency_events,
                'has_emergency': len(emergency_events) > 0
            }
            
        except Exception as e:
            logger.error(f"获取新闻情绪汇总失败: {e}")
            return {
                'timestamp': datetime.now(),
                'error': str(e)
            }


class EnhancedDataIntegration:
    """增强数据整合"""
    
    def __init__(self):
        self.macro_data = EnhancedMacroData()
        self.capital_flow = CapitalFlowData()
        self.news_analyzer = NewsSentimentAnalyzer()
    
    def get_comprehensive_data(self) -> Dict:
        """
        获取综合增强数据
        """
        logger.info("开始获取增强数据...")
        
        # 获取各类数据
        macro_data = self.macro_data.get_all_macro_data()
        capital_data = self.capital_flow.get_all_capital_flow_data()
        news_data = self.news_analyzer.get_news_sentiment_summary()
        
        # 整合数据
        comprehensive_data = {
            'macro': macro_data,
            'capital_flow': capital_data,
            'news_sentiment': news_data,
            'fetch_time': datetime.now()
        }
        
        # 生成风险信号
        risk_signals = self._generate_risk_signals(comprehensive_data)
        comprehensive_data['risk_signals'] = risk_signals
        
        logger.info("增强数据获取完成")
        
        return comprehensive_data
    
    def _generate_risk_signals(self, data: Dict) -> List[Dict]:
        """
        生成风险信号
        """
        signals = []
        
        # 1. VIX风险
        vix = data['macro']['vix'].get('value', 18.5)
        if vix > 30:
            signals.append({
                'type': 'macro',
                'indicator': 'VIX',
                'value': vix,
                'level': 'high',
                'message': f'VIX恐慌指数过高({vix:.1f}),市场恐慌情绪严重'
            })
        elif vix > 25:
            signals.append({
                'type': 'macro',
                'indicator': 'VIX',
                'value': vix,
                'level': 'medium',
                'message': f'VIX恐慌指数偏高({vix:.1f}),市场波动性增加'
            })
        
        # 2. 美元指数风险
        dollar = data['macro']['dollar_index'].get('value', 98.97)
        if dollar > 102:
            signals.append({
                'type': 'macro',
                'indicator': 'Dollar Index',
                'value': dollar,
                'level': 'high',
                'message': f'美元指数过强({dollar:.2f}),对铜价形成压制'
            })
        
        # 3. PMI风险
        pmi = data['macro']['pmi'].get('value', 54.04)
        if pmi < 45:
            signals.append({
                'type': 'macro',
                'indicator': 'PMI',
                'value': pmi,
                'level': 'high',
                'message': f'PMI过低({pmi:.1f}),经济衰退风险增加'
            })
        elif pmi < 50:
            signals.append({
                'type': 'macro',
                'indicator': 'PMI',
                'value': pmi,
                'level': 'medium',
                'message': f'PMI低于荣枯线({pmi:.1f}),经济活动收缩'
            })
        
        # 4. 新闻情绪风险
        news_data = data['news_sentiment']
        if news_data.get('has_emergency', False):
            for event in news_data.get('emergency_events', []):
                signals.append({
                    'type': 'news',
                    'indicator': 'Emergency Event',
                    'value': event['title'],
                    'level': event.get('severity', 'medium'),
                    'message': f'检测到突发事件: {event["title"]}'
                })
        elif news_data.get('overall_sentiment') == 'negative':
            signals.append({
                'type': 'news',
                'indicator': 'News Sentiment',
                'value': news_data.get('overall_sentiment_score', 0),
                'level': 'medium',
                'message': f'新闻情绪偏负面(分数: {news_data.get("overall_sentiment_score", 0):.2f})'
            })
        
        # 5. CFTC持仓风险
        cftc = data['capital_flow'].get('cftc', {})
        net_speculative = cftc.get('speculative', {}).get('net', 0)
        if net_speculative < -50000:
            signals.append({
                'type': 'capital',
                'indicator': 'CFTC Net Speculative',
                'value': net_speculative,
                'level': 'high',
                'message': f'投机净头寸大幅做空({net_speculative}),市场看空情绪浓厚'
            })
        
        return signals
    
    def save_to_file(self, data: Dict, filepath: str):
        """保存数据到文件"""
        import json
        
        # 转换datetime对象为字符串
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=json_serializer)
        
        logger.info(f"数据已保存到: {filepath}")
    
    def print_summary(self, data: Dict):
        """打印数据摘要"""
        print("\n" + "="*70)
        print("增强数据摘要")
        print("="*70)
        
        # 宏观数据
        print("\n【宏观数据】")
        macro = data['macro']
        print(f"  美元指数: {macro['dollar_index']['value']:.2f}")
        print(f"  PMI: {macro['pmi']['value']:.1f}")
        print(f"  联邦利率: {macro['interest_rate']['federal_funds_rate']:.2f}%")
        print(f"  VIX: {macro['vix']['value']:.1f}")
        
        # 资金流向
        print("\n【资金流向】")
        capital = data['capital_flow']
        cftc = capital['cftc']
        print(f"  商业净头寸: {cftc['commercial']['net']:,} 手")
        print(f"  投机净头寸: {cftc['speculative']['net']:,} 手")
        print(f"  总持仓量: {cftc['commercial']['long'] + cftc['speculative']['long']:,} 手")
        
        # 新闻情绪
        print("\n【新闻情绪】")
        news = data['news_sentiment']
        if 'error' not in news:
            print(f"  文章总数: {news['total_articles']}")
            print(f"  情绪分布: 正面{news['sentiment_distribution']['positive']} / 负面{news['sentiment_distribution']['negative']} / 中性{news['sentiment_distribution']['neutral']}")
            print(f"  整体情绪: {news['overall_sentiment']} (分数: {news['overall_sentiment_score']:.2f})")
            if news['has_emergency']:
                print(f"  ⚠️  检测到 {len(news['emergency_events'])} 个突发事件")
        
        # 风险信号
        print("\n【风险信号】")
        signals = data['risk_signals']
        if signals:
            for i, signal in enumerate(signals, 1):
                level_icon = '🔴' if signal['level'] == 'high' else '🟡'
                print(f"  {i}. {level_icon} {signal['message']}")
        else:
            print("  ✅ 无风险信号")
        
        print("\n" + "="*70)


if __name__ == '__main__':
    """测试"""
    integration = EnhancedDataIntegration()
    
    # 获取综合数据
    data = integration.get_comprehensive_data()
    
    # 打印摘要
    integration.print_summary(data)
    
    # 保存到文件
    output_file = "enhanced_data.json"
    integration.save_to_file(data, output_file)
    
    print(f"\n完整数据已保存到: {output_file}")
