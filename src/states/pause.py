from pygame import K_p

from src.engine import *
from src.engine.pygame_input import Button
from src.objects import Menu


class PauseState(State):
    BG_COLOR = None

    def __init__(self, game_state):
        super().__init__()
        self.game_state = game_state

        self.menu = self.add(
            Menu(
                (W / 2, 150),
                {
                    "Resume": self.stop_pause,
                    "Restart": self.restart,
                    "Settings": lambda: 0,
                    "Quit": App.MAIN_APP.quit,
                },
            )
        )

    def restart(self):
        self.pop_state()
        self.game_state.__init__()

    def create_inputs(self):
        inputs = super().create_inputs()
        inputs["pause"] = Button(K_p)
        inputs["pause"].on_press(self.stop_pause)

        return inputs

    def stop_pause(self, *args):
        self.pop_state()

    def draw(self, gfx: GFX):
        self.game_state.draw(gfx)
        gfx.box(SCREEN, (0, 0, 0, 180))

        super().draw(gfx)

        surf = text("Paused", 64, YELLOW)
        gfx.blit(surf, midtop=(W / 2, 32))
