#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
藏语批量翻译处理器 - 修复子进程调用问题
"""

import os
import sys
import json
import time
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class BatchTranslator:
    def __init__(self, max_workers=2, output_dir="results"):
        self.max_workers = max_workers
        self.output_dir = output_dir
        self.success_count = 0
        self.fail_count = 0
        
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def check_file_status(self, file_path):
        input_filename = os.path.basename(file_path)
        if '.' in input_filename:
            base_name = input_filename.rsplit('.', 1)[0]
        else:
            base_name = input_filename
        
        output_file = os.path.join(self.output_dir, f"{base_name}_result.json")
        
        if not os.path.exists(output_file):
            return (0, 0, 0)
        
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            processed_lines = len(data.get('entries', []))
            needs_retry = 0
            
            for entry in data.get('entries', []):
                if not entry.get('chinese', '').strip():
                    needs_retry += 1
            
            if '统计信息' in data:
                total_lines = data['统计信息'].get('总条数', processed_lines)
            else:
                total_lines = processed_lines
            
            return (total_lines, processed_lines, needs_retry)
            
        except Exception:
            return (0, 0, 0)
    
    def process_single_file(self, file_path, skip_processed=False):
        try:
            if skip_processed:
                total, processed, needs_retry = self.check_file_status(file_path)
                if processed > 0 and needs_retry == 0:
                    print(f"跳过已处理文件: {file_path}")
                    return True
            
            print(f"开始处理: {file_path}")
            
            # 修复：使用绝对路径调用final_translate.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            final_translate_path = os.path.join(current_dir, "final_translate.py")
            
            cmd = [sys.executable, final_translate_path, file_path]
            
            file_base = os.path.basename(file_path)
            log_file = os.path.join("logs", f"{file_base}.log")
            
            # 修复：设置正确的环境变量和工作目录
            env = os.environ.copy()
            env['PYTHONPATH'] = current_dir  # 添加当前目录到Python路径
            
            print(f"执行命令: {' '.join(cmd)}")
            print(f"工作目录: {current_dir}")
            
            with open(log_file, 'w', encoding='utf-8') as log_f:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=log_f,
                    text=True,
                    encoding='utf-8',
                    cwd=current_dir,  # 设置工作目录
                    env=env  # 传递环境变量
                )
                
                # 等待进程完成，设置超时避免卡住
                try:
                    process.wait(timeout=300)  # 5分钟超时
                except subprocess.TimeoutExpired:
                    print(f"警告: 处理超时，终止进程: {file_path}")
                    process.terminate()
                    process.wait()
                    self.fail_count += 1
                    return False
            
            # 检查结果
            if process.returncode == 0:
                print(f"成功: {file_path}")
                self.success_count += 1
                
                # 验证结果文件是否真的包含翻译
                self.verify_translation_result(file_path)
                
                return True
            else:
                print(f"失败: {file_path} (返回码: {process.returncode})")
                self.fail_count += 1
                
                # 显示日志的最后几行
                self.show_last_log_lines(log_file, 10)
                
                return False
                
        except Exception as e:
            print(f"处理错误 {file_path}: {e}")
            import traceback
            traceback.print_exc()
            self.fail_count += 1
            return False
    
    def verify_translation_result(self, file_path):
        """验证翻译结果是否有效"""
        try:
            input_filename = os.path.basename(file_path)
            if '.' in input_filename:
                base_name = input_filename.rsplit('.', 1)[0]
            else:
                base_name = input_filename
            
            output_file = os.path.join(self.output_dir, f"{base_name}_result.json")
            
            if not os.path.exists(output_file):
                print(f"警告: 结果文件不存在: {output_file}")
                return
            
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            entries = data.get('entries', [])
            if not entries:
                print(f"警告: 结果文件没有条目: {output_file}")
                return
            
            # 统计空翻译
            empty_count = sum(1 for entry in entries if not entry.get('chinese', '').strip())
            total_count = len(entries)
            
            if empty_count > 0:
                print(f"警告: 结果中有 {empty_count}/{total_count} 个空翻译")
            
        except Exception as e:
            print(f"验证结果时出错: {e}")
    
    def show_last_log_lines(self, log_file, num_lines=10):
        """显示日志文件的最后几行"""
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    last_lines = lines[-num_lines:] if len(lines) >= num_lines else lines
                    print(f"日志最后{len(last_lines)}行:")
                    for line in last_lines:
                        print(f"  {line.rstrip()}")
        except Exception as e:
            print(f"读取日志文件时出错: {e}")
    
    def process_files(self, file_paths, skip_processed=False):
        print("=" * 60)
        print("藏语批量翻译处理器")
        print(f"文件数: {len(file_paths)}")
        print(f"并行数: {self.max_workers}")
        print("=" * 60)
        
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
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_single_file, file_path, skip_processed): file_path 
                for file_path in files_to_process
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success = future.result()
                    if success:
                        print(f"完成: {file_path}")
                    else:
                        print(f"失败: {file_path}")
                except Exception as e:
                    print(f"处理文件时出错 {file_path}: {e}")
        
        total_time = time.time() - start_time
        self.print_statistics(total_time)
    
    def print_statistics(self, total_time):
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        print("\n" + "=" * 60)
        print("处理统计")
        print("=" * 60)
        print(f"成功: {self.success_count} 个文件")
        print(f"失败: {self.fail_count} 个文件")
        print(f"总计: {self.success_count + self.fail_count} 个文件")
        print(f"耗时: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        total_files = self.success_count + self.fail_count
        if total_files > 0:
            success_rate = self.success_count / total_files * 100
            print(f"成功率: {success_rate:.1f}%")
        
        stats_file = os.path.join(self.output_dir, "batch_statistics.json")
        stats = {
            "处理时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "总耗时": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "成功文件数": self.success_count,
            "失败文件数": self.fail_count,
            "总文件数": total_files
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

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
    parser = argparse.ArgumentParser(description='藏语批量翻译处理器')
    parser.add_argument('input', nargs='+', help='输入文件或目录路径')
    parser.add_argument('--workers', type=int, default=1, help='并行处理数 (默认: 1)')
    parser.add_argument('--skip', action='store_true', help='跳过已处理文件')
    parser.add_argument('--output', default='results', help='输出目录 (默认: results)')
    
    args = parser.parse_args()
    
    if args.workers > 3:
        print("警告: 并行数超过3可能有问题，自动调整为3")
        args.workers = 3
    
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
        print("错误: 没有找到藏语文件")
        print("支持格式: .txt, .json")
        return
    
    print(f"找到 {len(all_files)} 个藏语文件")
    
    translator = BatchTranslator(
        max_workers=args.workers,
        output_dir=args.output
    )
    
    translator.process_files(all_files, skip_processed=args.skip)

if __name__ == "__main__":
    main()