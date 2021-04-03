from glob import glob
from random import randint, randrange, shuffle, uniform

import pygame

from constants import ANIMATIONS, SIZE, W, H
from engine import ParticleFountain, SquareParticle
from engine.app import App
from engine.screen import IntegerScaleScreen
from engine.state_machine import State
from objects import Enemy, Planet, Player
from engine.pygame_input import Axis, Button, Inputs


class GameState(State):
    BG_COLOR = "#203040"

    def __init__(self):
        super().__init__()

        self.generate_planets(6)

        self.player = self.add(Player((100, 200)))
        self.add(Enemy((20, 20)))

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

        self.particles.fountains.append(
            ParticleFountain(
                lambda: SquareParticle("white")
                .builder()
                .at((uniform(0, W), uniform(-H / 3, H)), 90)
                .velocity(0.2)
                .living(6 * 60)
                .sized(uniform(1, 3))
                .anim_blink()
                .build(),
                0.2,
            )
        )

    def generate_planets(self, nb):
        positions = []
        possibilities = list(range(Planet.TOTAL_PLANETS))
        shuffle(possibilities)

        for number in possibilities[:nb]:
            planet = Planet.random_planet(number, positions)
            if planet:
                self.add(planet)
                positions.append(planet.pos)

    def toggle_pause(self, *args):
        self.paused = not self.paused

    def logic(self):
        if not self.paused:
            super().logic()


if __name__ == "__main__":
    App(GameState, IntegerScaleScreen(SIZE)).run()
