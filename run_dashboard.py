#!/usr/bin/env python3
"""
Launcher script for the Memecoin Trading Bot Dashboard
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit dashboard."""
    print("🚀 Starting Memecoin Trading Bot Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the dashboard")
    print("-" * 50)

    try:
        # Run streamlit dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n⏹️  Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")

if __name__ == "__main__":
    main()
