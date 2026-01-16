import os
import re

def rename_files(folder_path):
    """
    批量重命名文件夹中的文件，删除文件名中的'c2t'
    """
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 检查文件名是否包含c2t
        if 'c2t' in filename and filename.endswith('.json'):
            # 创建新文件名（删除c2t）
            new_filename = filename.replace('c2t_', '').replace('_c2t', '')
            
            # 构建完整的文件路径
            old_file = os.path.join(folder_path, filename)
            new_file = os.path.join(folder_path, new_filename)
            
            # 重命名文件
            os.rename(old_file, new_file)
            print(f"重命名: {filename} -> {new_filename}")

# 使用示例
folder_path = "C:\\Users\\qinsy\\Desktop\\藏汉平行语句对\\results"  # 替换为你的文件夹路径
rename_files(folder_path)