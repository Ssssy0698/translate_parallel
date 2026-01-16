#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文语句筛选脚本 - 只保留以句号结尾且不包含英文字符和阿拉伯数字的句子
使用方法: python filter.py 中文语句.txt
"""

import re
import sys
import os
from pathlib import Path

def is_valid_sentence(line):
    """
    判断是否为有效的以句号结尾且不包含英文字符和阿拉伯数字的中文语句
    """
    line = line.strip()
    if not line:
        return False
    
    # 1. 必须以中文句号结尾
    if not line.endswith('。'):
        return False
    
    # 2. 不能包含阿拉伯数字（0-9）
    if re.search(r'\d', line):
        return False
    
    # 3. 不能包含英文字符（A-Z, a-z）
    if re.search(r'[a-zA-Z]', line):
        return False
    
    # 4. 检查长度：不多于30个字符（包含标点）
    if len(line) > 30:
        return False
    
    # 5. 排除每个字都被括号包裹的句子
    if re.match(r'^(\（[^\）]{1,3}\）)+$', line):
        return False
    
    # 6. 检查是否包含过多特殊符号
    bracket_count = line.count('（') + line.count('）')
    if bracket_count > len(line) * 0.2:  # 降低到20%
        return False
    
    # 7. 检查是否包含连续的特殊字符或下划线
    if re.search(r'[_\-\=]{2,}', line):  # 降低到2个连续特殊字符
        return False
    
    # 8. 检查是否包含代码片段
    code_patterns = [
        r'create\s+table',
        r'select\s+.+\s+from',
        r'update\s+.+\s+set',
        r'insert\s+into',
        r'delete\s+from',
        r'function\s+\w+',
        r'var\s+\w+',
        r'\.\w+\s*\(',
        r'\w+\(\s*\)',  # 函数调用
    ]
    for pattern in code_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return False
    
    # 9. 必须有至少一个中文字符
    if not re.search(r'[\u4e00-\u9fff]', line):
        return False
    
    # 10. 至少要有3个中文字符
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', line)
    if len(chinese_chars) < 3:
        return False
    
    # 11. 排除括号过多的情况
    if line.count('（') > 2 or line.count('）') > 2:
        return False
    
    # 12. 排除代码注释
    if line.startswith('#') or line.startswith('//') or line.startswith('/*'):
        return False
    
    # 13. 排除以引号开头或包含过多引号的句子
    if line.startswith('"') or line.startswith("'") or line.startswith('('):
        # 检查是否整个句子都在引号或括号内
        if (line.startswith('"') and line.endswith('"。')) or \
           (line.startswith("'") and line.endswith("'。")) or \
           (line.startswith('(') and line.endswith(')。')):
            return False
    
    # 14. 排除包含连续相同符号的句子
    if re.search(r'["\']{2,}', line):  # 连续2个或以上的引号
        return False
    
    # 15. 排除包含省略号或其他奇怪标点的句子
    if re.search(r'\.{3,}|…{2,}|‧{2,}', line):  # 连续3个点或更多
        return False
    
    # 16. 只允许常用的中文标点符号
    # 允许的标点：，。：；！？、"、（）【】《》
    # 使用正则表达式检查是否只包含中文字符和允许的标点
    allowed_pattern = r'^[\u4e00-\u9fff，。：；！？、""（）【】《》]+$'
    if not re.match(allowed_pattern, line):
        # 检查是否有其他不允许的标点符号
        # 找到所有非中文字符和非允许标点的字符
        non_chinese = re.findall(r'[^\u4e00-\u9fff，。：；！？、""（）【】《》]', line)
        if non_chinese:
            # 如果有其他字符，检查是否是空格或常见的中文标点
            for char in non_chinese:
                # 如果是空格或换行符，允许
                if char in ' \t\n\r':
                    continue
                # 如果是其他字符，不允许
                return False
    
    # 17. 检查句子是否完整（不应该以数字或英文开头，但我们已经排除了英文和数字）
    # 可以添加其他完整性检查
    
    return True

def main():
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python filter.py <文件名>")
        print("示例: python filter.py 中文语句.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 文件 '{input_file}' 不存在")
        sys.exit(1)
    
    # 创建输出文件名
    input_path = Path(input_file)
    output_file = f"{input_path.stem}_filter.txt"
    
    print(f"📁 输入文件: {input_file}")
    print(f"💾 输出文件: {output_file}")
    print("⏳ 开始筛选以句号结尾且不包含英文字符和阿拉伯数字的句子...")
    print("=" * 60)
    
    total_count = 0
    filtered_count = 0
    period_count = 0  # 以句号结尾的句子计数
    has_digit_count = 0  # 包含数字的句子计数
    has_english_count = 0  # 包含英文的句子计数
    
    try:
        # 尝试UTF-8编码
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            
            for line in f_in:
                total_count += 1
                
                # 统计各种类型
                if line.strip().endswith('。'):
                    period_count += 1
                if re.search(r'\d', line):
                    has_digit_count += 1
                if re.search(r'[a-zA-Z]', line):
                    has_english_count += 1
                
                if is_valid_sentence(line):
                    f_out.write(line)
                    filtered_count += 1
                
                # 进度显示
                if total_count % 100000 == 0:
                    print(f"✓ 已处理 {total_count:,} 行，筛选出: {filtered_count:,} 条语句")
    
    except UnicodeDecodeError:
        print("检测到编码问题，尝试使用GBK编码...")
        # 重新尝试GBK编码
        total_count = 0
        period_count = 0
        has_digit_count = 0
        has_english_count = 0
        filtered_count = 0
        
        try:
            with open(input_file, 'r', encoding='gbk') as f_in, \
                 open(output_file, 'w', encoding='utf-8') as f_out:
                
                for line in f_in:
                    total_count += 1
                    
                    # 统计各种类型
                    if line.strip().endswith('。'):
                        period_count += 1
                    if re.search(r'\d', line):
                        has_digit_count += 1
                    if re.search(r'[a-zA-Z]', line):
                        has_english_count += 1
                    
                    if is_valid_sentence(line):
                        f_out.write(line)
                        filtered_count += 1
                    
                    # 进度显示
                    if total_count % 100000 == 0:
                        print(f"✓ 已处理 {total_count:,} 行，筛选出: {filtered_count:,} 条语句")
        
        except UnicodeDecodeError:
            print("错误: 无法解码文件，请检查文件编码")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ 筛选完成！")
    print(f"📊 统计信息:")
    print(f"   总行数: {total_count:,}")
    print(f"   以句号结尾的行数: {period_count:,} ({period_count/total_count*100:.1f}%)")
    print(f"   包含数字的行数: {has_digit_count:,} ({has_digit_count/total_count*100:.1f}%)")
    print(f"   包含英文的行数: {has_english_count:,} ({has_english_count/total_count*100:.1f}%)")
    print(f"   最终筛选出的语句数: {filtered_count:,} ({filtered_count/total_count*100:.1f}%)")
    
    if period_count > 0:
        print(f"   在以句号结尾的句子中的筛选比例: {filtered_count/period_count*100:.1f}%")
    
    print(f"💾 结果文件: {output_file}")
    
    # 显示结果文件的前几行
    try:
        print(f"\n📝 结果示例（前10行）:")
        with open(output_file, 'r', encoding='utf-8') as f:
            for i in range(10):
                line = f.readline()
                if not line:
                    break
                print(f"   {i+1:2d}. {line.strip()}")
    except:
        pass

if __name__ == "__main__":
    main()