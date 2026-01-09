#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
藏语批量翻译处理器 - 直接调用版本（支持高并行和双向翻译，增强版）
"""

import os
import sys
import json
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入公共函数
try:
    from final_translate_direction import (
        load_tibetan_file, 
        create_json_template
    )
    from improved_translator_direction import ImprovedTibetanTranslator
    HAS_IMPORTS = True
except ImportError as e:
    print(f"导入失败: {e}")
    HAS_IMPORTS = False

class BatchTranslatorDirect:
    """直接调用版本的批处理器 - 支持高并行和双向翻译（增强版）"""
    
    def __init__(self, max_workers=20, output_dir="results", translation_direction="tibetan_to_chinese"):
        """
        初始化批处理器
        
        Args:
            max_workers: 最大并行数（默认20）
            output_dir: 输出目录
            translation_direction: 翻译方向
                "tibetan_to_chinese": 藏语到汉语 (默认)
                "chinese_to_tibetan": 汉语到藏语
        """
        self.max_workers = min(max_workers, 30)  # 限制最大并行数，但保持默认20
        self.output_dir = output_dir
        self.translation_direction = translation_direction
        self.success_count = 0
        self.fail_count = 0
        self.total_entries = 0
        self.success_entries = 0
        self.fail_entries = 0
        
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        if not HAS_IMPORTS:
            raise ImportError("无法导入必要的模块")
        
        print(f"初始化批处理器 - 最大并行数: {self.max_workers}, 翻译方向: {self.translation_direction}")
    
    def process_single_file(self, file_path, skip_processed=False):
        """处理单个文件 - 增强版本"""
        file_start_time = time.time()
        try:
            input_filename = os.path.basename(file_path)
            if '.' in input_filename:
                base_name = input_filename.rsplit('.', 1)[0]
            else:
                base_name = input_filename
            
            # 根据翻译方向设置输出文件名
            if self.translation_direction == "tibetan_to_chinese":
                suffix = "_t2c_result.json"
            else:
                suffix = "_c2t_result.json"
            
            output_file = os.path.join(self.output_dir, f"{base_name}{suffix}")
            
            # 检查文件是否已处理
            if skip_processed and os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    processed = len(data.get('entries', []))
                    if processed > 0:
                        # 检查成功率和失败数
                        success_entries = [e for e in data.get('entries', []) 
                                         if e.get("status") == "success"]
                        success_count = len(success_entries)
                        
                        # 如果成功率高于95%，则跳过
                        if success_count / processed >= 0.95:
                            print(f"跳过已处理文件: {file_path} (已处理{processed}条，成功率{success_count/processed*100:.1f}%)")
                            return True, processed, success_count, processed - success_count
                except Exception as e:
                    print(f"检查已处理文件时出错: {e}")
            
            print(f"开始处理: {file_path}")
            
            # 步骤1: 加载文件
            lines, file_type = load_tibetan_file(file_path)
            if not lines:
                print(f"错误: 文件加载失败: {file_path}")
                self.fail_count += 1
                return False, 0, 0, 0
            
            print(f"  → 文件类型: {file_type}, 行数: {len(lines)}")
            
            # 步骤2: 创建初始模板
            template = create_json_template(file_type, self.translation_direction)
            
            # 步骤3: 执行翻译（核心）
            translated_entries = self.translate_all_lines(lines, file_type, output_file, file_path)
            
            if not translated_entries:
                print(f"错误: 没有生成翻译结果: {file_path}")
                self.fail_count += 1
                return False, 0, 0, 0
            
            # 步骤4: 保存结果
            success = self.save_results(translated_entries, template, output_file, file_path)
            
            file_end_time = time.time()
            file_time = file_end_time - file_start_time
            
            # 统计条目
            total_entries = len(translated_entries)
            success_entries_count = sum(1 for e in translated_entries if e.get("status") == "success")
            fail_entries_count = total_entries - success_entries_count
            
            if success:
                self.success_count += 1
                self.total_entries += total_entries
                self.success_entries += success_entries_count
                self.fail_entries += fail_entries_count
                
                print(f"  → 文件处理完成: {total_entries}条, "
                      f"成功: {success_entries_count}, "
                      f"失败: {fail_entries_count}, "
                      f"耗时: {file_time:.1f}秒")
                return True, total_entries, success_entries_count, fail_entries_count
            else:
                self.fail_count += 1
                return False, total_entries, success_entries_count, fail_entries_count
                
        except Exception as e:
            print(f"处理文件时出错 {file_path}: {e}")
            import traceback
            traceback.print_exc()
            self.fail_count += 1
            return False, 0, 0, 0
    
    def translate_all_lines(self, lines, file_type, output_file, file_path):
        """翻译所有行 - 增强版本"""
        translated_entries = []
        
        try:
            # 每个线程创建自己的翻译器实例，指定翻译方向
            with ImprovedTibetanTranslator(
                headless=True, 
                translation_direction=self.translation_direction
            ) as translator:
                total_lines = len(lines)
                
                print(f"  → 开始翻译 {total_lines} 行...")
                
                for i, line in enumerate(lines, 1):
                    # 每5行显示一次进度
                    if i % 5 == 0:
                        print(f"   进度: {i}/{total_lines} ({i/total_lines*100:.1f}%)")
                    
                    # 执行单句翻译
                    result = translator.translate_single(line, max_retries=5)  # 增加重试次数
                    
                    # 创建条目
                    if self.translation_direction == "tibetan_to_chinese":
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
                    
                    # 每5行保存一次进度
                    if i % 5 == 0:
                        self.save_progress(translated_entries, file_type, output_file)
                    
                    # 延迟避免请求过快
                    if i < total_lines:
                        wait_time = 2.5  # 增加延迟时间
                        time.sleep(wait_time)
                
                return translated_entries
                
        except Exception as e:
            print(f"翻译过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return translated_entries  # 返回已翻译的部分
    
    def save_progress(self, entries, file_type, output_file):
        """保存进度"""
        try:
            template = create_json_template(file_type, self.translation_direction)
            template["entries"] = entries
            
            # 计算统计信息
            total = len(entries)
            success = sum(1 for e in entries if e.get("status") == "success")
            failed = total - success
            
            template["统计信息"]["总条数"] = total
            template["统计信息"]["成功条数"] = success
            template["统计信息"]["失败条数"] = failed
            template["统计信息"]["最后更新"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 静默失败，不影响主流程
            pass
    
    def save_results(self, entries, template, output_file, file_path):
        """保存最终结果"""
        try:
            template["entries"] = entries
            
            # 计算统计信息
            total = len(entries)
            success = sum(1 for e in entries if e.get("status") == "success")
            failed = total - success
            
            template["统计信息"]["总条数"] = total
            template["统计信息"]["成功条数"] = success
            template["统计信息"]["失败条数"] = failed
            template["统计信息"]["结束时间"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            
            print(f"  → 完成: {os.path.basename(file_path)} "
                  f"(总数: {total}, 成功: {success}, 失败: {failed}, "
                  f"成功率: {success/total*100:.1f}%)")
            
            return True
        except Exception as e:
            print(f"保存结果时出错: {e}")
            return False
    
    def process_files(self, file_paths, skip_processed=False):
        """处理多个文件"""
        print("=" * 70)
        print("藏语批量翻译处理器 (直接调用版本 - 增强版)")
        print(f"文件数: {len(file_paths)}")
        print(f"并行数: {self.max_workers}")
        print(f"翻译方向: {self.translation_direction}")
        print("=" * 70)
        
        files_to_process = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"警告: 文件不存在，跳过: {file_path}")
                continue
            
            files_to_process.append(file_path)
        
        if not files_to_process:
            print("没有需要处理的文件")
            return
        
        print(f"实际处理文件: {len(files_to_process)}")
        
        start_time = time.time()
        
        # 限制并行数，避免资源耗尽
        actual_workers = min(self.max_workers, len(files_to_process))
        print(f"使用并行数: {actual_workers}")
        
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            future_to_file = {
                executor.submit(self.process_single_file, file_path, skip_processed): file_path 
                for file_path in files_to_process
            }
            
            for i, future in enumerate(as_completed(future_to_file), 1):
                file_path = future_to_file[future]
                try:
                    success, total_entries, success_entries, fail_entries = future.result()
                    if success:
                        print(f"[{i}/{len(files_to_process)}] ✓ 完成: {os.path.basename(file_path)} "
                              f"({total_entries}条, 成功: {success_entries}, 失败: {fail_entries})")
                    else:
                        print(f"[{i}/{len(files_to_process)}] ✗ 失败: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"[{i}/{len(files_to_process)}] ! 处理文件时出错 {file_path}: {e}")
        
        total_time = time.time() - start_time
        self.print_statistics(total_time)
    
    def print_statistics(self, total_time):
        """打印统计信息"""
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        print("\n" + "=" * 70)
        print("批量处理统计")
        print("=" * 70)
        print(f"成功文件: {self.success_count} 个")
        print(f"失败文件: {self.fail_count} 个")
        print(f"总计文件: {self.success_count + self.fail_count} 个")
        
        if self.total_entries > 0:
            print(f"\n条目统计:")
            print(f"  总条目数: {self.total_entries}")
            print(f"  成功条目: {self.success_entries}")
            print(f"  失败条目: {self.fail_entries}")
            print(f"  条目成功率: {self.success_entries/self.total_entries*100:.1f}%")
        
        print(f"\n时间统计:")
        print(f"  总耗时: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        total_files = self.success_count + self.fail_count
        if total_files > 0:
            success_rate = self.success_count / total_files * 100
            print(f"  文件成功率: {success_rate:.1f}%")
            
            if self.total_entries > 0:
                avg_time_per_entry = total_time / self.total_entries
                print(f"  平均每条目耗时: {avg_time_per_entry:.2f}秒")
        
        # 保存统计信息
        stats_file = os.path.join(self.output_dir, "batch_statistics_detailed.json")
        stats = {
            "处理时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "总耗时": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "总耗时秒数": total_time,
            "文件统计": {
                "成功文件数": self.success_count,
                "失败文件数": self.fail_count,
                "总文件数": total_files,
                "文件成功率": f"{success_rate:.1f}%" if total_files > 0 else "0%"
            },
            "条目统计": {
                "总条目数": self.total_entries,
                "成功条目数": self.success_entries,
                "失败条目数": self.fail_entries,
                "条目成功率": f"{self.success_entries/self.total_entries*100:.1f}%" if self.total_entries > 0 else "0%",
                "平均每条目耗时": f"{avg_time_per_entry:.2f}秒" if self.total_entries > 0 else "0秒"
            },
            "配置": {
                "并行数": self.max_workers,
                "翻译方向": self.translation_direction,
                "输出目录": self.output_dir
            }
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细统计已保存到: {stats_file}")

# 辅助函数：查找文件
def find_tibetan_files(directory, extensions=['.txt', '.json']):
    tibetan_files = []
    
    if os.path.isdir(directory):
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, filename)
                    tibetan_files.append(file_path)
    elif os.path.isfile(directory):
        tibetan_files.append(directory)
    
    return tibetan_files

def main():
    parser = argparse.ArgumentParser(description='藏语批量翻译处理器 (直接调用版本) - 支持双向翻译（增强版）')
    parser.add_argument('input', nargs='+', help='输入文件或目录路径')
    parser.add_argument('--workers', type=int, default=20, help='并行处理数 (默认: 20，最大: 50)')
    parser.add_argument('--skip', action='store_true', help='跳过已处理文件')
    parser.add_argument('--output', default='results', help='输出目录 (默认: results)')
    parser.add_argument('--direction', choices=['tibetan_to_chinese', 'chinese_to_tibetan'], 
                       default='tibetan_to_chinese', 
                       help='翻译方向: tibetan_to_chinese (藏->汉, 默认) 或 chinese_to_tibetan (汉->藏)')
    
    args = parser.parse_args()
    
    # ========== 并行数限制 ==========
    MAX_WORKERS = 50  # 保持最大50，但默认20
    
    if args.workers > MAX_WORKERS:
        print(f"警告: 并行数超过 {MAX_WORKERS}，自动调整为 {MAX_WORKERS}")
        args.workers = MAX_WORKERS
    
    # 显示警告但不阻止
    if args.workers > 10:
        print(f"\n⚠️ 注意: 使用高并行数 {args.workers}")
        print("建议:")
        print(f"1. 高并行数可能导致资源竞争")
        print(f"2. 如果频繁失败，请降低并行数")
        print(f"3. 建议使用 --skip 参数跳过已处理文件")
        print()
    
    all_files = []
    for input_path in args.input:
        if os.path.isdir(input_path):
            files = find_tibetan_files(input_path)
            all_files.extend(files)
        elif os.path.isfile(input_path):
            all_files.append(input_path)
        else:
            print(f"警告: 路径不存在 {input_path}")
    
    if not all_files:
        print("错误: 没有找到文件")
        print("支持格式: .txt, .json")
        return
    
    print(f"找到 {len(all_files)} 个文件")
    
    # 显示前几个文件
    if len(all_files) <= 10:
        print(f"文件列表: {', '.join([os.path.basename(f) for f in all_files])}")
    else:
        print(f"文件列表: {', '.join([os.path.basename(f) for f in all_files[:5]])} 等 {len(all_files)} 个文件")
    
    translator = BatchTranslatorDirect(
        max_workers=args.workers,
        output_dir=args.output,
        translation_direction=args.direction
    )
    
    translator.process_files(all_files, skip_processed=args.skip)

if __name__ == "__main__":
    main()