import pygame

from constants import SIZE, W, H
from engine.app import App
from engine.screen import IntegerScaleScreen
from engine.state_machine import State
from objects import Planet, Player
from engine.pygame_input import Axis, Inputs


class GameState(State):
    BG_COLOR = '#203040'
    def __init__(self):
        super().__init__()

        self.add(Planet(4, (W * 0.66, H - 20)))
        self.player = self.add(Player((100, 200)))

        self.inputs['horizontal'] = Axis([pygame.K_a, pygame.K_LEFT], [pygame.K_d, pygame.K_RIGHT])
        self.inputs['horizontal'].always_call(self.player.move_horizontally)

        self.inputs['vertical'] = Axis([pygame.K_w, pygame.K_UP], [pygame.K_s, pygame.K_DOWN])
        self.inputs['vertical'].always_call(self.player.move_vertically)



if __name__ == '__main__':
    App(GameState, IntegerScaleScreen(SIZE)).run()