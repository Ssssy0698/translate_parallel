#!/usr/bin/env python3
"""
JSON文件对比工具
对比两个JSON文件，提取藏语字段相同的条目（取第一个文件的结果），
并将各自独有的条目合并为一个新文件
"""

import json
import os
import sys
from datetime import datetime

def compare_and_merge_json(file1_path, file2_path, output_file=None):
    """
    对比两个JSON文件，提取藏语字段相同和不同的条目
    
    Args:
        file1_path: 第一个JSON文件路径
        file2_path: 第二个JSON文件路径
        output_file: 输出文件路径（可选）
    
    Returns:
        bool: 是否成功
    """
    
    try:
        # 读取第一个JSON文件
        print(f"正在读取第一个文件: {file1_path}")
        with open(file1_path, 'r', encoding='utf-8') as f:
            data1 = json.load(f)
        
        # 读取第二个JSON文件
        print(f"正在读取第二个文件: {file2_path}")
        with open(file2_path, 'r', encoding='utf-8') as f:
            data2 = json.load(f)
        
        # 提取条目
        entries1 = data1.get("entries", [])
        entries2 = data2.get("entries", [])
        
        print(f"第一个文件条目数: {len(entries1)}")
        print(f"第二个文件条目数: {len(entries2)}")
        
        # 创建藏语字段到条目的映射
        tibetan_to_entry1 = {}
        tibetan_to_entry2 = {}
        
        # 用于去重，存储已经处理过的藏语文本
        processed_tibetan1 = set()
        processed_tibetan2 = set()
        
        # 处理第一个文件
        for entry in entries1:
            tibetan = entry.get("tibetan", "").strip()
            if tibetan and tibetan not in processed_tibetan1:
                tibetan_to_entry1[tibetan] = entry
                processed_tibetan1.add(tibetan)
        
        # 处理第二个文件
        for entry in entries2:
            tibetan = entry.get("tibetan", "").strip()
            if tibetan and tibetan not in processed_tibetan2:
                tibetan_to_entry2[tibetan] = entry
                processed_tibetan2.add(tibetan)
        
        print(f"第一个文件有效藏语条目数（去重后）: {len(tibetan_to_entry1)}")
        print(f"第二个文件有效藏语条目数（去重后）: {len(tibetan_to_entry2)}")
        
        # 找出相同和不同的藏语条目
        common_tibetan = set(tibetan_to_entry1.keys()) & set(tibetan_to_entry2.keys())
        only_in_file1 = set(tibetan_to_entry1.keys()) - set(tibetan_to_entry2.keys())
        only_in_file2 = set(tibetan_to_entry2.keys()) - set(tibetan_to_entry1.keys())
        
        print(f"两个文件共同的藏语条目数: {len(common_tibetan)}")
        print(f"第一个文件独有的藏语条目数: {len(only_in_file1)}")
        print(f"第二个文件独有的藏语条目数: {len(only_in_file2)}")
        
        # 构建合并的条目列表
        merged_entries = []
        
        # 1. 添加共同条目（使用第一个文件的数据）
        for tibetan in common_tibetan:
            entry = tibetan_to_entry1[tibetan].copy()
            if "id" in entry:
                del entry["id"]
            merged_entries.append(entry)
        
        # 2. 添加第一个文件独有的条目
        for tibetan in only_in_file1:
            entry = tibetan_to_entry1[tibetan].copy()
            if "id" in entry:
                del entry["id"]
            merged_entries.append(entry)
        
        # 3. 添加第二个文件独有的条目
        for tibetan in only_in_file2:
            entry = tibetan_to_entry2[tibetan].copy()
            if "id" in entry:
                del entry["id"]
            merged_entries.append(entry)
        
        # 重新编号
        for i, entry in enumerate(merged_entries, 1):
            entry["id"] = i
        
        # 获取leixing（使用第一个文件的leixing）
        leixing = data1.get("leixing", "对比结果")
        
        # 创建合并后的数据结构
        merged_data = {
            "leixing": leixing,
            "entries": merged_entries,
            "统计信息": {
                "总条数": len(merged_entries),
                "最后更新": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        # 生成输出文件名
        if output_file is None:
            file1_name = os.path.basename(file1_path)
            file2_name = os.path.basename(file2_path)
            file1_base = os.path.splitext(file1_name)[0]
            file2_base = os.path.splitext(file2_name)[0]
            output_file = f"对比合并结果_{file1_base}_与_{file2_base}.json"
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 对比完成！")
        print(f"输出文件: {output_file}")
        print(f"总条数: {len(merged_entries)}")
        print(f"共同条数: {len(common_tibetan)}")
        print(f"文件1独有条数: {len(only_in_file1)}")
        print(f"文件2独有条数: {len(only_in_file2)}")
        print(f"文件大小: {os.path.getsize(output_file) / 1024:.2f} KB")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ 文件不存在: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

def main():
    """
    命令行入口函数
    
    用法:
      python compare_json.py file1.json file2.json
      python compare_json.py file1.json file2.json --output 自定义文件名.json
    """
    
    if len(sys.argv) < 3 or sys.argv[1] in ['-h', '--help']:
        print("""
JSON文件对比工具
================

功能:
  对比两个JSON文件，提取藏语字段相同的条目（取第一个文件的结果），
  并将各自独有的条目合并为一个新文件

使用方法:
  python compare_json.py 文件1.json 文件2.json [选项]

参数说明:
  文件1.json, 文件2.json - 要对比的两个JSON文件
  --output, -o           - 指定输出文件名
  --help, -h             - 显示帮助信息

示例:
  python compare_json.py oral_kham_001.json oral_kham_002.json
  python compare_json.py file1.json file2.json -o 合并结果.json

文件格式要求:
  {
    "leixing": "类型",
    "entries": [
      {
        "id": 1,
        "tibetan": "藏语文本",
        "chinese": "中文翻译"
      },
      ...
    ],
    "统计信息": {
      "总条数": 数字,
      "最后更新": "日期时间"
    }
  }

注意:
  - 提取两个文件中所有条目
  - 共同条目使用第一个文件的数据
  - 输出文件结构与原始JSON相同
  - 输出文件保存在当前目录
        """)
        sys.exit(1)
    
    # 解析命令行参数
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output_file = None
    
    # 解析可选参数
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] in ['--output', '-o']:
            if i + 1 < len(sys.argv):
                output_file = sys.argv[i + 1]
                i += 2
            else:
                print("❌ 错误: --output 参数需要指定文件名")
                sys.exit(1)
        elif sys.argv[i] in ['-h', '--help']:
            # 帮助信息已经在上面显示了
            sys.exit(0)
        else:
            print(f"❌ 错误: 未知参数: {sys.argv[i]}")
            print("使用 python compare_json.py -h 查看帮助")
            sys.exit(1)
    
    # 检查文件是否存在
    if not os.path.exists(file1):
        print(f"❌ 错误: 文件不存在 - {file1}")
        sys.exit(1)
    
    if not os.path.exists(file2):
        print(f"❌ 错误: 文件不存在 - {file2}")
        sys.exit(1)
    
    # 对比并合并文件
    success = compare_and_merge_json(file1, file2, output_file)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()