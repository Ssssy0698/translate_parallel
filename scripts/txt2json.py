#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本文件转JSON脚本
将.txt文件转换为指定格式的JSON
使用方法: python txt_to_json.py input.txt [output.json]
"""

import json
import sys
import os
import re

def process_text_file(input_file, output_file=None):
    """
    处理文本文件，转换为指定的JSON格式
    """
    # 如果未指定输出文件，则自动生成
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.json"
    
    print(f"📄 输入文件: {input_file}")
    print(f"💾 输出文件: {output_file}")
    
    # 读取文本文件
    lines = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(input_file, 'r', encoding='gbk') as f:
                lines = [line.strip() for line in f if line.strip()]
        except UnicodeDecodeError:
            print(f"❌ 错误: 无法解码文件 '{input_file}'，请检查文件编码")
            return False
    
    if not lines:
        print(f"❌ 错误: 文件 '{input_file}' 为空或只包含空行")
        return False
    
    print(f"📊 读取到 {len(lines)} 行有效数据")
    
    # 构建JSON数据
    json_data = {
        "type": "CCMatrix",
        "data": lines
    }
    
    # 写入JSON文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON文件已成功生成!")
        
        # 显示生成的JSON内容
        print("\n📝 生成的JSON内容预览:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ 错误: 写入JSON文件时出错 - {e}")
        return False
    
    return True

def main():
    """
    主函数
    """
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python txt_to_json.py <输入文件> [输出文件]")
        print("示例: python txt_to_json.py input.txt")
        print("示例: python txt_to_json.py input.txt output.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 错误: 输入文件 '{input_file}' 不存在")
        sys.exit(1)
    
    # 检查输入文件扩展名
    if not input_file.endswith('.txt'):
        print(f"⚠️  警告: 输入文件不是.txt格式: {input_file}")
        response = input("是否继续处理？(y/n): ")
        if response.lower() != 'y':
            print("已取消")
            sys.exit(0)
    
    # 获取输出文件名（如果提供了）
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 处理文件
    if process_text_file(input_file, output_file):
        print(f"\n🎉 转换完成!")
    else:
        print(f"\n❌ 转换失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()