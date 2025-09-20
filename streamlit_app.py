"""
Streamlit Community Cloud entry point for the Memecoin Trading Bot Dashboard
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the cloud dashboard
from dashboard_cloud import main

if __name__ == "__main__":
    main()
