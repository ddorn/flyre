from constants import *
from engine import State
from objects.other import Menu, Text


class GameOverState(State):
    def __init__(self, player):
        super().__init__()

        self.player = player
        r = self.add(Text("GAME OVER", RED, 64, midtop=(W / 2, 32)))

        r = self.add(
            Text(f"Score: {player.score}", YELLOW, 32, midtop=r.rect.midbottom)
        )

        self.add(Menu(r.rect.midbottom, {"Restart"}))
