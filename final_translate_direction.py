#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
藏语文件翻译工具 - 支持双向翻译（增强版）
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime

def load_tibetan_file(file_path):
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_type = data.get('type', 'unknown')
            
            # 支持多种JSON格式
            if 'data' in data:
                sentences = data['data']
                print(f"加载JSON文件: {file_path}, 句子数: {len(sentences)} (data格式)")
                return sentences, file_type
            elif 'entries' in data:
                # 支持entries格式
                entries = data['entries']
                # 根据翻译方向提取文本
                sentences = []
                for entry in entries:
                    if 'tibetan' in entry:
                        sentences.append(entry['tibetan'])
                    elif 'chinese' in entry:
                        sentences.append(entry['chinese'])
                print(f"加载JSON文件: {file_path}, 句子数: {len(sentences)} (entries格式)")
                return sentences, file_type
            else:
                print("错误: JSON文件格式不支持")
                return None, None
            
        else:  # 处理txt文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            lines = content.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            print(f"加载文本文件: {file_path}, 行数: {len(non_empty_lines)}")
            
            return non_empty_lines, "unknown"
            
    except Exception as e:
        print(f"加载文件失败: {e}")
        return None, None

def create_json_template(file_type="unknown", translation_direction="tibetan_to_chinese"):
    """创建JSON模板 - 根据翻译方向调整"""
    template = {
        "leixing": file_type,
        "translation_direction": translation_direction,
        "entries": [],
        "统计信息": {
            "总条数": 0,
            "成功条数": 0,
            "失败条数": 0,
            "开始时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "结束时间": "",
            "总耗时": ""
        }
    }
    return template

def translate_lines(lines, template, output_file, translation_direction="tibetan_to_chinese"):
    try:
        from improved_translator_direction import ImprovedTibetanTranslator
    except ImportError as e:
        print(f"错误: 无法导入翻译器: {e}")
        return []
    
    translated_entries = []
    success_count = 0
    fail_count = 0
    
    try:
        print("初始化翻译器...")
        with ImprovedTibetanTranslator(
            headless=True, 
            translation_direction=translation_direction
        ) as translator:
            total_lines = len(lines)
            
            print(f"开始翻译 {total_lines} 行...")
            
            for i, line in enumerate(lines, 1):
                if i % 5 == 0:  # 更频繁的进度显示
                    print(f"进度: {i}/{total_lines} ({i/total_lines*100:.1f}%)")
                
                result = translator.translate_single(line, max_retries=5)  # 增加重试次数
                
                if translation_direction == "tibetan_to_chinese":
                    entry = {
                        "id": i,
                        "tibetan": line,
                        "chinese": result if result else "",
                        "status": "success" if result else "failed"
                    }
                else:  # chinese_to_tibetan
                    entry = {
                        "id": i,
                        "chinese": line,
                        "tibetan": result if result else "",
                        "status": "success" if result else "failed"
                    }
                
                translated_entries.append(entry)
                
                # 更新统计
                if result:
                    success_count += 1
                else:
                    fail_count += 1
                    print(f"警告: 第 {i} 行翻译失败")
                
                # 每5行保存一次进度
                if i % 5 == 0:
                    template["entries"] = translated_entries
                    template["统计信息"]["总条数"] = len(translated_entries)
                    template["统计信息"]["成功条数"] = success_count
                    template["统计信息"]["失败条数"] = fail_count
                    template["统计信息"]["最后更新"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(template, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"保存进度时出错: {e}")
                
                # 延迟避免请求过快
                if i < total_lines:
                    wait_time = 2.5  # 增加延迟时间
                    time.sleep(wait_time)
            
            # 获取翻译统计
            stats = translator.get_stats()
            print(f"翻译统计: 成功={stats['success']}, 失败={stats['failed']}, 重试={stats['retries']}")
            
            return translated_entries
            
    except Exception as e:
        print(f"翻译过程出错: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    parser = argparse.ArgumentParser(description='藏语文件翻译工具 - 支持双向翻译（增强版）')
    parser.add_argument('input', help='输入文件路径')
    parser.add_argument('--direction', choices=['tibetan_to_chinese', 'chinese_to_tibetan'], 
                       default='tibetan_to_chinese', 
                       help='翻译方向: tibetan_to_chinese (藏->汉, 默认) 或 chinese_to_tibetan (汉->藏)')
    parser.add_argument('--output', help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    tibetan_file = args.input
    translation_direction = args.direction
    
    if not os.path.exists(tibetan_file):
        print(f"错误: 文件不存在: {tibetan_file}")
        return False
    
    input_filename = os.path.basename(tibetan_file)
    if '.' in input_filename:
        base_name = input_filename.rsplit('.', 1)[0]
    else:
        base_name = input_filename
    
    # 设置输出文件路径
    if args.output:
        output_file = args.output
    else:
        if translation_direction == "tibetan_to_chinese":
            suffix = "_t2c_result.json"
        else:
            suffix = "_c2t_result.json"
        output_file = f"results/{base_name}{suffix}"
    
    lines, file_type = load_tibetan_file(tibetan_file)
    
    if not lines:
        print("错误: 文件加载失败")
        return False
    
    print(f"文件类型: {file_type}")
    print(f"需要翻译的行数: {len(lines)}")
    print(f"翻译方向: {translation_direction}")
    print(f"输出文件: {output_file}")
    
    start_time = time.time()
    template = create_json_template(file_type, translation_direction)
    
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print(f"初始文件已创建: {output_file}")
    except Exception as e:
        print(f"创建初始文件时出错: {e}")
    
    entries = translate_lines(lines, template, output_file, translation_direction)
    
    if not entries:
        print("错误: 没有生成任何条目")
        return False
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"翻译完成: {len(entries)} 个条目")
    
    try:
        # 计算成功/失败数量
        success_entries = [e for e in entries if e.get("status") == "success"]
        fail_entries = [e for e in entries if e.get("status") == "failed"]
        
        template["entries"] = entries
        template["统计信息"]["总条数"] = len(entries)
        template["统计信息"]["成功条数"] = len(success_entries)
        template["统计信息"]["失败条数"] = len(fail_entries)
        template["统计信息"]["结束时间"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        template["统计信息"]["总耗时"] = f"{total_time:.2f}秒"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {output_file}")
        
        # 打印详细统计
        print(f"\n翻译统计:")
        print(f"  总条目数: {len(entries)}")
        print(f"  成功数: {len(success_entries)}")
        print(f"  失败数: {len(fail_entries)}")
        print(f"  成功率: {len(success_entries)/len(entries)*100:.1f}%")
        print(f"  总耗时: {total_time:.2f}秒")
        print(f"  平均每句: {total_time/len(entries):.2f}秒")
        
        # 如果失败条目较多，显示失败的ID
        if fail_entries:
            fail_ids = [str(e['id']) for e in fail_entries]
            print(f"  失败条目ID: {', '.join(fail_ids[:10])}" + 
                  (f" 等{len(fail_entries)}个" if len(fail_entries) > 10 else ""))
        
        return True
    except Exception as e:
        print(f"保存结果时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)