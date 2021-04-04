from constants import SIZE
from engine import App, IntegerScaleScreen
from states.game import GameState

if __name__ == "__main__":
    App(GameState, IntegerScaleScreen(SIZE)).run()
