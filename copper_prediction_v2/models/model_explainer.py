"""
模型解释性分析 - SHAP和特征重要性
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("提示: 安装shap可获得模型解释功能: pip install shap")


class ModelExplainer:
    """模型解释器"""
    
    def __init__(self, model, feature_names: List[str]):
        """
        Args:
            model: 训练好的模型
            feature_names: 特征名称列表
        """
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        
    def explain_prediction(self, X: pd.DataFrame, 
                          instance_idx: int = -1) -> Dict:
        """
        解释单个预测
        
        Returns:
            特征贡献度分析
        """
        if not SHAP_AVAILABLE:
            return {"error": "SHAP未安装"}
        
        # 初始化SHAP解释器
        if self.explainer is None:
            if hasattr(self.model, 'predict'):
                self.explainer = shap.Explainer(self.model, X)
            else:
                return {"error": "模型不支持SHAP解释"}
        
        # 计算SHAP值
        shap_values = self.explainer(X)
        
        # 获取指定样本的解释
        instance_shap = shap_values[instance_idx]
        
        # 整理特征贡献
        contributions = []
        for i, feature in enumerate(self.feature_names):
            contributions.append({
                'feature': feature,
                'value': X.iloc[instance_idx, i],
                'shap_value': instance_shap.values[i],
                'impact': '正向' if instance_shap.values[i] > 0 else '负向'
            })
        
        # 按绝对值排序
        contributions.sort(key=lambda x: abs(x['shap_value']), reverse=True)
        
        return {
            'base_value': shap_values.base_values[instance_idx],
            'predicted_value': shap_values[instance_idx].base_values + 
                              shap_values[instance_idx].values.sum(),
            'top_positive_features': [c for c in contributions if c['shap_value'] > 0][:5],
            'top_negative_features': [c for c in contributions if c['shap_value'] < 0][:5],
            'all_contributions': contributions
        }
    
    def get_feature_importance(self, X: pd.DataFrame, 
                               method: str = 'shap') -> pd.DataFrame:
        """
        获取特征重要性
        
        Args:
            X: 特征数据
            method: 'shap', 'permutation', 'model'
        """
        if method == 'shap' and SHAP_AVAILABLE:
            return self._shap_importance(X)
        elif method == 'permutation':
            return self._permutation_importance(X)
        else:
            return self._model_importance()
    
    def _shap_importance(self, X: pd.DataFrame) -> pd.DataFrame:
        """基于SHAP的特征重要性"""
        if not SHAP_AVAILABLE:
            return pd.DataFrame()
        
        explainer = shap.Explainer(self.model, X)
        shap_values = explainer(X)
        
        # 计算平均绝对SHAP值
        importance = np.abs(shap_values.values).mean(axis=0)
        
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance,
            'method': 'SHAP'
        }).sort_values('importance', ascending=False)
    
    def _permutation_importance(self, X: pd.DataFrame, 
                                n_repeats: int = 10) -> pd.DataFrame:
        """
        基于置换的特征重要性
        随机打乱某一列，观察性能下降程度
        """
        from sklearn.metrics import mean_squared_error
        
        # 基准预测
        baseline_pred = self.model.predict(X)
        baseline_score = 0  # 简化处理
        
        importances = []
        
        for i, feature in enumerate(self.feature_names):
            scores = []
            
            for _ in range(n_repeats):
                # 复制数据并打乱该特征
                X_permuted = X.copy()
                X_permuted.iloc[:, i] = np.random.permutation(X_permuted.iloc[:, i])
                
                # 重新预测
                permuted_pred = self.model.predict(X_permuted)
                
                # 计算性能下降
                score = mean_squared_error(baseline_pred, permuted_pred)
                scores.append(score)
            
            importances.append({
                'feature': feature,
                'importance': np.mean(scores),
                'std': np.std(scores),
                'method': 'permutation'
            })
        
        return pd.DataFrame(importances).sort_values('importance', ascending=False)
    
    def _model_importance(self) -> pd.DataFrame:
        """从模型直接获取特征重要性"""
        if hasattr(self.model, 'feature_importances_'):
            # 树模型
            importance = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            # 线性模型
            importance = np.abs(self.model.coef_)
        else:
            return pd.DataFrame()
        
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance,
            'method': 'model'
        }).sort_values('importance', ascending=False)
    
    def analyze_feature_interaction(self, X: pd.DataFrame, 
                                    feature1: str, 
                                    feature2: str) -> Dict:
        """
        分析两个特征的交互效应
        """
        if not SHAP_AVAILABLE:
            return {"error": "SHAP未安装"}
        
        # 获取特征索引
        idx1 = self.feature_names.index(feature1)
        idx2 = self.feature_names.index(feature2)
        
        # 计算SHAP交互值
        explainer = shap.TreeExplainer(self.model) if hasattr(self.model, 'tree_') else \
                   shap.Explainer(self.model, X)
        
        shap_values = explainer(X)
        
        # 计算相关系数
        feature_values_1 = X[feature1].values
        feature_values_2 = X[feature2].values
        shap_values_1 = shap_values.values[:, idx1]
        shap_values_2 = shap_values.values[:, idx2]
        
        correlation = np.corrcoef(feature_values_1 * feature_values_2, 
                                 shap_values_1 + shap_values_2)[0, 1]
        
        return {
            'feature1': feature1,
            'feature2': feature2,
            'interaction_strength': abs(correlation),
            'correlation': correlation,
            'interpretation': '强交互' if abs(correlation) > 0.5 else '弱交互'
        }
    
    def generate_report(self, X: pd.DataFrame, 
                       y: Optional[pd.Series] = None) -> Dict:
        """生成完整的模型解释报告"""
        report = {
            'model_type': type(self.model).__name__,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names
        }
        
        # 1. 特征重要性
        importance_df = self.get_feature_importance(X)
        report['feature_importance'] = importance_df.to_dict('records')
        
        # 2. 重要特征分析
        top_features = importance_df.head(5)['feature'].tolist()
        report['top_features'] = top_features
        
        # 3. 特征统计
        feature_stats = []
        for feature in self.feature_names:
            stats = {
                'feature': feature,
                'mean': X[feature].mean(),
                'std': X[feature].std(),
                'min': X[feature].min(),
                'max': X[feature].max()
            }
            feature_stats.append(stats)
        report['feature_statistics'] = feature_stats
        
        # 4. 预测解释示例（最新样本）
        if SHAP_AVAILABLE:
            explanation = self.explain_prediction(X, instance_idx=-1)
            report['latest_prediction_explanation'] = explanation
        
        return report


class FeatureAnalyzer:
    """特征分析工具"""
    
    @staticmethod
    def correlation_analysis(df: pd.DataFrame, 
                            target: str = None) -> pd.DataFrame:
        """相关性分析"""
        corr_matrix = df.corr()
        
        if target:
            # 返回与目标变量的相关性
            target_corr = corr_matrix[target].drop(target)
            return target_corr.abs().sort_values(ascending=False)
        
        return corr_matrix
    
    @staticmethod
    def feature_redundancy(df: pd.DataFrame, 
                          threshold: float = 0.95) -> List[Dict]:
        """
        检测冗余特征（高度相关）
        
        Returns:
            冗余特征对列表
        """
        corr_matrix = df.corr().abs()
        
        redundant_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                if corr_matrix.iloc[i, j] > threshold:
                    redundant_pairs.append({
                        'feature1': corr_matrix.columns[i],
                        'feature2': corr_matrix.columns[j],
                        'correlation': corr_matrix.iloc[i, j]
                    })
        
        return redundant_pairs
    
    @staticmethod
    def feature_stability(df: pd.DataFrame, 
                         window: int = 30) -> pd.DataFrame:
        """
        分析特征稳定性（滚动窗口标准差）
        """
        stability = df.rolling(window=window).std().mean()
        return stability.sort_values(ascending=True)


# 便捷函数
def explain_model_prediction(model, X: pd.DataFrame, 
                            feature_names: List[str] = None,
                            instance_idx: int = -1) -> Dict:
    """
    便捷函数：解释模型预测
    
    Example:
        explanation = explain_model_prediction(
            trained_model, 
            X_test,
            feature_names=['feature1', 'feature2', ...]
        )
    """
    if feature_names is None:
        feature_names = list(X.columns)
    
    explainer = ModelExplainer(model, feature_names)
    return explainer.explain_prediction(X, instance_idx)


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("模型解释性分析测试")
    print("="*60)
    
    from sklearn.ensemble import RandomForestRegressor
    
    # 生成测试数据
    np.random.seed(42)
    n_samples = 200
    n_features = 10
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = X['feature_0'] * 2 + X['feature_1'] * -1 + np.random.randn(n_samples) * 0.1
    
    # 训练模型
    print("\n训练测试模型...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # 创建解释器
    explainer = ModelExplainer(model, list(X.columns))
    
    # 1. 特征重要性
    print("\n1. 特征重要性分析:")
    importance = explainer.get_feature_importance(X, method='model')
    print(importance.head())
    
    # 2. 预测解释
    print("\n2. 单个预测解释:")
    if SHAP_AVAILABLE:
        explanation = explainer.explain_prediction(X, instance_idx=0)
        print(f"基础值: {explanation['base_value']:.4f}")
        print(f"预测值: {explanation['predicted_value']:.4f}")
        print("\nTop 3 正向贡献特征:")
        for feat in explanation['top_positive_features'][:3]:
            print(f"  {feat['feature']}: {feat['shap_value']:+.4f}")
    else:
        print("SHAP未安装，跳过")
    
    # 3. 特征分析
    print("\n3. 特征相关性分析:")
    analyzer = FeatureAnalyzer()
    corr = analyzer.correlation_analysis(X, target='feature_0')
    print(corr.head())
    
    # 4. 冗余检测
    print("\n4. 冗余特征检测:")
    # 添加一个高度相关的特征
    X['feature_0_copy'] = X['feature_0'] * 0.99
    redundant = analyzer.feature_redundancy(X, threshold=0.9)
    for pair in redundant:
        print(f"  {pair['feature1']} - {pair['feature2']}: {pair['correlation']:.3f}")
    
    # 5. 完整报告
    print("\n5. 生成完整报告...")
    X = X.drop('feature_0_copy', axis=1)
    explainer = ModelExplainer(model, list(X.columns))
    report = explainer.generate_report(X, y)
    print(f"报告包含 {len(report['feature_importance'])} 个特征")
    print(f"Top 3 重要特征: {report['top_features'][:3]}")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
