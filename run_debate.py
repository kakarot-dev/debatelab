#!/usr/bin/env python3
"""
Simple runner script for the AI Debate System.

This script provides an easy way to run the debate system without needing to 
remember the module syntax.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    sys.exit(main())