#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
藏语文件翻译工具
"""

import json
import os
import sys
import time
from datetime import datetime

def load_tibetan_file(file_path):
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_type = data.get('type', 'unknown')
            
            if 'data' not in data:
                print("错误: JSON文件中缺少'data'字段")
                return None, None
            
            sentences = data['data']
            print(f"加载JSON文件: {file_path}, 句子数: {len(sentences)}")
            return sentences, file_type
            
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            lines = content.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            print(f"加载文本文件: {file_path}, 行数: {len(non_empty_lines)}")
            
            return non_empty_lines, "unknown"
            
    except Exception as e:
        print(f"加载文件失败: {e}")
        return None, None

def create_json_template(file_type="unknown"):
    template = {
        "leixing": file_type,
        "entries": [],
        "统计信息": {
            "总条数": 0,
            "最后更新": "2025-12-29"
        }
    }
    return template

def translate_lines(lines, template, output_file):
    try:
        from improved_translator import ImprovedTibetanTranslator as TibetanTranslator
    except ImportError:
        print("错误: 无法导入翻译器")
        try:
            from translate import TibetanTranslator
        except ImportError:
            print("错误: 无法导入任何翻译器")
            return []
    
    translated_entries = []
    
    try:
        print("初始化翻译器...")
        with TibetanTranslator(headless=True) as translator:
            total_lines = len(lines)
            
            print(f"开始翻译 {total_lines} 行...")
            
            for i, line in enumerate(lines, 1):
                if i % 10 == 0:
                    print(f"进度: {i}/{total_lines} ({i/total_lines*100:.1f}%)")
                
                result = translator.translate_single(line, max_retries=3)
                
                entry = {
                    "id": i,
                    "tibetan": line,
                    "chinese": result if result else ""
                }
                translated_entries.append(entry)
                
                template["entries"] = translated_entries
                template["统计信息"]["总条数"] = len(translated_entries)
                template["统计信息"]["最后更新"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(template, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                
                if i < total_lines:
                    time.sleep(2)
            
            return translated_entries
            
    except Exception as e:
        print(f"翻译过程出错: {e}")
        return []

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            print("用法: python final_translate.py <文件路径>")
            return True
        
        tibetan_file = sys.argv[1]
    else:
        tibetan_file = "tibetan/1.txt"
    
    if not os.path.exists(tibetan_file):
        print(f"错误: 文件不存在: {tibetan_file}")
        return False
    
    input_filename = os.path.basename(tibetan_file)
    if '.' in input_filename:
        base_name = input_filename.rsplit('.', 1)[0]
    else:
        base_name = input_filename
    
    output_filename = f"{base_name}_result.json"
    output_file = f"results/{output_filename}"
    
    lines, file_type = load_tibetan_file(tibetan_file)
    
    if not lines:
        print("错误: 文件加载失败")
        return False
    
    print(f"文件类型: {file_type}")
    print(f"需要翻译的行数: {len(lines)}")
    
    template = create_json_template(file_type)
    
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print(f"初始文件已创建: {output_file}")
    except Exception:
        pass
    
    entries = translate_lines(lines, template, output_file)
    
    if not entries:
        print("错误: 没有生成任何条目")
        return False
    
    print(f"翻译完成: {len(entries)} 个条目")
    
    try:
        template["entries"] = entries
        template["统计信息"]["总条数"] = len(entries)
        template["统计信息"]["最后更新"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {output_file}")
        
        success_count = sum(1 for entry in entries if entry.get("chinese", "").strip())
        print(f"成功翻译: {success_count}/{len(entries)}")
        
        return True
    except Exception as e:
        print(f"保存结果时出错: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)