"""Streamlit entry shim — always boots VibePilot.

If Streamlit Cloud main file is set to `app.py` (repo root) instead of
`vibepilot/app.py`, this forwards to the real app instead of loading the
heavy discovery-engine stack (which can OOM on free tier).
"""

import runpy
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_VP = _ROOT / "vibepilot"
sys.path.insert(0, str(_VP))
runpy.run_path(str(_VP / "app.py"), run_name="__main__")
