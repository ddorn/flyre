from random import shuffle

import pygame

from constants import SCREEN
from engine import ParticleFountain, State
from objects import Planet


class MyState(State):
    BG_RECT = SCREEN
    BG_COLORS = [pygame.Color(c) for c in ["#203040", "#481e66", "#008782", "#3f1f3c"]]
    NB_PLANETS = 6

    def __init__(self):
        super().__init__()

        self.particles.fountains.append(ParticleFountain.stars(self.BG_RECT))
        self.generate_planets(self.NB_PLANETS)

    def generate_planets(self, nb):
        positions = []
        possibilities = list(range(Planet.TOTAL_PLANETS))
        shuffle(possibilities)

        for number in possibilities[:nb]:
            planet = Planet.random_planet(number, positions, SCREEN)
            if planet:
                self.add(planet)
                positions.append(planet.pos)
