#!/usr/bin/env python3
"""
Streamlit Community Cloud 部署入口
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

# 导入主应用
from dashboard_visual import main

if __name__ == "__main__":
    main()