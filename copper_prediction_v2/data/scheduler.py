"""
任务调度模块 - 定时更新数据和模型
"""

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("提示: 安装schedule库可启用任务调度: pip install schedule")
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, Optional
import threading
import warnings
warnings.filterwarnings('ignore')


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, log_file: str = "scheduler.log"):
        if not SCHEDULE_AVAILABLE:
            raise ImportError("需要安装schedule库: pip install schedule")
        
        self.log_file = log_file
        self.tasks = {}
        self.running = False
        self.thread = None
        
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 打印到控制台
        print(log_entry.strip())
        
        # 写入文件
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
    
    def add_task(self, name: str, job: Callable, 
                 schedule_type: str, **kwargs):
        """
        添加定时任务
        
        Args:
            name: 任务名称
            job: 任务函数
            schedule_type: 'daily', 'hourly', 'weekly', 'interval'
            **kwargs: 调度参数
        """
        if schedule_type == 'daily':
            # 每天特定时间执行
            at_time = kwargs.get('at', '09:00')
            schedule.every().day.at(at_time).do(self._wrap_job, name, job)
            
        elif schedule_type == 'hourly':
            # 每小时执行
            schedule.every().hour.do(self._wrap_job, name, job)
            
        elif schedule_type == 'weekly':
            # 每周特定时间执行
            day = kwargs.get('day', 'monday')
            at_time = kwargs.get('at', '09:00')
            getattr(schedule.every(), day).at(at_time).do(
                self._wrap_job, name, job
            )
            
        elif schedule_type == 'interval':
            # 按间隔执行
            minutes = kwargs.get('minutes', 60)
            schedule.every(minutes).minutes.do(self._wrap_job, name, job)
        
        self.tasks[name] = {
            'job': job,
            'schedule': schedule_type,
            'params': kwargs,
            'last_run': None,
            'run_count': 0
        }
        
        self.log(f"添加任务: {name} ({schedule_type})")
    
    def _wrap_job(self, name: str, job: Callable):
        """包装任务函数，添加日志和错误处理"""
        try:
            self.log(f"开始执行任务: {name}")
            result = job()
            
            self.tasks[name]['last_run'] = datetime.now()
            self.tasks[name]['run_count'] += 1
            
            self.log(f"任务完成: {name}")
            return result
            
        except Exception as e:
            self.log(f"任务失败 {name}: {str(e)}")
            return None
    
    def start(self, blocking: bool = False):
        """启动调度器"""
        self.running = True
        self.log("调度器已启动")
        
        if blocking:
            self._run_loop()
        else:
            self.thread = threading.Thread(target=self._run_loop)
            self.thread.daemon = True
            self.thread.start()
    
    def _run_loop(self):
        """运行调度循环"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.log("调度器已停止")
    
    def get_status(self) -> Dict:
        """获取任务状态"""
        return {
            name: {
                'schedule': info['schedule'],
                'last_run': info['last_run'].strftime("%Y-%m-%d %H:%M:%S") 
                           if info['last_run'] else None,
                'run_count': info['run_count']
            }
            for name, info in self.tasks.items()
        }


class DataUpdateTask:
    """数据更新任务"""
    
    def __init__(self, data_source, storage_path: str = "data/"):
        self.data_source = data_source
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
    def update_price_data(self) -> bool:
        """更新价格数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            df = self.data_source.fetch_copper_price(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            if not df.empty:
                # 保存到CSV
                filepath = self.storage_path / f"price_{end_date.strftime('%Y%m%d')}.csv"
                df.to_csv(filepath)
                print(f"价格数据已更新: {len(df)} 条记录")
                return True
            
            return False
            
        except Exception as e:
            print(f"更新价格数据失败: {e}")
            return False
    
    def update_inventory_data(self) -> bool:
        """更新库存数据"""
        try:
            df = self.data_source.fetch_inventory(days=365)
            
            if not df.empty:
                filepath = self.storage_path / "inventory_latest.csv"
                df.to_csv(filepath)
                print(f"库存数据已更新: {len(df)} 条记录")
                return True
            
            return False
            
        except Exception as e:
            print(f"更新库存数据失败: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """清理旧数据"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for file in self.storage_path.glob("price_*.csv"):
            # 从文件名提取日期
            try:
                file_date_str = file.stem.split('_')[1]
                file_date = datetime.strptime(file_date_str, "%Y%m%d")
                
                if file_date < cutoff_date:
                    file.unlink()
                    print(f"已删除旧数据: {file.name}")
            except:
                pass


class ModelRetrainTask:
    """模型重训练任务"""
    
    def __init__(self, predictor, model_path: str = "models/"):
        self.predictor = predictor
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
        self.best_score = float('inf')
        
    def retrain_model(self) -> bool:
        """重训练模型"""
        try:
            print("开始模型重训练...")
            
            # 加载最新数据
            from data.data_sources import MockDataSource, DataMerger
            
            source = MockDataSource()
            merger = DataMerger(source)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            data = merger.get_full_dataset(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            if data.empty:
                print("无数据可用")
                return False
            
            # 准备特征
            from models.copper_model_v2 import FeatureEngineer
            
            feature_engineer = FeatureEngineer()
            features = feature_engineer.create_features(data)
            
            # 生成标签
            target = (data['close'].shift(-5) / data['close'] - 1).loc[features.index]
            
            # 训练模型
            results = self.predictor.full_pipeline(data)
            
            # 评估性能
            backtest_results = results.get('backtest_results', {})
            current_score = backtest_results.get('sharpe_ratio', 0)
            
            # 如果性能更好，保存模型
            if current_score > self.best_score:
                self.best_score = current_score
                self._save_model_checkpoint()
                print(f"模型性能提升，已保存 (Sharpe: {current_score:.3f})")
            else:
                print(f"模型性能未提升 (当前: {current_score:.3f}, 最佳: {self.best_score:.3f})")
            
            return True
            
        except Exception as e:
            print(f"模型重训练失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _save_model_checkpoint(self):
        """保存模型检查点"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 这里可以添加实际的模型保存逻辑
        checkpoint_file = self.model_path / f"model_{timestamp}.pkl"
        print(f"模型检查点: {checkpoint_file}")


class PredictionReportTask:
    """生成预测报告任务"""
    
    def __init__(self, predictor, report_path: str = "reports/"):
        self.predictor = predictor
        self.report_path = Path(report_path)
        self.report_path.mkdir(exist_ok=True)
    
    def generate_daily_report(self) -> str:
        """生成每日报告"""
        try:
            report_time = datetime.now()
            
            # 获取最新预测
            short_term = self.predictor.predict_short_term(5)
            medium_term = self.predictor.predict_medium_term(3)
            
            # 构建报告
            report = f"""
# 铜价预测日报
生成时间: {report_time.strftime("%Y-%m-%d %H:%M:%S")}

## 价格预测

### 短期 (5天)
- 当前价格: ¥{short_term['current_price']:,.2f}
- 预测价格: ¥{short_term['predicted_price']:,.2f}
- 预期变化: {short_term['predicted_change']:+.2f}%
- 趋势: {short_term['trend']}

### 中期 (3个月)
- 预测价格: ¥{medium_term['predicted_price']:,.2f}
- 预期变化: {medium_term['predicted_change']:+.2f}%

## 交易建议
- 短期策略: {short_term.get('recommendation', '观望')}
- 中期策略: {medium_term.get('recommendation', '观望')}

## 风险提示
本报告仅供参考，不构成投资建议。
"""
            
            # 保存报告
            report_file = self.report_path / f"report_{report_time.strftime('%Y%m%d')}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"报告已生成: {report_file}")
            return str(report_file)
            
        except Exception as e:
            print(f"生成报告失败: {e}")
            return ""


# 便捷函数：创建默认调度器
def create_default_scheduler(predictor, data_source) -> TaskScheduler:
    """创建默认的任务调度器"""
    scheduler = TaskScheduler()
    
    # 创建任务对象
    data_task = DataUpdateTask(data_source)
    model_task = ModelRetrainTask(predictor)
    report_task = PredictionReportTask(predictor)
    
    # 添加定时任务
    scheduler.add_task(
        'update_price',
        data_task.update_price_data,
        'daily',
        at='09:00'
    )
    
    scheduler.add_task(
        'update_inventory',
        data_task.update_inventory_data,
        'daily',
        at='09:30'
    )
    
    scheduler.add_task(
        'retrain_model',
        model_task.retrain_model,
        'weekly',
        day='sunday',
        at='02:00'
    )
    
    scheduler.add_task(
        'generate_report',
        report_task.generate_daily_report,
        'daily',
        at='08:00'
    )
    
    scheduler.add_task(
        'cleanup_data',
        data_task.cleanup_old_data,
        'weekly',
        day='saturday',
        at='03:00'
    )
    
    return scheduler


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("任务调度模块测试")
    print("="*60)
    
    # 创建调度器
    scheduler = TaskScheduler(log_file="test_scheduler.log")
    
    # 定义测试任务
    def test_job_1():
        print("执行任务 1: 数据更新")
        return "success"
    
    def test_job_2():
        print("执行任务 2: 模型训练")
        return "success"
    
    # 添加任务
    scheduler.add_task('test_data_update', test_job_1, 'interval', minutes=1)
    scheduler.add_task('test_model_train', test_job_2, 'interval', minutes=2)
    
    # 查看任务状态
    print("\n任务列表:")
    for name, info in scheduler.tasks.items():
        print(f"  - {name}: {info['schedule']}")
    
    # 启动调度器（非阻塞）
    print("\n启动调度器 (运行10秒)...")
    scheduler.start(blocking=False)
    
    # 运行10秒后停止
    time.sleep(10)
    
    scheduler.stop()
    
    # 查看状态
    print("\n最终状态:")
    status = scheduler.get_status()
    for name, info in status.items():
        print(f"  {name}: 运行{info['run_count']}次")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
