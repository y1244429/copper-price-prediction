# 依赖包安装指南

## 当前状态

✅ **已安装:**
- numpy, pandas
- scikit-learn
- xgboost
- AKShare (v1.16.50) ✅

❌ **待安装:**
- PyTorch (用于LSTM模型)
- SHAP (用于模型解释)

## 安装方法

### 方法1: 使用pip安装(推荐)

```bash
# 安装PyTorch (CPU版本)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 安装SHAP
pip install shap
```

### 方法2: 使用脚本安装

```bash
cd copper_prediction_v2
./install_deps.sh
```

### 方法3: 使用conda安装PyTorch

```bash
conda install pytorch -c pytorch
pip install shap
```

### 方法4: GPU版本(如果有NVIDIA显卡)

```bash
# CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 或者 CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118

pip install shap
```

## 验证安装

运行以下命令验证安装是否成功:

```bash
# 检查PyTorch
python -c "import torch; print('PyTorch version:', torch.__version__)"

# 检查SHAP
python -c "import shap; print('SHAP version:', shap.__version__)"

# 检查AKShare
python -c "import akshare as ak; print('AKShare version:', ak.__version__)"

# 测试完整系统
python main.py --demo --data-source mock
```

## 测试真实数据源

安装完成后,可以使用真实数据源:

```bash
# 使用AKShare真实数据
python main.py --demo --data-source akshare
```

## 注意事项

1. **PyTorch安装时间**: PyTorch包较大(~500MB),安装可能需要5-15分钟
2. **网络连接**: 确保网络连接稳定,安装过程中不要中断
3. **权限问题**: 如果遇到权限问题,添加 `--user` 参数
4. **镜像源**: 如果下载慢,可以使用清华镜像:
   ```bash
   pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

## 完整依赖列表

查看 `requirements.txt` 获取完整依赖列表:

```bash
pip install -r requirements.txt
```

## 故障排除

### 问题1: PyTorch导入失败
```bash
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 问题2: SHAP导入失败
```bash
pip install --upgrade shap
```

### 问题3: AKShare数据获取失败
AKShare接口可能变化,可以尝试:
- 更新AKShare: `pip install --upgrade akshare`
- 使用mock数据: `--data-source mock`
