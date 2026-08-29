import json
import sys
import os

def delete_empty_fields(json_file, mode='any'):
    """
    删除JSON文件中chinese或tibetan字段为空的条目，并重新编号
    
    Args:
        json_file (str): JSON文件路径
        mode (str): 删除模式
            - 'any': 任意一个字段为空就删除（默认）
            - 'both': 两个字段都为空才删除
    """
    # 检查文件是否存在
    if not os.path.exists(json_file):
        print(f"错误：文件 '{json_file}' 不存在")
        return False
    
    # 读取JSON文件
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：文件 '{json_file}' 不是有效的JSON格式 ({e})")
        return False
    except Exception as e:
        print(f"错误：读取文件 '{json_file}' 时发生错误 ({e})")
        return False
    
    # 检查数据结构
    if 'entries' not in data or not isinstance(data['entries'], list):
        print(f"错误：文件 '{json_file}' 没有找到有效的entries列表")
        return False
    
    # 备份原始数据
    original_entries = data['entries'].copy()
    original_count = len(original_entries)
    
    # 收集被删除的条目ID
    deleted_ids = []
    
    # 过滤出符合条件的条目
    filtered_entries = []
    empty_count = 0
    
    for entry in data['entries']:
        chinese = entry.get('chinese', '')
        tibetan = entry.get('tibetan', '')
        
        # 根据模式判断是否删除
        if mode == 'any':
            # 任意一个字段为空就删除
            if chinese == '' or tibetan == '':
                empty_count += 1
                deleted_ids.append(entry.get('id', 0))
                continue
        elif mode == 'both':
            # 两个字段都为空才删除
            if chinese == '' and tibetan == '':
                empty_count += 1
                deleted_ids.append(entry.get('id', 0))
                continue
        else:
            print(f"错误：未知的删除模式 '{mode}'")
            return False
        
        filtered_entries.append(entry)
    
    # 重新编号ID
    for i, entry in enumerate(filtered_entries, 1):
        entry['id'] = i
    
    # 更新数据
    data['entries'] = filtered_entries
    filtered_count = len(filtered_entries)
    
    # 如果有"统计信息"部分，更新总条数
    if '统计信息' in data and isinstance(data['统计信息'], dict):
        data['统计信息']['总条数'] = filtered_count
    
    # 保存修改后的文件
    try:
        # 创建一个备份文件
        backup_file = json_file + '.bak'
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 用备份文件替换原文件
        os.replace(backup_file, json_file)
        
        print(f"✓ 文件 '{json_file}' 处理完成")
        print(f"  原始条目数: {original_count}")
        print(f"  删除空条目: {empty_count}")
        print(f"  保留条目数: {filtered_count}")
        
        if deleted_ids:
            deleted_ids_str = ', '.join(map(str, deleted_ids[:10]))
            if len(deleted_ids) > 10:
                deleted_ids_str += f", ...(共{len(deleted_ids)}个)"
            print(f"  删除的ID: {deleted_ids_str}")
        
        # 显示新ID范围
        if filtered_entries:
            new_ids = [entry['id'] for entry in filtered_entries]
            print(f"  新ID范围: {min(new_ids)} - {max(new_ids)}")
        
        return True
    except Exception as e:
        print(f"错误：保存文件 '{json_file}' 时发生错误 ({e})")
        return False

def main():
    """
    主函数：处理命令行参数
    """
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python delete_empty.py <json文件> [删除模式]")
        print("示例: python delete_empty.py 1.json any")
        print("      支持通配符: python delete_empty.py *.json any")
        print("")
        print("删除模式:")
        print("  any  - 任意一个字段为空就删除 (默认)")
        print("  both - 两个字段都为空才删除")
        return
    
    # 获取删除模式，默认为'any'
    delete_mode = 'any'
    if len(sys.argv) > 2:
        delete_mode = sys.argv[2].lower()
        if delete_mode not in ['any', 'both']:
            print(f"警告：未知的删除模式 '{delete_mode}'，使用默认模式 'any'")
            delete_mode = 'any'
    
    # 处理所有JSON文件
    for i, arg in enumerate(sys.argv[1:], 1):
        # 跳过模式参数
        if arg in ['any', 'both']:
            continue
        
        # 检查是否是通配符模式
        if '*' in arg or '?' in arg:
            import glob
            files = glob.glob(arg)
            if not files:
                print(f"警告：没有找到匹配 '{arg}' 的文件")
                continue
            
            for file_path in files:
                if file_path.endswith('.json'):
                    print(f"处理文件 ({i}/{len(sys.argv)-1}): {file_path}")
                    delete_empty_fields(file_path, delete_mode)
                    print()  # 空行分隔
        else:
            # 单个文件
            print(f"处理文件 ({i}/{len(sys.argv)-1}): {arg}")
            delete_empty_fields(arg, delete_mode)
            if i < len(sys.argv) - 1:
                print()  # 空行分隔

if __name__ == "__main__":
    main()