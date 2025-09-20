#!/usr/bin/env python3
"""
保守的代码质量修复脚本
只修复空白行和行尾空格问题
"""

import os
import re
import glob
from pathlib import Path

def fix_file(file_path):
    """修复单个文件的代码质量问题"""
    print(f"修复文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. 移除空白行中的空格
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
    
    # 2. 移除行尾空格
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    
    # 3. 确保文件以换行符结尾
    if content and not content.endswith('\n'):
        content += '\n'
    
    # 4. 移除重复的空行（最多保留2个连续空行）
    content = re.sub(r'\n\s*\n\s*\n+', r'\n\n', content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ 已修复: {file_path}")
        return True
    else:
        print(f"  ⏭️  无需修复: {file_path}")
        return False

def main():
    """主函数"""
    print("🔧 开始保守修复代码质量问题...")
    
    # 获取所有Python文件
    python_files = []
    for pattern in ['*.py', 'tests/*.py']:
        python_files.extend(glob.glob(pattern))
    
    # 排除不需要修复的文件
    exclude_files = [
        '.venv',
        '__pycache__',
        'fix_code_quality.py',
        'fix_code_quality_conservative.py'
    ]
    
    python_files = [f for f in python_files if not any(ex in f for ex in exclude_files)]
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    fixed_count = 0
    for file_path in python_files:
        if os.path.exists(file_path):
            if fix_file(file_path):
                fixed_count += 1
    
    print(f"\n✅ 修复完成！共修复了 {fixed_count} 个文件")

if __name__ == "__main__":
    main()
