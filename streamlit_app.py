"""
NagrikMitra Frontend - Streamlit Cloud Entry Point
This is the main entry point for Streamlit Cloud deployment
"""

import sys
import os

# Add parent directory to path so we can import frontend module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the streamlit app
from frontend.streamlit_app import *
