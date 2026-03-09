#!/usr/bin/env python3
"""
COMEX铜库存手动更新工具
"""

import json
import os
from datetime import datetime

def update_comex_inventory():
    """手动更新COMEX铜库存数据"""
    
    print('='*70)
    print('📦 COMEX铜库存手动更新')
    print('='*70)
    print()
    
    # 读取当前配置
    config_path = 'data/comex_config.json'
    current_value = 80000  # 默认8万吨
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            current_value = config.get('inventory_tons', 80000)
    
    print(f'当前COMEX库存值: {current_value:,.0f} 吨 ({current_value/10000:.1f} 万吨)')
    print()
    
    # 提供数据源信息
    print('📊 官方数据源:')
    print('  1. CME Group官网:')
    print('     https://www.cmegroup.com/markets/metals/base/copper.html')
    print('     → 点击 Reports → Stocks & Inventories')
    print()
    print('  2. Trading Economics:')
    print('     https://tradingeconomics.com/commodity/copper')
    print()
    print('  3. SMM上海有色网:')
    print('     https://www.smm.cn/copper')
    print()
    
    # 参考值（基于历史数据）
    print('📈 近期参考值:')
    print('  2024年COMEX铜库存范围: 约 5-15 万吨')
    print('  2025年初至今平均: 约 8-10 万吨')
    print()
    
    # 获取用户输入
    while True:
        try:
            user_input = input(f'请输入最新COMEX铜库存（吨，直接回车保持 {current_value:,.0f}）: ')
            
            if user_input.strip() == '':
                new_value = current_value
                print(f'保持原值: {new_value:,.0f} 吨')
                break
            
            new_value = float(user_input)
            
            if new_value < 0 or new_value > 500000:
                print('❌ 输入值异常，请检查（合理范围: 0-50万吨）')
                continue
                
            print(f'✅ 新值: {new_value:,.0f} 吨 ({new_value/10000:.1f} 万吨)')
            break
            
        except ValueError:
            print('❌ 请输入有效数字')
    
    # 保存配置
    os.makedirs('data', exist_ok=True)
    config = {
        'inventory_tons': new_value,
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'manual_input',
        'note': 'COMEX Copper Warehouse Stocks'
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print()
    print(f'✅ 数据已保存到: {config_path}')
    print()
    
    # 是否立即运行分析
    run_analysis = input('是否立即运行库存分析? (y/n): ').lower().strip()
    
    if run_analysis == 'y':
        print()
        print('='*70)
        print('正在运行库存分析...')
        print('='*70)
        print()
        
        from data.global_inventory_analyzer import analyze_copper_inventory
        
        # 读取其他库存配置
        bonded = 120000  # 保税区默认值
        social = 250000  # 社会库存默认值
        
        report = analyze_copper_inventory(new_value, bonded, social)
        print(report)
    else:
        print()
        print('提示: 稍后可通过以下命令运行分析:')
        print('  python3 analyze_inventory.py')

if __name__ == '__main__':
    update_comex_inventory()
