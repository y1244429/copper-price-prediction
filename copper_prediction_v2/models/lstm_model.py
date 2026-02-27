"""
LSTM深度学习模型 - 时序预测
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    Dataset = object
    print("警告: 未安装PyTorch，LSTM模型不可用")


class CopperDataset(Dataset if TORCH_AVAILABLE else object):
    """铜价数据集"""
    
    def __init__(self, features: np.ndarray, targets: np.ndarray, 
                 seq_length: int = 60):
        """
        Args:
            features: 特征数组 (N, n_features)
            targets: 目标数组 (N,)
            seq_length: 序列长度
        """
        if not TORCH_AVAILABLE:
            raise ImportError("需要安装PyTorch")
        
        self.features = features
        self.targets = targets
        self.seq_length = seq_length
        
    def __len__(self):
        return len(self.features) - self.seq_length
    
    def __getitem__(self, idx):
        x = self.features[idx:idx + self.seq_length]
        y = self.targets[idx + self.seq_length]
        return torch.FloatTensor(x), torch.FloatTensor([y])


class LSTMModel(nn.Module if TORCH_AVAILABLE else object):
    """LSTM价格预测模型"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 128, 
                 num_layers: int = 2, dropout: float = 0.2,
                 bidirectional: bool = True):
        if not TORCH_AVAILABLE:
            raise ImportError("需要安装PyTorch")
        
        super(LSTMModel, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        
        # LSTM层
        self.lstm = nn.LSTM(
            input_dim, hidden_dim, num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )
        
        # 注意力机制
        lstm_output_dim = hidden_dim * 2 if bidirectional else hidden_dim
        self.attention = nn.Sequential(
            nn.Linear(lstm_output_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
            nn.Softmax(dim=1)
        )
        
        # 全连接层
        self.fc = nn.Sequential(
            nn.Linear(lstm_output_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        # LSTM编码
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # 注意力加权
        attention_weights = self.attention(lstm_out)
        context = torch.sum(attention_weights * lstm_out, dim=1)
        
        # 预测
        output = self.fc(context)
        return output.squeeze()


class GRUModel(nn.Module if TORCH_AVAILABLE else object):
    """GRU价格预测模型 (LSTM的轻量替代)"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 128,
                 num_layers: int = 2, dropout: float = 0.2):
        if not TORCH_AVAILABLE:
            raise ImportError("需要安装PyTorch")
        
        super(GRUModel, self).__init__()
        
        self.gru = nn.GRU(
            input_dim, hidden_dim, num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1)
        )
    
    def forward(self, x):
        gru_out, hidden = self.gru(x)
        output = self.fc(gru_out[:, -1, :])  # 取最后一个时间步
        return output.squeeze()


class DeepLearningPredictor:
    """深度学习预测器 - 封装训练和预测逻辑"""
    
    def __init__(self, model_type: str = 'lstm', seq_length: int = 60,
                 hidden_dim: int = 128, num_layers: int = 2,
                 learning_rate: float = 0.001, batch_size: int = 32,
                 epochs: int = 100, early_stopping_patience: int = 10):
        """
        Args:
            model_type: 'lstm' 或 'gru'
            seq_length: 输入序列长度
            hidden_dim: 隐藏层维度
            num_layers: LSTM层数
            learning_rate: 学习率
            batch_size: 批次大小
            epochs: 训练轮数
            early_stopping_patience: 早停耐心值
        """
        if not TORCH_AVAILABLE:
            raise ImportError("需要安装PyTorch: pip install torch")
        
        self.model_type = model_type
        self.seq_length = seq_length
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.early_stopping_patience = early_stopping_patience
        
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {self.device}")
        
    def _build_model(self, input_dim: int):
        """构建模型"""
        if self.model_type == 'lstm':
            self.model = LSTMModel(
                input_dim, self.hidden_dim, 
                self.num_layers
            ).to(self.device)
        else:
            self.model = GRUModel(
                input_dim, self.hidden_dim,
                self.num_layers
            ).to(self.device)
        
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), 
            lr=self.learning_rate,
            weight_decay=1e-5  # L2正则化
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', patience=5, factor=0.5
        )
    
    def prepare_data(self, features: pd.DataFrame, target: pd.Series,
                     train_ratio: float = 0.8) -> Tuple:
        """准备训练和验证数据"""
        # 标准化
        from sklearn.preprocessing import StandardScaler
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        
        X_scaled = self.scaler_X.fit_transform(features)
        y_scaled = self.scaler_y.fit_transform(target.values.reshape(-1, 1)).flatten()
        
        # 划分训练集和验证集 (时序分割)
        split_idx = int(len(X_scaled) * train_ratio)
        
        X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_val = y_scaled[:split_idx], y_scaled[split_idx:]
        
        # 创建数据集
        train_dataset = CopperDataset(X_train, y_train, self.seq_length)
        val_dataset = CopperDataset(X_val, y_val, self.seq_length)
        
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, 
                                  shuffle=False)  # 时序数据不打乱
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size)
        
        return train_loader, val_loader
    
    def train(self, features: pd.DataFrame, target: pd.Series,
              verbose: bool = True) -> Dict:
        """训练模型"""
        # 准备数据
        train_loader, val_loader = self.prepare_data(features, target)
        
        # 构建模型
        input_dim = features.shape[1]
        self._build_model(input_dim)
        
        # 训练循环
        best_val_loss = float('inf')
        patience_counter = 0
        train_losses = []
        val_losses = []
        
        for epoch in range(self.epochs):
            # 训练
            self.model.train()
            train_loss = 0
            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device).squeeze()
                
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                
                # 梯度裁剪
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                self.optimizer.step()
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            train_losses.append(train_loss)
            
            # 验证
            self.model.eval()
            val_loss = 0
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device).squeeze()
                    
                    outputs = self.model(batch_X)
                    loss = self.criterion(outputs, batch_y)
                    val_loss += loss.item()
            
            val_loss /= len(val_loader)
            val_losses.append(val_loss)
            
            # 学习率调整
            self.scheduler.step(val_loss)
            
            # 早停
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # 保存最佳模型
                self.best_model_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
                if patience_counter >= self.early_stopping_patience:
                    if verbose:
                        print(f"早停于第 {epoch + 1} 轮")
                    break
            
            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}/{self.epochs}, "
                      f"Train Loss: {train_loss:.6f}, "
                      f"Val Loss: {val_loss:.6f}")
        
        # 加载最佳模型
        self.model.load_state_dict(self.best_model_state)
        
        return {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'best_val_loss': best_val_loss,
            'final_epoch': len(train_losses)
        }
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """预测"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        self.model.eval()
        
        # 标准化
        X_scaled = self.scaler_X.transform(features)
        
        # 创建序列
        predictions = []
        with torch.no_grad():
            for i in range(len(X_scaled) - self.seq_length + 1):
                seq = X_scaled[i:i + self.seq_length]
                seq_tensor = torch.FloatTensor(seq).unsqueeze(0).to(self.device)
                
                pred = self.model(seq_tensor).cpu().numpy()
                predictions.append(pred)
        
        # 反标准化
        predictions = np.array(predictions)
        predictions = self.scaler_y.inverse_transform(predictions.reshape(-1, 1)).flatten()
        
        # 补齐前面的空值
        padding = np.full(self.seq_length - 1, np.nan)
        predictions = np.concatenate([padding, predictions])
        
        return predictions
    
    def save_model(self, filepath: str):
        """保存模型"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler_X': self.scaler_X,
            'scaler_y': self.scaler_y,
            'model_config': {
                'model_type': self.model_type,
                'seq_length': self.seq_length,
                'hidden_dim': self.hidden_dim,
                'num_layers': self.num_layers
            }
        }, filepath)
        print(f"模型已保存至: {filepath}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        config = checkpoint['model_config']
        self.model_type = config['model_type']
        self.seq_length = config['seq_length']
        self.hidden_dim = config['hidden_dim']
        self.num_layers = config['num_layers']
        
        self.scaler_X = checkpoint['scaler_X']
        self.scaler_y = checkpoint['scaler_y']
        
        input_dim = self.scaler_X.scale_.shape[0]
        self._build_model(input_dim)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        print(f"模型已从 {filepath} 加载")


# 测试代码
if __name__ == '__main__':
    if not TORCH_AVAILABLE:
        print("PyTorch未安装，无法运行测试")
        exit()
    
    print("="*60)
    print("LSTM模型测试")
    print("="*60)
    
    # 生成测试数据
    np.random.seed(42)
    n_samples = 500
    n_features = 10
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = pd.Series(np.random.randn(n_samples))
    
    print(f"\n数据形状: X={X.shape}, y={y.shape}")
    
    # 创建和训练模型
    print("\n训练LSTM模型...")
    model = DeepLearningPredictor(
        model_type='lstm',
        seq_length=30,
        hidden_dim=64,
        num_layers=2,
        epochs=20,
        early_stopping_patience=5
    )
    
    history = model.train(X, y, verbose=True)
    
    print(f"\n最佳验证损失: {history['best_val_loss']:.6f}")
    print(f"训练轮数: {history['final_epoch']}")
    
    # 预测
    print("\n生成预测...")
    predictions = model.predict(X)
    print(f"预测数量: {len(predictions)}")
    print(f"预测范围: [{predictions.min():.4f}, {predictions.max():.4f}]")
    
    # 保存和加载
    print("\n测试模型保存/加载...")
    model.save_model('test_lstm_model.pth')
    model.load_model('test_lstm_model.pth')
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
