import sys
from pathlib import Path

# Ensure the project root is on sys.path so that the `pricing` package can be imported
sys.path.append(str(Path(__file__).resolve().parents[1]))
