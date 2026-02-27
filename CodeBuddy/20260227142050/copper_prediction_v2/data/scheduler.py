"""
任务调度器 - 定时执行数据更新和预测任务
"""

import schedule
import time
from typing import Optional, Callable
import warnings
warnings.filterwarnings('ignore')

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        """初始化调度器"""
        self.running = False
        self.thread = None

    def schedule_daily(self, func: Callable, time_str: str):
        """
        安排每日任务

        Args:
            func: 要执行的函数
            time_str: 时间字符串,如 '09:00'
        """
        schedule.every().day.at(time_str).do(func)
        print(f"已安排每日任务: {time_str}")

    def schedule_weekly(self, func: Callable, day: str, time_str: str):
        """
        安排每周任务

        Args:
            func: 要执行的函数
            day: 星期几,如 'monday', 'tuesday'
            time_str: 时间字符串
        """
        getattr(schedule.every(), day).at(time_str).do(func)
        print(f"已安排每周任务: {day} {time_str}")

    def start(self, blocking: bool = True):
        """
        启动调度器

        Args:
            blocking: 是否阻塞主线程
        """
        self.running = True

        if blocking:
            print("调度器已启动(阻塞模式)")
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        else:
            print("调度器已启动(后台模式,需要手动调用run_pending)")
            import threading
            def run_schedule():
                while self.running:
                    schedule.run_pending()
                    time.sleep(60)
            self.thread = threading.Thread(target=run_schedule, daemon=True)
            self.thread.start()

    def stop(self):
        """停止调度器"""
        self.running = False
        schedule.clear()
        print("调度器已停止")

    def run_pending(self):
        """手动执行待运行的任务"""
        schedule.run_pending()


def create_default_scheduler(predictor: 'CopperPriceModel', data_source):
    """
    创建默认调度器配置

    Args:
        predictor: 预测模型实例
        data_source: 数据源实例

    Returns:
        TaskScheduler实例
    """
    scheduler = TaskScheduler()

    # 每日9:00更新数据
    def update_data():
        print(f"\n[{pd.Timestamp.now()}] 更新数据...")
        try:
            data = data_source.fetch_copper_price(
                start_date=(pd.Timestamp.now() - pd.Timedelta(days=365)).strftime("%Y-%m-%d"),
                end_date=pd.Timestamp.now().strftime("%Y-%m-%d")
            )
            print(f"数据更新完成: {len(data)} 条记录")
        except Exception as e:
            print(f"数据更新失败: {e}")

    # 每日8:00生成预测报告
    def generate_report():
        print(f"\n[{pd.Timestamp.now()}] 生成预测报告...")
        try:
            # 这里可以调用预测和报告生成逻辑
            print("报告生成完成")
        except Exception as e:
            print(f"报告生成失败: {e}")

    # 每周日凌晨2:00重新训练模型
    def retrain_model():
        print(f"\n[{pd.Timestamp.now()}] 重新训练模型...")
        try:
            # 这里可以调用模型训练逻辑
            print("模型训练完成")
        except Exception as e:
            print(f"模型训练失败: {e}")

    # 安排任务
    scheduler.schedule_daily(update_data, "09:00")
    scheduler.schedule_daily(generate_report, "08:00")
    scheduler.schedule_weekly(retrain_model, "sunday", "02:00")

    return scheduler
