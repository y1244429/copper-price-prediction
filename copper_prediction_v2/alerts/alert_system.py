"""
实时预警系统
支持价格预警、技术指标预警、波动率预警等
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import time
import warnings
warnings.filterwarnings('ignore')


@dataclass
class AlertRule:
    """预警规则"""
    id: str
    name: str
    type: str  # 'price', 'indicator', 'volatility', 'volume'
    condition: str  # 'above', 'below', 'cross_up', 'cross_down', 'change_pct'
    threshold: float
    symbol: str = "CU"
    active: bool = True
    notification_channels: List[str] = None
    cooldown_minutes: int = 60  # 冷却时间
    last_triggered: datetime = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = ['console']


class AlertEngine:
    """预警引擎"""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Dict] = []
        self.data_cache: pd.DataFrame = None
        self.callbacks: List[Callable] = []
        self.running = False
        self.check_interval = 60  # 检查间隔(秒)
    
    def add_rule(self, rule: AlertRule):
        """添加预警规则"""
        self.rules[rule.id] = rule
        print(f"添加预警规则: {rule.name} (ID: {rule.id})")
    
    def remove_rule(self, rule_id: str):
        """删除预警规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            print(f"删除预警规则: {rule_id}")
    
    def check_alerts(self, data: pd.DataFrame):
        """检查所有预警规则"""
        self.data_cache = data
        current_price = data['close'].iloc[-1]
        current_time = datetime.now()
        
        for rule_id, rule in self.rules.items():
            if not rule.active:
                continue
            
            # 检查冷却时间
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if current_time < cooldown_end:
                    continue
            
            # 检查条件
            triggered = self._check_condition(rule, data)
            
            if triggered:
                alert = self._create_alert(rule, current_price, data)
                self._send_notifications(rule, alert)
                self.alert_history.append(alert)
                rule.last_triggered = current_time
    
    def _check_condition(self, rule: AlertRule, data: pd.DataFrame) -> bool:
        """检查单个规则条件"""
        current = data['close'].iloc[-1]
        previous = data['close'].iloc[-2] if len(data) > 1 else current
        
        if rule.type == 'price':
            if rule.condition == 'above':
                return current > rule.threshold
            elif rule.condition == 'below':
                return current < rule.threshold
            elif rule.condition == 'cross_up':
                return (previous <= rule.threshold) and (current > rule.threshold)
            elif rule.condition == 'cross_down':
                return (previous >= rule.threshold) and (current < rule.threshold)
        
        elif rule.type == 'change_pct':
            change_pct = (current / previous - 1) * 100
            if rule.condition == 'above':
                return change_pct > rule.threshold
            elif rule.condition == 'below':
                return change_pct < -rule.threshold
        
        elif rule.type == 'indicator':
            # 检查技术指标
            indicator_value = self._get_indicator_value(rule, data)
            if indicator_value is None:
                return False
            
            if rule.condition == 'above':
                return indicator_value > rule.threshold
            elif rule.condition == 'below':
                return indicator_value < rule.threshold
        
        elif rule.type == 'volatility':
            # 检查波动率
            volatility = data['close'].pct_change().rolling(20).std().iloc[-1] * 100
            if rule.condition == 'above':
                return volatility > rule.threshold
        
        return False
    
    def _get_indicator_value(self, rule: AlertRule, data: pd.DataFrame) -> Optional[float]:
        """获取技术指标值"""
        from features.technical_indicators import TechnicalIndicators
        
        ti = TechnicalIndicators()
        
        if 'rsi' in rule.name.lower():
            rsi = ti.rsi(data['close'])
            return rsi.iloc[-1] if not rsi.empty else None
        
        elif 'macd' in rule.name.lower():
            macd_df = ti.macd(data['close'])
            return macd_df['macd'].iloc[-1] if not macd_df.empty else None
        
        elif 'kdj' in rule.name.lower():
            kdj_df = ti.kdj(data['high'], data['low'], data['close'])
            return kdj_df['k'].iloc[-1] if not kdj_df.empty else None
        
        elif 'boll' in rule.name.lower():
            bb_df = ti.bollinger_bands(data['close'])
            return bb_df['percent_b'].iloc[-1] if not bb_df.empty else None
        
        return None
    
    def _create_alert(self, rule: AlertRule, current_price: float, 
                     data: pd.DataFrame) -> Dict:
        """创建预警记录"""
        return {
            'id': f"{rule.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'rule_id': rule.id,
            'rule_name': rule.name,
            'timestamp': datetime.now().isoformat(),
            'symbol': rule.symbol,
            'current_price': current_price,
            'threshold': rule.threshold,
            'condition': rule.condition,
            'data_snapshot': {
                'open': data['open'].iloc[-1],
                'high': data['high'].iloc[-1],
                'low': data['low'].iloc[-1],
                'close': data['close'].iloc[-1],
                'volume': data.get('volume', pd.Series([0])).iloc[-1]
            }
        }
    
    def _send_notifications(self, rule: AlertRule, alert: Dict):
        """发送通知"""
        for channel in rule.notification_channels:
            if channel == 'console':
                self._notify_console(rule, alert)
            elif channel == 'email':
                self._notify_email(rule, alert)
            elif channel == 'webhook':
                self._notify_webhook(rule, alert)
    
    def _notify_console(self, rule: AlertRule, alert: Dict):
        """控制台通知"""
        print("\n" + "="*60)
        print(f"🚨 预警触发: {rule.name}")
        print("="*60)
        print(f"时间: {alert['timestamp']}")
        print(f"品种: {alert['symbol']}")
        print(f"当前价格: ¥{alert['current_price']:,.2f}")
        print(f"条件: {rule.condition} {rule.threshold}")
        print("="*60 + "\n")
    
    def _notify_email(self, rule: AlertRule, alert: Dict):
        """邮件通知 (需要配置SMTP)"""
        # 这里需要配置SMTP服务器信息
        pass
    
    def _notify_webhook(self, rule: AlertRule, alert: Dict):
        """Webhook通知"""
        # 可以发送到企业微信、钉钉、Slack等
        pass
    
    def start_monitoring(self, data_provider: Callable, interval: int = 60):
        """
        开始持续监控
        
        Args:
            data_provider: 数据提供函数
            interval: 检查间隔(秒)
        """
        self.running = True
        self.check_interval = interval
        
        def monitor_loop():
            while self.running:
                try:
                    data = data_provider()
                    if data is not None and not data.empty:
                        self.check_alerts(data)
                except Exception as e:
                    print(f"监控错误: {e}")
                
                time.sleep(self.check_interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        print(f"预警监控已启动 (检查间隔: {interval}秒)")
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        print("预警监控已停止")
    
    def get_alert_history(self, hours: int = 24) -> List[Dict]:
        """获取预警历史"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alert_history 
                if datetime.fromisoformat(a['timestamp']) > cutoff]
    
    def export_rules(self, filepath: str):
        """导出规则到JSON"""
        rules_data = [asdict(rule) for rule in self.rules.values()]
        with open(filepath, 'w') as f:
            json.dump(rules_data, f, indent=2, default=str)
        print(f"规则已导出: {filepath}")
    
    def import_rules(self, filepath: str):
        """从JSON导入规则"""
        with open(filepath, 'r') as f:
            rules_data = json.load(f)
        
        for rule_data in rules_data:
            rule = AlertRule(**rule_data)
            self.add_rule(rule)
        
        print(f"已导入 {len(rules_data)} 条规则")


# 预定义常用预警规则
class AlertTemplates:
    """预警规则模板"""
    
    @staticmethod
    def price_breakout(symbol: str = "CU", threshold: float = 70000) -> AlertRule:
        """价格突破预警"""
        return AlertRule(
            id="price_breakout",
            name="价格突破预警",
            type="price",
            condition="above",
            threshold=threshold,
            symbol=symbol,
            notification_channels=['console'],
            cooldown_minutes=30
        )
    
    @staticmethod
    def price_support(symbol: str = "CU", threshold: float = 65000) -> AlertRule:
        """价格支撑位预警"""
        return AlertRule(
            id="price_support",
            name="价格跌破支撑",
            type="price",
            condition="below",
            threshold=threshold,
            symbol=symbol,
            notification_channels=['console'],
            cooldown_minutes=30
        )
    
    @staticmethod
    def big_movement(symbol: str = "CU", threshold: float = 3.0) -> AlertRule:
        """大幅波动预警"""
        return AlertRule(
            id="big_movement",
            name="大幅波动预警",
            type="change_pct",
            condition="above",
            threshold=threshold,
            symbol=symbol,
            notification_channels=['console'],
            cooldown_minutes=15
        )
    
    @staticmethod
    def rsi_overbought(symbol: str = "CU", threshold: float = 80) -> AlertRule:
        """RSI超买预警"""
        return AlertRule(
            id="rsi_overbought",
            name="RSI超买预警",
            type="indicator",
            condition="above",
            threshold=threshold,
            symbol=symbol,
            notification_channels=['console'],
            cooldown_minutes=60
        )
    
    @staticmethod
    def rsi_oversold(symbol: str = "CU", threshold: float = 20) -> AlertRule:
        """RSI超卖预警"""
        return AlertRule(
            id="rsi_oversold",
            name="RSI超卖预警",
            type="indicator",
            condition="below",
            threshold=threshold,
            symbol=symbol,
            notification_channels=['console'],
            cooldown_minutes=60
        )
    
    @staticmethod
    def high_volatility(symbol: str = "CU", threshold: float = 5.0) -> AlertRule:
        """高波动率预警"""
        return AlertRule(
            id="high_volatility",
            name="高波动率预警",
            type="volatility",
            condition="above",
            threshold=threshold,
            symbol=symbol,
            notification_channels=['console'],
            cooldown_minutes=120
        )


# 便捷函数
def create_default_alert_system() -> AlertEngine:
    """创建默认预警系统"""
    engine = AlertEngine()
    
    # 添加常用预警
    engine.add_rule(AlertTemplates.price_breakout(threshold=75000))
    engine.add_rule(AlertTemplates.price_support(threshold=65000))
    engine.add_rule(AlertTemplates.big_movement(threshold=2.5))
    engine.add_rule(AlertTemplates.rsi_overbought(threshold=75))
    engine.add_rule(AlertTemplates.rsi_oversold(threshold=25))
    engine.add_rule(AlertTemplates.high_volatility(threshold=4.0))
    
    return engine


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("实时预警系统测试")
    print("="*60)
    
    # 创建预警系统
    engine = create_default_alert_system()
    
    # 生成测试数据
    np.random.seed(42)
    n = 100
    
    dates = pd.date_range(end=datetime.now(), periods=n, freq='H')
    prices = 70000 + np.cumsum(np.random.randn(n) * 100)
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n) * 0.001),
        'high': prices * (1 + abs(np.random.randn(n)) * 0.002),
        'low': prices * (1 - abs(np.random.randn(n)) * 0.002),
        'close': prices,
        'volume': np.random.randint(10000, 50000, n)
    }, index=dates)
    
    print(f"\n测试数据: {len(data)} 条")
    print(data.tail())
    
    # 手动触发检查
    print("\n" + "="*60)
    print("检查预警...")
    print("="*60)
    
    engine.check_alerts(data)
    
    # 查看历史
    print("\n预警历史:")
    history = engine.get_alert_history(hours=24)
    print(f"最近24小时预警数: {len(history)}")
    
    # 导出规则
    engine.export_rules("alert_rules.json")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
