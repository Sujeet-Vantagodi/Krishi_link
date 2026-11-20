"""
KrishiLink Agricultural Logistics Platform - Live Terminal Database Viewer
Convenience entry point from the project root.
Usage:
    python view_db.py
    python view_db.py users
    python view_db.py farmers
    python view_db.py buyers
    python view_db.py drivers
    python view_db.py trips
    python view_db.py orders
    python view_db.py hubs
    python view_db.py --watch
"""

import os
import sys

# Ensure root directory is on Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database.view_db import main

if __name__ == "__main__":
    main()
