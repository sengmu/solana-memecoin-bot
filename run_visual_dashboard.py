#!/usr/bin/env python3
"""
启动可视化仪表板
"""

import subprocess
import sys
import time
import threading
import os

def run_streamlit_app(script, port):
    """运行 Streamlit 应用"""
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", script,
            "--server.port", str(port),
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except Exception as e:
        print(f"❌ 启动 {script} 失败: {e}")

def main():
    """主函数"""
    print("🚀 启动 Memecoin 交易机器人可视化界面")
    print("=" * 60)
    print("📊 主仪表板: http://localhost:8501")
    print("⚙️  配置界面: http://localhost:8502")
    print("⏹️  按 Ctrl+C 停止所有服务")
    print("=" * 60)
    
    try:
        # 启动主仪表板
        print("🔄 启动主仪表板...")
        dashboard_thread = threading.Thread(
            target=run_streamlit_app,
            args=("dashboard_visual.py", 8501)
        )
        dashboard_thread.daemon = True
        dashboard_thread.start()
        
        # 等待一下再启动配置界面
        time.sleep(3)
        
        # 启动配置界面
        print("🔄 启动配置界面...")
        config_thread = threading.Thread(
            target=run_streamlit_app,
            args=("config_ui.py", 8502)
        )
        config_thread.daemon = True
        config_thread.start()
        
        # 等待用户中断
        print("\n✅ 所有服务已启动!")
        print("🌐 在浏览器中打开上述链接开始使用")
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  正在停止所有服务...")
        print("✅ 所有服务已停止")

if __name__ == "__main__":
    main()
