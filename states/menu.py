from constants import ORANGE, W
from engine import App
from objects.other import Menu, Text
from objects.player import Player
from states import GameState
from states.my_state import MyState
from states.skillpickup import SkillPickUp


class MenuState(MyState):
    BG_MUSIC = "cozyFractal.mp3"

    def __init__(self):
        super().__init__()

        self.add(Text("Kuglo", ORANGE, 64, midtop=(W / 2, 32)))
        self.add(
            Menu(
                (W / 2, 150),
                {
                    "Play": self.push_state_callback(GameState),
                    "Highscores": self.push_state_callback(SkillPickUp, Player((0, 0))),
                    "Settings": lambda: 0,
                    "Quit": App.MAIN_APP.quit,
                },
            )
        )
