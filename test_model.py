from copper_price_model import CopperPriceModel
import json

model = CopperPriceModel()

print("=" * 60)
print("铜价格预测模型测试 - 升级版")
print("=" * 60)

# 测试短期预测
print("\n【短期预测(5天)】")
result = model.predict_short_term(days=5)
print(json.dumps(result, indent=2, ensure_ascii=False))

# 测试中期预测
print("\n【中期预测(3个月)】")
result = model.predict_medium_term(months=3)
print(json.dumps(result, indent=2, ensure_ascii=False))

# 测试长期预测
print("\n【长期预测(1年)】")
result = model.predict_long_term(years=1)
print(json.dumps(result, indent=2, ensure_ascii=False))

# 市场评估
print("\n【市场评估报告】")
assessment = model.get_market_assessment()
print(json.dumps(assessment, indent=2, ensure_ascii=False))

# 因子分析
print("\n【因子分析报告】")
factor_analysis = model.get_factor_analysis()
print(json.dumps(factor_analysis, indent=2, ensure_ascii=False))

# 压力测试
print("\n【压力测试】")
stress_test = model.stress_test()
print(json.dumps(stress_test, indent=2, ensure_ascii=False))

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
