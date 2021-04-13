from src.engine import *
from src.objects import *
from .game import GameState
from .my_state import MyState
from .skillpickup import SkillPickUp


class MenuState(MyState):
    BG_MUSIC = "cozyFractal.oga"

    def __init__(self):
        super().__init__()

        from . import HighScoreState

        self.add(Text(GAME_NAME, ORANGE, TITLE_SIZE, midtop=(W / 2, 32)))
        self.add(
            Menu(
                (W / 2, 150),
                {
                    "Play": self.push_state_callback(GameState),
                    "Highscores": self.push_state_callback(HighScoreState),
                    # "Settings": lambda: 0,
                    "Quit": App.MAIN_APP.quit,
                },
            )
        )
