"""Entry point — run with: python main.py"""
import sys
import os

# Ensure the package root is in the path
sys.path.insert(0, os.path.dirname(__file__))

from po_gsd_center.main import main

if __name__ == "__main__":
    main()
