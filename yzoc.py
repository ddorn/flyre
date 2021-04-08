import sys
from pathlib import Path

SRC = str((Path(__file__).parent / "src").absolute())
sys.path.append(SRC)

from constants import SIZE
from engine import App, IntegerScaleScreen
from states.loading import LoadingState

if __name__ == "__main__":
    App(LoadingState, IntegerScaleScreen(SIZE)).run()
