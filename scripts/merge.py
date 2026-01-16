#!/usr/bin/env python3
"""
JSON文件合并工具
将多个按序号命名的JSON文件合并为一个文件，支持多种基础文件名和不同位数的序号
"""

import json
import os
import sys
import re
from datetime import datetime

def extract_file_info(filename):
    """
    从文件名中提取基础名和序号
    
    Args:
        filename: 文件名
    
    Returns:
        tuple: (基础名, 序号, 序号位数) 或 (None, None, None) 如果格式不匹配
    """
    # 匹配格式: {基础名}_{序号}_result.json
    # 支持1-6位数的序号
    pattern = r'^(.+)_(\d{1,6})_result\.json$'
    match = re.match(pattern, filename)
    
    if match:
        base_name = match.group(1)
        file_num = int(match.group(2))
        num_digits = len(match.group(2))
        return base_name, file_num, num_digits
    else:
        return None, None, None

def get_file_patterns(base_name, num, num_digits=None):
    """
    生成可能的文件名模式
    
    Args:
        base_name: 基础文件名
        num: 序号
        num_digits: 序号位数（如果为None，则尝试所有可能的位数）
    
    Returns:
        list: 可能的文件名列表
    """
    patterns = []
    
    if num_digits is not None:
        # 使用指定的位数
        patterns.append(f"{base_name}_{num:0{num_digits}d}_result.json")
    else:
        # 尝试1-6位数
        for digits in range(1, 7):
            patterns.append(f"{base_name}_{num:0{digits}d}_result.json")
    
    # 添加其他可能的格式
    patterns.append(f"{base_name}_{num}_result.json")  # 不补零
    
    return patterns

