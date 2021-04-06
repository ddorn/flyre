from constants import ORANGE, W
from engine import App
from objects.other import Menu, Text
from states import GameState
from states.my_state import MyState


class MenuState(MyState):
    def __init__(self):
        super().__init__()

        self.add(Text("Destiny", ORANGE, 64, midtop=(W / 2, 32)))
        self.add(
            Menu(
                (W / 2, 150),
                {
                    "Play": self.play,
                    "Highscores": lambda: 0,
                    "Settings": lambda: 0,
                    "Quit": App.MAIN_APP.quit,
                },
            )
        )

    def play(self):
        self.next_state = GameState()
