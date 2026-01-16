import json
import os
import sys
from datetime import datetime

def process_json_files(folder_path):
    """
    处理指定文件夹下所有JSON文件：
    1. 删除每个条目的status字段
    2. 修改"统计信息"，只保留"总条数"并将"结束时间"改为"最后更新"
    
    Args:
        folder_path (str): 包含JSON文件的文件夹路径
    """
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 '{folder_path}' 不存在")
        return
    
    # 获取文件夹中所有的json文件
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    
    if not json_files:
        print(f"在文件夹 '{folder_path}' 中没有找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个JSON文件")
    
    # 处理每个JSON文件
    for json_file in json_files:
        file_path = os.path.join(folder_path, json_file)
        
        try:
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 删除每个条目的status字段
            modified = False
            
            # 情况1: 如果JSON有entries字段且是列表
            if isinstance(data, dict) and 'entries' in data and isinstance(data['entries'], list):
                for entry in data['entries']:
                    if isinstance(entry, dict) and 'status' in entry:
                        del entry['status']
                        modified = True
            
            # 情况2: 如果JSON本身就是entries列表
            elif isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and 'status' in entry:
                        del entry['status']
                        modified = True
            
            # 情况3: 如果JSON是字典但不包含entries键，但包含status键
            elif isinstance(data, dict) and 'status' in data:
                del data['status']
                modified = True
            
            # 修改"统计信息"部分
            if isinstance(data, dict) and '统计信息' in data:
                stats = data['统计信息']
                
                # 创建新的统计信息字典
                new_stats = {}
                
                # 保留总条数
                if '总条数' in stats:
                    new_stats['总条数'] = stats['总条数']
                
                # 将结束时间改为最后更新
                if '结束时间' in stats:
                    # 获取当前的结束时间值
                    end_time = stats['结束时间']
                    # 如果是空字符串，使用当前时间
                    if not end_time:
                        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_stats['最后更新'] = end_time
                elif '开始时间' in stats:
                    # 如果没有结束时间但有开始时间，使用开始时间
                    new_stats['最后更新'] = stats['开始时间']
                else:
                    # 如果都没有，使用当前时间
                    new_stats['最后更新'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 更新统计信息
                data['统计信息'] = new_stats
                modified = True
            
            # 如果有修改，保存文件
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✓ 已处理: {json_file}")
            else:
                print(f"- 跳过: {json_file} (未找到需要修改的内容)")
                
        except json.JSONDecodeError as e:
            print(f"✗ 错误: {json_file} (JSON格式错误: {e})")
        except Exception as e:
            print(f"✗ 错误: {json_file} ({e})")

def main():
    # 使用方法1: 通过命令行参数指定文件夹路径
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    # 使用方法2: 硬编码文件夹路径（取消下面一行的注释并修改路径）
    else:
        # 请将这里修改为你的文件夹路径
        folder_path = "./your_json_folder"  # 修改为你的文件夹路径
        print(f"使用默认文件夹路径: {folder_path}")
        print("提示: 你也可以通过命令行参数指定路径，如: python script.py /path/to/json/folder")
    
    # 处理JSON文件
    process_json_files(folder_path)

if __name__ == "__main__":
    main()