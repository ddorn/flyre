from constants import SIZE
from engine import App, IntegerScaleScreen
from states.menu import MenuState

if __name__ == "__main__":
    App(MenuState, IntegerScaleScreen(SIZE)).run()
