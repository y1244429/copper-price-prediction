#!/usr/bin/env python3
"""
全球铜库存分析脚本
用法: python analyze_inventory.py [comex] [bonded] [social]
示例: python analyze_inventory.py 80000 120000 250000
"""

import sys
from data.global_inventory_analyzer import analyze_copper_inventory

def main():
    # 默认库存值（吨）
    comex = 80000      # COMEX库存
    bonded = 120000    # 保税区库存  
    social = 250000    # 社会库存
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        comex = float(sys.argv[1])
    if len(sys.argv) > 2:
        bonded = float(sys.argv[2])
    if len(sys.argv) > 3:
        social = float(sys.argv[3])
    
    print(f"📊 使用参数:")
    print(f"   COMEX库存: {comex:,.0f} 吨 ({comex/10000:.1f} 万吨)")
    print(f"   保税区库存: {bonded:,.0f} 吨 ({bonded/10000:.1f} 万吨)")
    print(f"   社会库存: {social:,.0f} 吨 ({social/10000:.1f} 万吨)")
    print()
    
    # 生成报告
    report = analyze_copper_inventory(comex, bonded, social)
    print(report)

if __name__ == '__main__':
    main()
