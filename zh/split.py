#!/usr/bin/env python3
"""
JSON文件拆分工具
将大型JSON文件拆分为多个小文件，保存在原始文件同一目录下
"""

import json
import math
import os
import sys

def split_json_file(input_file, chunk_size=4500):
    """
    将大型JSON文件拆分为多个小文件
    
    Args:
        input_file: 输入JSON文件路径
        chunk_size: 每个文件包含的数据条数，默认为60000
    """
    
    try:
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            print(f"错误: 输入文件 '{input_file}' 不存在")
            return False
        
        # 获取文件所在目录和文件名信息
        input_dir = os.path.dirname(input_file) or "."
        input_filename = os.path.basename(input_file)
        input_name, input_ext = os.path.splitext(input_filename)
        
        print(f"正在处理文件: {input_filename}")
        
        # 读取原始JSON文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取type和data字段
        json_type = data.get("type", "")
        json_data = data.get("data", [])
        
        # 检查data字段是否存在
        if not isinstance(json_data, list):
            print("错误: JSON文件的'data'字段不是数组格式")
            return False
        
        # 计算需要拆分成多少个文件
        total_items = len(json_data)
        
        if total_items == 0:
            print("警告: JSON文件中没有数据")
            return True
        
        if total_items <= chunk_size:
            print(f"文件数据量({total_items}条)小于等于拆分阈值({chunk_size}条)，无需拆分")
            return True
        
        num_chunks = math.ceil(total_items / chunk_size)
        
        print(f"原始文件包含 {total_items} 条数据")
        print(f"将拆分为 {num_chunks} 个文件，每个文件最多 {chunk_size} 条数据")
        print(f"输出目录: {input_dir}")
        
        # 计算序号位数，用于文件名格式化
        max_digits = len(str(num_chunks))
        
        # 拆分数据
        for i in range(num_chunks):
            # 计算当前块的起始和结束索引
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total_items)
            
            # 提取当前块的数据
            chunk_data = json_data[start_idx:end_idx]
            
            # 构建新的JSON结构
            chunk_json = {
                "type": json_type,
                "data": chunk_data
            }
            
            # 生成输出文件名：原始文件名_序号.json
            # 例如：data.json -> data_001.json, data_002.json
            chunk_num = i + 1
            if num_chunks <= 99:
                format_str = f"{input_name}_{chunk_num:02d}{input_ext}"
            elif num_chunks <= 999:
                format_str = f"{input_name}_{chunk_num:03d}{input_ext}"
            else:
                format_str = f"{input_name}_{chunk_num:04d}{input_ext}"
            
            output_file = os.path.join(input_dir, format_str)
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_json, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 已创建: {format_str}，包含 {len(chunk_data)} 条数据")
        
        print(f"\n✅ 拆分完成！共生成 {num_chunks} 个文件")
        
        # 显示生成的文件列表
        print("\n生成的文件列表:")
        for i in range(num_chunks):
            chunk_num = i + 1
            if num_chunks <= 99:
                filename = f"{input_name}_{chunk_num:02d}{input_ext}"
            elif num_chunks <= 999:
                filename = f"{input_name}_{chunk_num:03d}{input_ext}"
            else:
                filename = f"{input_name}_{chunk_num:04d}{input_ext}"
            print(f"  - {filename}")
        
        return True
        
    except json.JSONDecodeError:
        print("错误: 输入的JSON文件格式不正确")
        return False
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

def main():
    """
    命令行入口函数
    支持以下用法:
      python split.py data.json
      python split.py data.json 50000
    """
    
    # 检查命令行参数
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print("""
JSON文件拆分工具 v1.0
====================

功能:
  将大型JSON文件按指定条数拆分为多个小文件，保存到原始文件同一目录下

使用方法:
  python split.py 输入文件.json [每条数据数]

参数说明:
  输入文件.json  - 要拆分的JSON文件 (必需)
  每条数据数     - 每个小文件包含的数据条数 (可选，默认: 60000)

示例:
  python split.py data.json          # 每条60000条数据拆分
  python split.py data.json 50000    # 每条50000条数据拆分
  python split.py data.json 100000   # 每条100000条数据拆分

输出文件命名:
  data.json -> data_01.json, data_02.json, data_03.json ...
        """)
        sys.exit(1)
    
    # 获取输入文件路径
    input_file = sys.argv[1]
    
    # 获取chunk_size参数（默认为60000）
    chunk_size = 4500  # 默认值
    if len(sys.argv) >= 3:
        try:
            chunk_size = int(sys.argv[2])
            if chunk_size <= 0:
                print("错误: 每条数据数必须大于0")
                sys.exit(1)
        except ValueError:
            print("错误: 每条数据数必须是整数")
            sys.exit(1)
    
    # 执行拆分操作
    success = split_json_file(input_file, chunk_size)
    
    # 根据执行结果返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()