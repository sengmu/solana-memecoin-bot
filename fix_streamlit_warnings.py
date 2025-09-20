#!/usr/bin/env python3
"""
修复 Streamlit 弃用警告的脚本
"""

import os
import re
from pathlib import Path

def fix_use_container_width(file_path):
    """修复文件中的 use_container_width 警告"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换 use_container_width=True 为 width='stretch'
        content = re.sub(
            r'use_container_width=True',
            "width='stretch'",
            content
        )
        
        # 替换 use_container_width=False 为 width='content'
        content = re.sub(
            r'use_container_width=False',
            "width='content'",
            content
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已修复: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("🔧 开始修复 Streamlit 弃用警告...")
    
    # 需要修复的文件列表
    files_to_fix = [
        "dashboard_cloud.py",
        "dashboard_fixed.py", 
        "dashboard_backup.py"
    ]
    
    fixed_count = 0
    total_count = len(files_to_fix)
    
    for file_name in files_to_fix:
        file_path = Path(file_name)
        if file_path.exists():
            if fix_use_container_width(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  文件不存在: {file_name}")
    
    print(f"\n🎉 修复完成! 成功修复 {fixed_count}/{total_count} 个文件")
    
    # 检查是否还有遗漏的 use_container_width
    print("\n🔍 检查是否还有遗漏的 use_container_width...")
    
    for file_name in files_to_fix:
        file_path = Path(file_name)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'use_container_width' in content:
                    print(f"⚠️  仍有遗漏: {file_name}")
                else:
                    print(f"✅ 已清理: {file_name}")

if __name__ == "__main__":
    main()
