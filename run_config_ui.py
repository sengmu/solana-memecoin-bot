#!/usr/bin/env python3
"""
启动配置界面
"""

import subprocess
import sys
import os

def main():
    """启动配置界面"""
    print("⚙️ 启动交易配置界面...")
    print("📊 配置界面将在 http://localhost:8502 打开")
    print("⏹️  按 Ctrl+C 停止配置界面")
    print("-" * 50)
    
    try:
        # 启动配置界面
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "config_ui.py",
            "--server.port", "8502",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n⏹️  配置界面已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
