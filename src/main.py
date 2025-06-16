import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ui import main

if __name__ == "__main__":
    main()