def merge_json_files_by_pattern(start_file, end_file):
    """
    根据起始文件和结束文件合并JSON文件
    
    Args:
        start_file: 起始文件名
        end_file: 结束文件名
    """
    
    # 提取起始文件信息
    start_base, start_num, start_digits = extract_file_info(start_file)
    if start_base is None:
        print(f"❌ 无法解析起始文件名格式: {start_file}")
        print("文件名应类似: oral_kham_0002_result.json 或 oral_amdo_001_result.json")
        return None
    
    # 提取结束文件信息
    end_base, end_num, end_digits = extract_file_info(end_file)
    if end_base is None:
        print(f"❌ 无法解析结束文件名格式: {end_file}")
        print("文件名应类似: oral_kham_1000_result.json 或 oral_amdo_100_result.json")
        return None
    
    # 检查基础名是否一致
    if start_base != end_base:
        print(f"❌ 基础名不一致: {start_base} vs {end_base}")
        print("起始文件和结束文件的基础名必须相同")
        return None
    
    base_name = start_base
    
    # 检查序号顺序
    if start_num > end_num:
        print(f"❌ 起始序号({start_num})不能大于结束序号({end_num})")
        return None
    
    # 确定序号位数（使用起始文件的位数）
    num_digits = start_digits
    
    # 存储合并后的条目
    merged_entries = []
    total_entries_count = 0
    removed_empty_count = 0
    actual_files_found = 0
    
    # 获取当前目录
    current_dir = os.getcwd()
    
    print(f"正在合并 {base_name} 文件...")
    print(f"序号范围: {start_num} 到 {end_num}")
    print(f"目录: {current_dir}")
    print(f"基础文件名: {base_name}")
    
    # 遍历所有序号
    for i in range(start_num, end_num + 1):
        # 生成可能的文件名
        possible_filenames = get_file_patterns(base_name, i, num_digits)
        
        file_found = False
        filename = ""
        
        for possible_filename in possible_filenames:
            filepath = os.path.join(current_dir, possible_filename)
            if os.path.exists(filepath):
                filename = possible_filename
                file_found = True
                break
        
        if not file_found:
            # 尝试不指定位数的搜索
            extra_patterns = get_file_patterns(base_name, i, None)
            for possible_filename in extra_patterns:
                filepath = os.path.join(current_dir, possible_filename)
                if os.path.exists(filepath):
                    filename = possible_filename
                    file_found = True
                    break
        
        if not file_found:
            # 显示最可能的文件名格式
            expected_filename = f"{base_name}_{i:0{num_digits}d}_result.json"
            print(f"⚠️  文件不存在: {expected_filename}，跳过")
            continue
        
        try:
            # 读取JSON文件
            filepath = os.path.join(current_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取条目
            entries = data.get("entries", [])
            
            # 过滤掉chinese为空或None的条目
            for entry in entries:
                chinese_text = entry.get("chinese", "")
                # 检查chinese字段是否为空或None或只包含空白字符
                if chinese_text and str(chinese_text).strip():
                    # 去除条目中的id，后面会重新编号
                    entry_copy = entry.copy()
                    if "id" in entry_copy:
                        del entry_copy["id"]
                    merged_entries.append(entry_copy)
                else:
                    removed_empty_count += 1
            
            total_entries_count += len(entries)
            actual_files_found += 1
            print(f"✓  已读取: {filename} ({len(entries)} 条)")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {filename} - {e}")
        except Exception as e:
            print(f"❌ 读取错误: {filename} - {e}")
    
    if not merged_entries:
        print("❌ 没有找到可合并的数据")
        return None
    
    if actual_files_found == 0:
        print(f"❌ 在序号 {start_num} 到 {end_num} 范围内没有找到任何文件")
        return None
    
    # 重新为条目编号
    for i, entry in enumerate(merged_entries, 1):
        entry["id"] = i
    
    # 获取leixing（假设所有文件类型相同）
    leixing = base_name.replace("_", " ")  # 默认值
    if actual_files_found > 0:
        # 尝试从第一个找到的文件获取leixing
        for i in range(start_num, end_num + 1):
            possible_filenames = get_file_patterns(base_name, i, num_digits)
            for possible_filename in possible_filenames:
                filepath = os.path.join(current_dir, possible_filename)
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            first_data = json.load(f)
                            leixing = first_data.get("leixing", leixing)
                    except:
                        pass
                    break
            if leixing != base_name.replace("_", " "):
                break
    
    # 创建合并后的数据结构
    merged_data = {
        "leixing": leixing,
        "entries": merged_entries,
        "统计信息": {
            "总条数": len(merged_entries),
            "原始总条数": total_entries_count,
            "已过滤空中文条数": removed_empty_count,
            "最后更新": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "合并范围": f"{start_num} - {end_num}",
            "源文件数": actual_files_found,
            "基础文件名": base_name
        }
    }
    
    return merged_data, base_name, start_num, end_num, num_digits

def save_merged_data(merged_data, base_name, start_num, end_num, num_digits):
    """
    保存合并后的数据到文件
    
    Args:
        merged_data: 合并后的数据
        base_name: 基础文件名
        start_num: 起始序号
        end_num: 结束序号
        num_digits: 序号位数
    """
    
    # 生成输出文件名
    if start_num == end_num:
        output_filename = f"{base_name}_merged_{start_num:0{num_digits}d}.json"
    else:
        output_filename = f"{base_name}_merged_{start_num:0{num_digits}d}_{end_num:0{num_digits}d}.json"
    
    output_path = os.path.join(os.getcwd(), output_filename)
    
    try:
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 合并完成！")
        print(f"输出文件: {output_filename}")
        print(f"总条数: {len(merged_data['entries'])}")
        print(f"原始总条数: {merged_data['统计信息']['原始总条数']}")
        print(f"已过滤空中文条数: {merged_data['统计信息']['已过滤空中文条数']}")
        print(f"实际合并文件数: {merged_data['统计信息']['源文件数']}")
        print(f"文件大小: {os.path.getsize(output_path) / 1024:.2f} KB")
        
        return output_path
    except Exception as e:
        print(f"❌ 保存文件时出错: {e}")
        return None

def list_available_files():
    """列出当前目录下所有可合并的JSON文件"""
    
    current_dir = os.getcwd()
    file_groups = {}
    
    # 匹配文件名格式: {基础名}_{序号}_result.json
    pattern = r'^(.+)_(\d{1,6})_result\.json$'
    
    print("当前目录下可合并的文件:")
    print("=" * 60)
    
    for filename in sorted(os.listdir(current_dir)):
        if filename.endswith('.json'):
            match = re.match(pattern, filename)
            if match:
                base_name = match.group(1)
                file_num = int(match.group(2))
                num_digits = len(match.group(2))
                
                if base_name not in file_groups:
                    file_groups[base_name] = {
                        'files': [],
                        'min_digits': num_digits,
                        'max_digits': num_digits
                    }
                
                file_groups[base_name]['files'].append((file_num, filename, num_digits))
                file_groups[base_name]['min_digits'] = min(file_groups[base_name]['min_digits'], num_digits)
                file_groups[base_name]['max_digits'] = max(file_groups[base_name]['max_digits'], num_digits)
    
    if not file_groups:
        print("未找到可合并的JSON文件")
        print("支持的格式: {基础名}_{序号}_result.json")
        print("示例: oral_kham_001_result.json, oral_amdo_100_result.json")
        return
    
    for base_name in sorted(file_groups.keys()):
        group = file_groups[base_name]
        file_list = group['files']
        file_list.sort(key=lambda x: x[0])  # 按序号排序
        
        if file_list:
            min_num = min(f[0] for f in file_list)
            max_num = max(f[0] for f in file_list)
            count = len(file_list)
            min_digits = group['min_digits']
            max_digits = group['max_digits']
            
            print(f"\n基础名: {base_name}")
            print(f"  文件数: {count}")
            print(f"  序号范围: {min_num} - {max_num}")
            print(f"  序号位数: {min_digits} - {max_digits} 位")
            
            # 显示前3个和后3个文件
            if count <= 6:
                print(f"  文件列表: {', '.join(f[1] for f in file_list)}")
            else:
                first_files = [f[1] for f in file_list[:3]]
                last_files = [f[1] for f in file_list[-3:]]
                print(f"  文件示例: {', '.join(first_files)} ... {', '.join(last_files)}")
            
            # 显示合并命令示例
            if min_digits == max_digits:
                # 所有文件位数相同
                start_file = f"{base_name}_{min_num:0{min_digits}d}_result.json"
                end_file = f"{base_name}_{max_num:0{min_digits}d}_result.json"
                print(f"  合并命令: python merge.py {start_file} {end_file}")
            else:
                # 位数不同，使用实际文件名
                start_file = file_list[0][1]
                end_file = file_list[-1][1]
                print(f"  合并命令: python merge.py {start_file} {end_file}")
    
    print("\n" + "=" * 60)

def main():
    """
    命令行入口函数
    
    支持以下用法:
      python merge.py 起始文件 结束文件
      python merge.py list
    """
    
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', '--help']:
        print("""
JSON文件合并工具 v2.1
====================

功能:
  将多个按序号命名的JSON文件合并为一个文件，自动过滤掉chinese为空的条目
  支持多种文件名格式和不同位数的序号

使用方法:
  1. 合并指定范围:
     python merge.py 起始文件 结束文件
     
  2. 查看可合并文件:
     python merge.py list

参数说明:
  起始文件 - 合并的起始文件名，如: oral_kham_002_result.json
  结束文件 - 合并的结束文件名，如: oral_kham_1000_result.json

示例:
  python merge.py oral_kham_002_result.json oral_kham_1000_result.json
  python merge.py oral_amdo_001_result.json oral_amdo_100_result.json
  python merge.py list

文件名格式支持:
  {基础名}_{序号}_result.json
  其中序号可以是1-6位数字，如:
    - oral_kham_002_result.json   (3位数)
    - oral_amdo_001_result.json   (3位数)
    - data_0001_result.json       (4位数)
    - file_1_result.json          (1位数)

注意:
  - 自动过滤掉chinese字段为空的条目
  - 输出文件保存在当前目录
  - 起始文件和结束文件的基础名必须相同
        """)
        sys.exit(1)
    
    # 处理list命令
    if sys.argv[1].lower() == 'list':
        list_available_files()
        sys.exit(0)
    
    # 检查参数数量
    if len(sys.argv) != 3:
        print("❌ 错误: 需要两个文件名参数")
        print("用法: python merge.py 起始文件 结束文件")
        print("示例: python merge.py oral_kham_002_result.json oral_kham_1000_result.json")
        print("或使用: python merge.py list 查看可合并的文件")
        sys.exit(1)
    
    start_file = sys.argv[1]
    end_file = sys.argv[2]
    
    # 检查文件是否存在
    if not os.path.exists(start_file):
        print(f"❌ 错误: 起始文件不存在 - {start_file}")
        sys.exit(1)
    
    if not os.path.exists(end_file):
        print(f"❌ 错误: 结束文件不存在 - {end_file}")
        sys.exit(1)
    
    # 合并文件
    result = merge_json_files_by_pattern(start_file, end_file)
    
    if result is None:
        sys.exit(1)
    
    merged_data, base_name, start_num, end_num, num_digits = result
    
    # 保存合并结果
    output_path = save_merged_data(merged_data, base_name, start_num, end_num, num_digits)
    
    if output_path:
        print(f"\n📁 文件已保存到: {output_path}")
    else:
        print("❌ 保存文件失败")
        sys.exit(1)

if __name__ == "__main__":
    main()