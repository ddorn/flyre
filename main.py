import pygame

from constants import SIZE, W, H
from engine.app import App
from engine.screen import IntegerScaleScreen
from engine.state_machine import State
from objects import Planet, Player
from engine.pygame_input import Axis, Button, Inputs


class GameState(State):
    BG_COLOR = "#203040"

    def __init__(self):
        super().__init__()

        self.add(Planet(4, (W * 0.66, H - 20)))
        self.player = self.add(Player((100, 200)))

        self.inputs["horizontal"] = Axis(
            [pygame.K_a, pygame.K_LEFT], [pygame.K_d, pygame.K_RIGHT]
        )
        self.inputs["horizontal"].always_call(self.player.move_horizontally)

        self.inputs["vertical"] = Axis(
            [pygame.K_w, pygame.K_UP], [pygame.K_s, pygame.K_DOWN]
        )
        self.inputs["vertical"].always_call(self.player.move_vertically)

        self.inputs["fire"] = Button(pygame.K_SPACE)
        self.inputs["fire"].on_press_repeated(lambda _: self.player.fire(self), 0.1)

        self.paused = False
        self.inputs["pause"] = Button(pygame.K_p)
        self.inputs["pause"].on_press(self.toggle_pause)

    def toggle_pause(self, *args):
        self.paused = not self.paused

    def logic(self):
        if not self.paused:
            super().logic()


if __name__ == "__main__":
    App(GameState, IntegerScaleScreen(SIZE)).run()
