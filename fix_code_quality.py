#!/usr/bin/env python3
"""
代码质量修复脚本
自动修复常见的代码质量问题
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
    
    # 4. 修复过长的行（简单处理）
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        if len(line) > 127:
            # 尝试在合适的位置换行
            if '=' in line and len(line) > 127:
                # 在赋值操作符后换行
                parts = line.split('=', 1)
                if len(parts) == 2:
                    indent = len(line) - len(line.lstrip())
                    new_line = parts[0] + '=\n' + ' ' * (indent + 4) + parts[1]
                    fixed_lines.append(new_line)
                    continue
            elif ',' in line and len(line) > 127:
                # 在逗号后换行
                parts = line.split(',')
                if len(parts) > 1:
                    indent = len(line) - len(line.lstrip())
                    new_parts = [parts[0]]
                    for part in parts[1:]:
                        new_parts.append('\n' + ' ' * (indent + 4) + part.strip())
                    fixed_lines.append(','.join(new_parts))
                    continue
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # 5. 移除未使用的导入（简单处理）
    lines = content.split('\n')
    fixed_lines = []
    imports_to_remove = [
        'import os',
        'import json', 
        'import time',
        'import asyncio',
        'import re',
        'from typing import Dict',
        'from typing import List',
        'from typing import Optional',
        'from typing import Any',
        'from datetime import timedelta',
        'from urllib.parse import quote',
        'import aiohttp',
        'import websockets',
        'from solana.rpc.types import TxOpts',
        'from models import TokenInfo',
        'from models import TradingStats',
        'import base58',
    ]
    
    for line in lines:
        should_remove = False
        for import_to_remove in imports_to_remove:
            if line.strip().startswith(import_to_remove):
                should_remove = True
                break
        if not should_remove:
            fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # 6. 修复函数定义前的空行
    content = re.sub(r'\n(\s*def\s)', r'\n\n\1', content)
    content = re.sub(r'\n(\s*class\s)', r'\n\n\1', content)
    
    # 7. 修复类定义后的空行
    content = re.sub(r'(\s*class\s[^:]+:)\n([^\n])', r'\1\n\n\2', content)
    
    # 8. 移除重复的空行
    content = re.sub(r'\n\s*\n\s*\n', r'\n\n', content)
    
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
    print("🔧 开始修复代码质量问题...")
    
    # 获取所有Python文件
    python_files = []
    for pattern in ['*.py', 'tests/*.py']:
        python_files.extend(glob.glob(pattern))
    
    # 排除不需要修复的文件
    exclude_files = [
        '.venv',
        '__pycache__',
        'fix_code_quality.py'
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
