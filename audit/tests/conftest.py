"""
Pytest configuration for audit tests.

Sets up Python path to include auzoom source.
"""

import sys
from pathlib import Path

# Add auzoom source to Python path
auzoom_src = Path(__file__).parent.parent.parent / "auzoom" / "src"
if str(auzoom_src) not in sys.path:
    sys.path.insert(0, str(auzoom_src))

# Add orchestrator source to Python path
orchestrator_src = Path(__file__).parent.parent.parent / "orchestrator" / "src"
if str(orchestrator_src) not in sys.path:
    sys.path.insert(0, str(orchestrator_src))
