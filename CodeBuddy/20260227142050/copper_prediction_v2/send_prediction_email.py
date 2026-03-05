#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铜价预测邮件发送脚本
"""

import sys
from pathlib import Path
from datetime import datetime
import glob
import os


def find_latest_prediction_files():
    """查找最新的预测结果文件"""
    # 项目目录
    base_dir = Path(__file__).parent
    
    # 查找今天生成的文件
    today = datetime.now().strftime("%Y%m%d")
    
    pattern = f"**/*{today}*.*"
    files = []
    
    for file_path in base_dir.rglob(f"*{today}*"):
        if file_path.suffix in ['.txt', '.html', '.pptx']:
            files.append(str(file_path))
    
    # 如果没有找到今天的文件，查找最近的文件
    if not files:
        # 查找所有txt/html/pptx文件
        for file_path in base_dir.rglob("*.txt"):
            if "prediction" in file_path.name.lower() or "report" in file_path.name.lower():
                files.append(str(file_path))
        for file_path in base_dir.rglob("*.html"):
            if "prediction" in file_path.name.lower() or "report" in file_path.name.lower():
                files.append(str(file_path))
        for file_path in base_dir.rglob("*.pptx"):
            files.append(str(file_path))
    
    return files


def send_prediction_email():
    """发送铜价预测邮件"""
    try:
        # 导入邮件发送模块
        base_dir = Path(__file__).parent
        email_sender_path = base_dir / "email_sender.py"
        
        # 如果没有email_sender.py，则查找新闻项目的
        if not email_sender_path.exists():
            news_dir = base_dir.parent.parent / "20260301115643"
            email_sender_path = news_dir / "email_sender.py"
        
        if not email_sender_path.exists():
            print("邮件发送模块不存在")
            return False
        
        sys.path.insert(0, str(email_sender_path.parent))
        from email_sender import EmailSender, load_email_config
        
        # 加载邮件配置
        config = load_email_config()
        
        # 检查是否启用邮件发送
        if not config.get('send_copper_prediction', False):
            print("铜价预测邮件发送未启用")
            return False
        
        # 检查配置是否完整
        required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'receiver_email']
        for field in required_fields:
            if not config.get(field):
                print(f"邮件配置不完整（缺少 {field}）")
                return False
        
        # 查找预测结果文件
        print("正在查找预测结果文件...")
        prediction_files = find_latest_prediction_files()
        
        if not prediction_files:
            print("未找到预测结果文件")
            return False
        
        print(f"找到 {len(prediction_files)} 个文件:")
        for f in prediction_files:
            print(f"  - {f}")
        
        # 创建邮件发送器
        email_sender = EmailSender(
            smtp_server=config['smtp_server'],
            smtp_port=config['smtp_port'],
            sender_email=config['sender_email'],
            sender_password=config['sender_password']
        )
        
        # 发送邮件
        print("正在发送铜价预测邮件...")
        success, message = email_sender.send_copper_prediction_email(
            to_email=config['receiver_email'],
            prediction_result_files=prediction_files
        )
        
        if success:
            print(f"✅ 铜价预测邮件发送成功")
            return True
        else:
            print(f"❌ 铜价预测邮件发送失败: {message}")
            return False
        
    except Exception as e:
        print(f"发送邮件时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("铜价预测邮件发送")
    print("=" * 50)
    print()
    
    success = send_prediction_email()
    
    print()
    print("=" * 50)
    if success:
        print("邮件发送完成！")
    else:
        print("邮件发送失败！")
    print("=" * 50)
