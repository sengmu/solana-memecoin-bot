#!/usr/bin/env python3
"""
Streamlit Community Cloud 部署入口
直接运行dashboard.py的内容
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

# 直接导入并运行dashboard.py的内容
import dashboard
