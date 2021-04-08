from constants import *
from engine import App, State
from objects.other import Menu, Text
from states.my_state import MyState


class GameOverState(MyState):
    def __init__(self, player):
        super().__init__()

        self.player = player
        r = self.add(Text("GAME OVER", RED, 64, midtop=(W / 2, 32)))

        r = self.add(
            Text(f"Score: {player.score}", YELLOW, 32, midtop=r.rect.midbottom)
        )

        from states import GameState

        from states.menu import MenuState

        self.add(
            Menu(
                (W / 2, H - 150),
                {
                    "Restart": self.replace_state_callback(GameState),
                    "Menu": self.replace_state_callback(MenuState),
                    "Quit": App.MAIN_APP.quit,
                },
            )
        )
