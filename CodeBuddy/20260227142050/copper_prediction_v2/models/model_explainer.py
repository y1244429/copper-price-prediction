"""
模型解释器 - 使用SHAP等方法解释模型预测
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("SHAP未安装,模型解释功能不可用. 安装: pip install shap")


class ModelExplainer:
    """模型解释器 - 基于SHAP"""

    def __init__(self, model, feature_names: List[str]):
        """
        初始化解释器

        Args:
            model: 训练好的模型
            feature_names: 特征名称列表
        """
        self.model = model
        self.feature_names = feature_names
        self.explainer = None

        # 创建SHAP解释器
        self._init_explainer()

    def _init_explainer(self):
        """初始化SHAP解释器"""
        if not SHAP_AVAILABLE:
            return

        try:
            # 尝试使用TreeExplainer (适用于XGBoost)
            self.explainer = shap.TreeExplainer(self.model.model)
        except:
            # 如果失败,使用通用解释器
            self.explainer = None

    def explain_prediction(self, features: pd.DataFrame, instance_idx: int = -1) -> Dict:
        """
        解释单个预测

        Args:
            features: 特征数据
            instance_idx: 要解释的样本索引

        Returns:
            解释结果字典
        """
        if self.explainer is None:
            return self._simple_explanation(features, instance_idx)

        try:
            # 获取SHAP值
            shap_values = self.explainer.shap_values(features)

            # 获取单个样本的SHAP值
            instance_idx = instance_idx if instance_idx >= 0 else len(features) - 1
            instance_shap = shap_values[instance_idx]

            # 基础值
            base_value = self.explainer.expected_value

            # 按SHAP值绝对值排序特征
            shap_df = pd.DataFrame({
                'feature': self.feature_names,
                'shap_value': instance_shap
            })
            shap_df['abs_shap'] = shap_df['shap_value'].abs()
            shap_df = shap_df.sort_values('abs_shap', ascending=False)

            # 分类正向和负向特征
            top_positive = shap_df[shap_df['shap_value'] > 0].head(5).to_dict('records')
            top_negative = shap_df[shap_df['shap_value'] < 0].tail(5).to_dict('records')

            return {
                'base_value': float(base_value),
                'instance_idx': instance_idx,
                'top_positive_features': top_positive,
                'top_negative_features': top_negative,
                'feature_contributions': shap_df.to_dict('records')
            }

        except Exception as e:
            print(f"SHAP解释失败: {e}")
            return self._simple_explanation(features, instance_idx)

    def _simple_explanation(self, features: pd.DataFrame, instance_idx: int) -> Dict:
        """简单解释 (SHAP不可用时使用)"""
        instance_idx = instance_idx if instance_idx >= 0 else len(features) - 1

        # 使用特征值排序
        instance_values = features.iloc[instance_idx]
        values_df = pd.DataFrame({
            'feature': features.columns,
            'value': instance_values.values,
            'shap_value': 0  # 占位符
        })

        # 按绝对值排序
        values_df['abs_value'] = values_df['value'].abs()
        values_df = values_df.sort_values('abs_value', ascending=False)

        return {
            'base_value': 0,
            'instance_idx': instance_idx,
            'top_positive_features': values_df.head(5).to_dict('records'),
            'top_negative_features': [],
            'note': 'SHAP不可用,使用简单解释'
        }

    def get_feature_importance(self, features: pd.DataFrame = None) -> pd.DataFrame:
        """
        获取特征重要性

        Args:
            features: 特征数据 (可选)

        Returns:
            特征重要性DataFrame
        """
        if hasattr(self.model, 'get_feature_importance'):
            # 如果模型有自己的特征重要性方法
            return self.model.get_feature_importance()

        # 否则使用简单的统计方法
        if features is None:
            return pd.DataFrame(columns=['feature', 'importance'])

        # 计算特征的变异系数
        importance = features.std() / features.abs().mean()
        importance_df = pd.DataFrame({
            'feature': features.columns,
            'importance': importance.values
        })
        importance_df = importance_df.sort_values('importance', ascending=False)

        return importance_df


class FeatureAnalyzer:
    """特征分析工具"""

    def __init__(self, features: pd.DataFrame, target: pd.Series = None):
        """
        初始化分析器

        Args:
            features: 特征数据
            target: 目标变量 (可选)
        """
        self.features = features
        self.target = target

    def compute_correlation(self) -> pd.DataFrame:
        """
        计算特征相关性矩阵

        Returns:
            相关性矩阵
        """
        return self.features.corr()

    def find_redundant_features(self, threshold: float = 0.95) -> List[tuple]:
        """
        查找冗余特征

        Args:
            threshold: 相关性阈值

        Returns:
            冗余特征对列表
        """
        corr_matrix = self.compute_correlation()

        # 找出高相关的特征对
        redundant = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) > threshold:
                    redundant.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr
                    ))

        # 按相关性排序
        redundant.sort(key=lambda x: abs(x[2]), reverse=True)

        return redundant

    def analyze_feature_importance(self) -> pd.DataFrame:
        """
        分析特征重要性 (基于随机森林)

        Returns:
            特征重要性DataFrame
        """
        try:
            from sklearn.ensemble import RandomForestRegressor

            rf = RandomForestRegressor(n_estimators=100, random_state=42)
            X = self.features.fillna(0)
            y = self.target if self.target is not None else self.features.iloc[:, 0]

            rf.fit(X, y)

            importance_df = pd.DataFrame({
                'feature': X.columns,
                'importance': rf.feature_importances_
            })
            importance_df = importance_df.sort_values('importance', ascending=False)

            return importance_df

        except Exception as e:
            print(f"特征重要性分析失败: {e}")
            return pd.DataFrame(columns=['feature', 'importance'])

    def compute_stability(self, n_samples: int = 100) -> Dict:
        """
        计算特征稳定性

        Args:
            n_samples: 采样次数

        Returns:
            稳定性指标字典
        """
        np.random.seed(42)
        n = len(self.features)

        # 多次采样计算特征重要性
        importances_list = []

        for _ in range(n_samples):
            # Bootstrap采样
            indices = np.random.choice(n, n, replace=True)
            sample_features = self.features.iloc[indices]

            # 计算变异系数
            importance = sample_features.std() / (sample_features.abs().mean() + 1e-10)
            importances_list.append(importance)

        # 计算稳定性 (变异系数的标准差 / 均值)
        importances_array = np.array(importances_list)
        mean_importance = importances_array.mean(axis=0)
        std_importance = importances_array.std(axis=0)
        stability = std_importance / (mean_importance + 1e-10)

        stability_df = pd.DataFrame({
            'feature': self.features.columns,
            'mean_importance': mean_importance,
            'std_importance': std_importance,
            'stability_score': stability
        })
        stability_df = stability_df.sort_values('stability_score')

        return {
            'stability': stability_df,
            'stable_features': stability_df.head(10)['feature'].tolist(),
            'unstable_features': stability_df.tail(10)['feature'].tolist()
        }

    def generate_report(self) -> str:
        """
        生成特征分析报告

        Returns:
            报告字符串
        """
        report = []
        report.append("=" * 60)
        report.append("特征分析报告")
        report.append("=" * 60)

        # 1. 基本统计
        report.append("\n【特征统计】")
        report.append(f"特征数量: {len(self.features.columns)}")
        report.append(f"样本数量: {len(self.features)}")
        report.append(f"缺失值数量: {self.features.isnull().sum().sum()}")

        # 2. 相关性分析
        report.append("\n【冗余特征分析】")
        redundant = self.find_redundant_features(threshold=0.9)
        if redundant:
            report.append(f"发现 {len(redundant)} 对高相关特征:")
            for feat1, feat2, corr in redundant[:5]:
                report.append(f"  - {feat1} <-> {feat2}: {corr:.3f}")
        else:
            report.append("未发现高相关特征")

        # 3. 特征重要性
        report.append("\n【特征重要性 (Top 10)】")
        importance = self.analyze_feature_importance()
        if not importance.empty:
            for idx, row in importance.head(10).iterrows():
                report.append(f"  {row['feature']}: {row['importance']:.4f}")

        # 4. 特征稳定性
        report.append("\n【特征稳定性分析】")
        stability = self.compute_stability()
        report.append("  最稳定特征:")
        for feat in stability['stable_features'][:5]:
            report.append(f"    - {feat}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)


# 便捷函数
def explain_model_prediction(model, features: pd.DataFrame,
                            feature_names: List[str],
                            instance_idx: int = -1) -> Dict:
    """
    快速解释模型预测

    Args:
        model: 训练好的模型
        features: 特征数据
        feature_names: 特征名称列表
        instance_idx: 要解释的样本索引

    Returns:
        解释结果
    """
    explainer = ModelExplainer(model, feature_names)
    return explainer.explain_prediction(features, instance_idx)


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("模型解释器测试")
    print("="*60)

    # 生成测试数据
    from models.copper_model_v2 import XGBoostModel, FeatureEngineer
    from data.data_sources import MockDataSource

    # 加载数据
    mock_source = MockDataSource()
    data = mock_source.fetch_copper_price(start_date="2023-01-01", end_date="2024-01-01")

    # 特征工程
    feature_engineer = FeatureEngineer()
    features = feature_engineer.create_features(data)

    # 生成目标
    target = (data['close'].shift(-5) / data['close'] - 1).loc[features.index]

    # 训练模型
    print("\n训练模型...")
    model = XGBoostModel()
    model.train(features, target)

    # 模型解释
    print("\n模型解释:")
    explainer = ModelExplainer(model, features.columns.tolist())
    explanation = explainer.explain_prediction(features)

    if 'top_positive_features' in explanation:
        print("\n正向驱动因素:")
        for feat in explanation['top_positive_features'][:5]:
            print(f"  {feat['feature']}: {feat.get('shap_value', feat['value']):+.4f}")

    # 特征分析
    print("\n特征分析:")
    analyzer = FeatureAnalyzer(features, target)
    report = analyzer.generate_report()
    print(report)

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
