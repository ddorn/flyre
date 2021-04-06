from pygame import K_p

from constants import H, SCREEN, W, YELLOW
from engine import App, GFX, State
from engine.assets import text
from engine.pygame_input import Button
from objects.other import Menu


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
        self.next_state = None
        self.game_state.__init__()

    def create_inputs(self):
        inputs = super().create_inputs()
        inputs["pause"] = Button(K_p)
        inputs["pause"].on_press(self.stop_pause)

        return inputs

    def stop_pause(self, *args):
        self.next_state = None

    def draw(self, gfx: GFX):
        self.game_state.draw(gfx)
        gfx.box(SCREEN, (0, 0, 0, 180))

        super().draw(gfx)

        surf = text("Paused", 64, YELLOW)
        gfx.blit(surf, midtop=(W / 2, 32))
