import sys
import os
from pathlib import Path

# Add project root to sys.path so that src modules can be imported
# This assumes conftest.py is in the tests/ directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
