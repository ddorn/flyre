from constants import SIZE
from engine import App, IntegerScaleScreen
from states.loading import LoadingState

if __name__ == "__main__":
    App(LoadingState, IntegerScaleScreen(SIZE)).run()
