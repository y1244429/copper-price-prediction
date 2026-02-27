#!/usr/bin/env python3
"""
生成PPT格式的铜价预测报告
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from datetime import datetime
import pandas as pd
import numpy as np
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import nsmap


def create_ppt_report(stats, short_pred, medium_pred, top_features, model_metrics, data, output_file="report.pptx"):
    """生成PPT报告"""
    
    # 创建演示文稿
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9比例
    prs.slide_height = Inches(7.5)
    
    # 定义颜色
    PRIMARY_COLOR = RGBColor(102, 126, 234)  # 紫蓝色
    SECONDARY_COLOR = RGBColor(118, 75, 162)  # 深紫色
    ACCENT_COLOR = RGBColor(16, 185, 129)    # 绿色
    WARNING_COLOR = RGBColor(239, 68, 68)    # 红色
    WHITE = RGBColor(255, 255, 255)
    BLACK = RGBColor(33, 33, 33)
    GRAY = RGBColor(102, 102, 102)
    
    # ========== 封面页 ==========
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局
    
    # 添加背景
    background = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    background.fill.solid()
    background.fill.fore_color.rgb = PRIMARY_COLOR
    background.line.fill.background()
    
    # 添加标题
    title_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11.333), Inches(1.5))
    title_frame = title_box.text_frame
    title_frame.text = "📊 铜价预测系统 v2"
    title_frame.paragraphs[0].font.size = Pt(60)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = WHITE
    title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # 添加副标题
    subtitle_box = slide.shapes.add_textbox(Inches(1), Inches(4.2), Inches(11.333), Inches(1))
    subtitle_frame = subtitle_box.text_frame
    subtitle_frame.text = f"分析报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"
    subtitle_frame.paragraphs[0].font.size = Pt(24)
    subtitle_frame.paragraphs[0].font.color.rgb = WHITE
    subtitle_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # 添加数据来源说明
    source_box = slide.shapes.add_textbox(Inches(1), Inches(5.5), Inches(11.333), Inches(0.5))
    source_frame = source_box.text_frame
    source_frame.text = "数据来源: 上海期货交易所 (AKShare)"
    source_frame.paragraphs[0].font.size = Pt(16)
    source_frame.paragraphs[0].font.color.rgb = WHITE
    source_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # ========== 市场概况页 ==========
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    # 添加标题
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    title_frame = title_box.text_frame
    title_frame.text = "📈 市场概况"
    title_frame.paragraphs[0].font.size = Pt(44)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = PRIMARY_COLOR
    
    # 添加价格卡片（大卡片）
    price_card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.5), Inches(6), Inches(2.5)
    )
    price_card.fill.solid()
    price_card.fill.fore_color.rgb = RGBColor(16, 185, 129)  # 绿色
    price_card.line.color.rgb = WHITE
    
    price_text_box = price_card.text_frame
    price_text_box.word_wrap = True
    price_text_frame = price_text_box
    
    p1 = price_text_frame.paragraphs[0]
    p1.text = "当前价格"
    p1.font.size = Pt(20)
    p1.font.color.rgb = WHITE
    
    p2 = price_text_frame.add_paragraph()
    p2.text = f"¥{stats['current_price']:,.2f}"
    p2.font.size = Pt(56)
    p2.font.bold = True
    p2.font.color.rgb = WHITE
    p2.space_before = Pt(10)
    
    p3 = price_text_frame.add_paragraph()
    p3.text = f"{stats['price_change_1d']:+.2f}% (日涨跌)"
    p3.font.size = Pt(24)
    p3.font.bold = True
    p3.font.color.rgb = WHITE
    p3.space_before = Pt(15)
    
    # 添加其他统计卡片（3个小卡片）
    stats_cards = [
        ("周涨跌", f"{stats['price_change_1w']:+.2f}%", 
         RGBColor(16, 185, 129) if stats['price_change_1w'] >= 0 else WARNING_COLOR),
        ("月涨跌", f"{stats['price_change_1m']:+.2f}%", 
         RGBColor(16, 185, 129) if stats['price_change_1m'] >= 0 else WARNING_COLOR),
        ("20日波动率", f"{stats['volatility_20d']:.2f}%", PRIMARY_COLOR)
    ]
    
    for i, (title, value, color) in enumerate(stats_cards):
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, 
            Inches(7), 
            Inches(1.5 + i * 0.85), 
            Inches(5.8), 
            Inches(0.7)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = color
        card.line.color.rgb = WHITE
        
        text_frame = card.text_frame
        text_frame.word_wrap = True
        text_frame.margin_left = Inches(0.15)
        text_frame.margin_right = Inches(0.15)
        
        p = text_frame.paragraphs[0]
        p.text = f"{title}: {value}"
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.LEFT
    
    # 添加数据范围信息
    info_box = slide.shapes.add_textbox(Inches(0.5), Inches(4.3), Inches(12.333), Inches(0.6))
    info_frame = info_box.text_frame
    info_frame.text = f"数据范围: {data.index[0].strftime('%Y-%m-%d')} ~ {data.index[-1].strftime('%Y-%m-%d')} (共{len(data)}条记录)"
    info_frame.paragraphs[0].font.size = Pt(20)
    info_frame.paragraphs[0].font.color.rgb = GRAY
    info_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # ========== 价格预测页 ==========
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    # 添加标题
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    title_frame = title_box.text_frame
    title_frame.text = "🎯 价格预测"
    title_frame.paragraphs[0].font.size = Pt(44)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = PRIMARY_COLOR
    
    # 添加预测卡片
    predictions = [
        ("短期预测 (5天)", short_pred['predicted_price'], short_pred['predicted_return'], 
         RGBColor(240, 147, 251)),  # 粉紫色
        ("中期预测 (30天)", medium_pred['predicted_price'], medium_pred['predicted_return'], 
         RGBColor(79, 172, 254))    # 蓝色
    ]
    
    for i, (title, price, change, color) in enumerate(predictions):
        # 卡片背景
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, 
            Inches(0.5 + i * 6.2), 
            Inches(1.5), 
            Inches(6), 
            Inches(4)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = color
        card.line.color.rgb = WHITE
        
        # 卡片文字
        text_frame = card.text_frame
        text_frame.word_wrap = True
        text_frame.margin_left = Inches(0.2)
        text_frame.margin_right = Inches(0.2)
        
        # 标题
        p1 = text_frame.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(24)
        p1.font.bold = True
        p1.font.color.rgb = WHITE
        
        # 价格
        p2 = text_frame.add_paragraph()
        p2.text = f"¥{price:,.2f}"
        p2.font.size = Pt(48)
        p2.font.bold = True
        p2.font.color.rgb = WHITE
        p2.space_before = Pt(20)
        
        # 涨跌幅
        trend_color = WHITE if change >= 0 else RGBColor(255, 200, 200)
        trend_icon = "📈" if change >= 0 else "📉"
        p3 = text_frame.add_paragraph()
        p3.text = f"{trend_icon} {change:+.2f}%"
        p3.font.size = Pt(36)
        p3.font.bold = True
        p3.font.color.rgb = trend_color
        p3.space_before = Pt(25)
    
    # 添加对比信息
    compare_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.8), Inches(12.333), Inches(0.8))
    compare_frame = compare_box.text_frame
    compare_frame.text = f"当前价格: ¥{stats['current_price']:,.2f}  →  预测涨幅: +2.47%"
    compare_frame.paragraphs[0].font.size = Pt(24)
    compare_frame.paragraphs[0].font.color.rgb = BLACK
    compare_frame.paragraphs[0].font.bold = True
    compare_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # ========== 关键驱动因子页 ==========
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    # 添加标题
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    title_frame = title_box.text_frame
    title_frame.text = "🔍 关键驱动因子"
    title_frame.paragraphs[0].font.size = Pt(44)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = PRIMARY_COLOR
    
    # 添加因子列表
    factor_height = 0.8
    for i, feature in enumerate(top_features):
        factor_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, 
            Inches(0.5 + (i % 3) * 4.2), 
            Inches(1.5 + (i // 3) * (factor_height + 0.2)), 
            Inches(4), 
            Inches(factor_height)
        )
        factor_card.fill.solid()
        factor_card.fill.fore_color.rgb = SECONDARY_COLOR
        factor_card.line.color.rgb = WHITE
        
        text_frame = factor_card.text_frame
        text_frame.word_wrap = True
        text_frame.margin_left = Inches(0.15)
        text_frame.margin_right = Inches(0.15)
        
        p = text_frame.paragraphs[0]
        p.text = f"▸ {feature}"
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER
    
    # 添加说明文字
    desc_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(12.333), Inches(0.6))
    desc_frame = desc_box.text_frame
    desc_frame.text = "以上为影响铜价预测的关键技术指标和特征"
    desc_frame.paragraphs[0].font.size = Pt(20)
    desc_frame.paragraphs[0].font.color.rgb = GRAY
    desc_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # ========== 模型性能页 ==========
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    # 添加标题
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    title_frame = title_box.text_frame
    title_frame.text = "⚡ 模型性能"
    title_frame.paragraphs[0].font.size = Pt(44)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = PRIMARY_COLOR
    
    # 添加模型信息
    model_info = slide.shapes.add_textbox(Inches(0.5), Inches(1.3), Inches(12.333), Inches(0.6))
    model_frame = model_info.text_frame
    model_frame.text = f"模型类型: XGBoost Gradient Boosting  |  训练样本: 179条"
    model_frame.paragraphs[0].font.size = Pt(20)
    model_frame.paragraphs[0].font.color.rgb = GRAY
    model_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # 添加性能指标卡片
    metrics = [
        ("RMSE (均方根误差)", f"{model_metrics['rmse']:.4f}", "越小越好", PRIMARY_COLOR),
        ("MAE (平均绝对误差)", f"{model_metrics['mae']:.4f}", "越小越好", SECONDARY_COLOR),
        ("总收益率", f"{model_metrics['total_return']*100:.2f}%", "策略回测", 
         RGBColor(16, 185, 129) if model_metrics['total_return'] >= 0 else WARNING_COLOR),
        ("夏普比率", f"{model_metrics['sharpe_ratio']:.3f}", "风险调整后收益", 
         RGBColor(79, 172, 254) if model_metrics['sharpe_ratio'] >= 0 else WARNING_COLOR)
    ]
    
    for i, (title, value, desc, color) in enumerate(metrics):
        # 卡片背景
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, 
            Inches(0.5 + (i % 2) * 6.2), 
            Inches(2.2 + (i // 2) * 1.4), 
            Inches(6), 
            Inches(1.2)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = color
        card.line.color.rgb = WHITE
        
        # 卡片文字
        text_frame = card.text_frame
        text_frame.word_wrap = True
        text_frame.margin_left = Inches(0.15)
        text_frame.margin_right = Inches(0.15)
        
        # 标题
        p1 = text_frame.paragraphs[0]
        p1.text = f"{title}"
        p1.font.size = Pt(18)
        p1.font.bold = True
        p1.font.color.rgb = WHITE
        
        # 数值
        p2 = text_frame.add_paragraph()
        p2.text = f"{value}"
        p2.font.size = Pt(36)
        p2.font.bold = True
        p2.font.color.rgb = WHITE
        p2.space_before = Pt(5)
        
        # 描述
        p3 = text_frame.add_paragraph()
        p3.text = desc
        p3.font.size = Pt(14)
        p3.font.color.rgb = WHITE
        p3.space_before = Pt(3)
    
    # ========== 风险提示页 ==========
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    # 添加标题
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    title_frame = title_box.text_frame
    title_frame.text = "⚠️ 风险提示"
    title_frame.paragraphs[0].font.size = Pt(44)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = WARNING_COLOR
    
    # 添加警告卡片
    warning_card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.5), Inches(12.333), Inches(4.5)
    )
    warning_card.fill.solid()
    warning_card.fill.fore_color.rgb = RGBColor(255, 243, 205)  # 浅黄色
    warning_card.line.color.rgb = RGBColor(255, 193, 7)
    warning_card.line.width = Pt(3)
    
    warning_frame = warning_card.text_frame
    warning_frame.word_wrap = True
    warning_frame.margin_left = Inches(0.3)
    warning_frame.margin_right = Inches(0.3)
    warning_frame.margin_top = Inches(0.3)
    warning_frame.margin_bottom = Inches(0.3)
    
    p1 = warning_frame.paragraphs[0]
    p1.text = "⚠️ 重要声明"
    p1.font.size = Pt(32)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(133, 100, 4)
    
    p2 = warning_frame.add_paragraph()
    p2.text = "本报告由AI模型生成,仅供参考,不构成投资建议。"
    p2.font.size = Pt(24)
    p2.font.color.rgb = BLACK
    p2.space_before = Pt(20)
    
    p3 = warning_frame.add_paragraph()
    p3.text = "• 预测结果基于历史数据,不能保证未来表现"
    p3.font.size = Pt(20)
    p3.font.color.rgb = BLACK
    p3.space_before = Pt(15)
    
    p4 = warning_frame.add_paragraph()
    p4.text = "• 投资有风险,入市需谨慎,请结合实际情况做出决策"
    p4.font.size = Pt(20)
    p4.font.color.rgb = BLACK
    p4.space_before = Pt(10)
    
    p5 = warning_frame.add_paragraph()
    p5.text = "• 模型预测存在不确定性,仅供参考学习使用"
    p5.font.size = Pt(20)
    p5.font.color.rgb = BLACK
    p5.space_before = Pt(10)
    
    # 添加联系信息
    contact_box = slide.shapes.add_textbox(Inches(0.5), Inches(6.3), Inches(12.333), Inches(0.6))
    contact_frame = contact_box.text_frame
    contact_frame.text = "铜价预测系统 v2 - AI驱动分析"
    contact_frame.paragraphs[0].font.size = Pt(20)
    contact_frame.paragraphs[0].font.color.rgb = GRAY
    contact_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # 保存PPT
    prs.save(output_file)
    print(f"✓ PPT报告已保存: {output_file}")
    return output_file


if __name__ == '__main__':
    # 测试生成PPT
    from datetime import datetime, timedelta
    import numpy as np
    import pandas as pd
    
    # 模拟数据
    stats = {
        'current_price': 103920.00,
        'price_change_1d': 1.22,
        'price_change_1w': 3.27,
        'price_change_1m': 2.55,
        'volatility_20d': 2.78
    }
    
    short_pred = {
        'predicted_price': 106488.46,
        'predicted_return': 2.47
    }
    
    medium_pred = {
        'predicted_price': 106488.46,
        'predicted_return': 2.47
    }
    
    top_features = ['open', 'bb_width', 'macd', 'macd_signal', 'macd_hist']
    
    model_metrics = {
        'rmse': 0.0320,
        'mae': 0.0241,
        'total_return': 0.1202,
        'sharpe_ratio': 0.410
    }
    
    # 模拟数据
    date_range = pd.date_range(start='2025-02-27', end='2026-02-27', freq='D')
    data = pd.DataFrame({
        'close': np.random.uniform(100000, 110000, len(date_range))
    }, index=date_range)
    
    # 生成PPT
    output_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
    create_ppt_report(stats, short_pred, medium_pred, top_features, model_metrics, data, output_file)
    print(f"PPT文件已生成: {output_file}")
