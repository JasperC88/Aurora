#!/usr/bin/env python3
"""
Project Aurora - Tactical Radar Launcher
Usage:
    python3 run_tactical_server.py [--port 8050] [--no-open]
"""

import sys
import os

# Add src to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(root_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from aurora.visualization.tactical_server import main

if __name__ == "__main__":
    main()
