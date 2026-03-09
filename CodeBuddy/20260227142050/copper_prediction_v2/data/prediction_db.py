"""
预测数据库管理模块
管理预测历史记录和数据库操作
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

class PredictionDatabase:
    """预测数据库管理类"""
    
    def __init__(self, db_path: str = "data/data/predictions.db"):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    date DATE,
                    predicted_price REAL,
                    actual_price REAL,
                    model_type TEXT,
                    horizon INTEGER,
                    confidence_lower REAL,
                    confidence_upper REAL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model_type TEXT,
                    rmse REAL,
                    mae REAL,
                    mape REAL,
                    r2 REAL,
                    horizon INTEGER
                )
            """)
            
            conn.commit()
    
    def save_prediction(self, *args, **kwargs):
        """
        保存预测结果 - 适配项目原有表结构
        
        支持两种调用方式:
        1. save_prediction(prediction_data_dict) - 传入完整字典
        2. save_prediction(date=..., predicted_price=...) - 单独参数
        """
        from datetime import datetime
        
        # 处理位置参数 - 如果第一个参数是字典，视为 prediction_data
        prediction_data = kwargs.get('prediction_data')
        if args and isinstance(args[0], dict):
            prediction_data = args[0]
        
        # 如果传入的是完整字典，直接使用
        if prediction_data is not None:
            pd = prediction_data
            run_time = pd.get('run_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO predictions 
                    (prediction_date, run_time, current_price, xgboost_5day, xgboost_10day, xgboost_20day,
                     macro_1month, macro_3month, macro_6month, fundamental_6month,
                     lstm_5day, lstm_10day, enhanced_system_5day, enhanced_system_30day,
                     integrated_system_5day, integrated_system_30day,
                     overall_trend, confidence, risk_level, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pd.get('prediction_date'), run_time, pd.get('current_price'),
                    pd.get('xgboost_5day'), pd.get('xgboost_10day'), pd.get('xgboost_20day'),
                    pd.get('macro_1month'), pd.get('macro_3month'), pd.get('macro_6month'),
                    pd.get('fundamental_6month'), pd.get('lstm_5day'), pd.get('lstm_10day'),
                    pd.get('enhanced_system_5day'), pd.get('enhanced_system_30day'),
                    pd.get('integrated_system_5day'), pd.get('integrated_system_30day'),
                    pd.get('overall_trend'), pd.get('confidence'), pd.get('risk_level'),
                    pd.get('notes'), run_time, run_time
                ))
                conn.commit()
            return True
        
        # 简单模式：从 kwargs 获取单独参数
        run_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prediction_date = kwargs.get('date', datetime.now().strftime('%Y-%m-%d'))
        predicted_price = kwargs.get('predicted_price')
        metadata = kwargs.get('metadata')
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO predictions 
                (prediction_date, run_time, current_price, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (prediction_date, run_time, predicted_price, metadata, run_time, run_time))
            conn.commit()
        return True
    
    def save_metrics(self, model_type, rmse, mae, mape, r2, horizon=1):
        """
        保存模型评估指标
        
        Args:
            model_type: 模型类型
            rmse: 均方根误差
            mae: 平均绝对误差
            mape: 平均绝对百分比误差
            r2: R² 分数
            horizon: 预测 horizon
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO model_metrics 
                (model_type, rmse, mae, mape, r2, horizon)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (model_type, rmse, mae, mape, r2, horizon))
            conn.commit()
    
    def get_predictions(self, model_type=None, limit=100):
        """
        获取历史预测记录
        
        Args:
            model_type: 筛选特定模型类型
            limit: 返回记录数限制
            
        Returns:
            DataFrame: 预测记录
        """
        with sqlite3.connect(self.db_path) as conn:
            if model_type:
                query = """
                    SELECT * FROM predictions 
                    WHERE model_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                return pd.read_sql_query(query, conn, params=(model_type, limit))
            else:
                query = """
                    SELECT * FROM predictions 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                return pd.read_sql_query(query, conn, params=(limit,))
    
    def get_latest_prediction(self, model_type=None):
        """
        获取最新预测
        
        Args:
            model_type: 模型类型筛选
            
        Returns:
            dict: 最新预测记录
        """
        with sqlite3.connect(self.db_path) as conn:
            if model_type:
                query = """
                    SELECT * FROM predictions 
                    WHERE model_type = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                result = conn.execute(query, (model_type,)).fetchone()
            else:
                query = """
                    SELECT * FROM predictions 
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                result = conn.execute(query).fetchone()
            
            if result:
                columns = [description[0] for description in conn.execute(
                    "PRAGMA table_info(predictions)").fetchall()]
                return dict(zip(columns, result))
            return None
    
    def close(self):
        """关闭数据库连接 (上下文管理器会自动处理)"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
