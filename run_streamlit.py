#!/usr/bin/env python3
"""
Simple script to launch the DebateLab Streamlit application.

Usage:
    python run_streamlit.py
    
Or directly:
    streamlit run src/debate_app.py
    streamlit run streamlit_app.py
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Streamlit app."""
    
    # Check if we're in the right directory
    if not Path("src/debate_app.py").exists():
        print("❌ Error: src/debate_app.py not found!")
        print("Please run this script from the project root directory.")
        return 1
    
    # Check if streamlit is installed
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} found")
    except ImportError:
        print("❌ Error: Streamlit not installed!")
        print("Please install it with: pip install streamlit")
        return 1
    
    # Check if model file exists
    model_path = Path("models/phi-3.gguf")
    if not model_path.exists():
        print(f"⚠️  Warning: Model file not found at {model_path}")
        print("The debate system requires a GGUF model file to function.")
        print("Please ensure you have a compatible model file in the models/ directory.")
    else:
        print(f"✅ Model file found: {model_path}")
    
    print("\n🚀 Launching DebateLab Streamlit App...")
    print("The app will open in your default web browser.")
    print("Press Ctrl+C to stop the server.\n")
    
    # Launch streamlit
    try:
        # Use the simpler debate_app.py by default
        app_file = "src/debate_app.py"
        
        # Check if user wants the advanced version
        if len(sys.argv) > 1 and sys.argv[1] == "--advanced":
            app_file = "streamlit_app.py"
            print("Using advanced Streamlit interface...")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", app_file,
            "--server.headless", "false",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 DebateLab app stopped.")
        return 0
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())