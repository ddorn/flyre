from typing import Type

from constants import WORLD
from engine.utils import prop_in_rect
from objects.enemies import *

__all__ = ["LEVELS"]


class Level:
    def __init__(self, state):
        self.state = state

    def spawn(self, enemy: Type[Enemy], pos=0, *args):
        positions = [
            (-0.1, 0.2),  # -2, left side
            (0.2, -0.2),  # -1, left up
            (0.5, -0.2),  # 0, up
            (0.8, -0.2),  # 1, right up
            (1.1, 0.2),  # 2, right side
        ]

        pos = prop_in_rect(WORLD, *positions[pos + 2])

        return self.state.add(enemy(pos, *args))

    def any_alive(self):
        return any(e.alive for e in self.state.get_all(Enemy))

    def wait_until_dead(self, *enemies):
        if len(enemies) == 0:
            yield  # Enemies may have not been added to the state yet.
            while self.any_alive():
                yield
        else:
            while any(e.alive for e in enemies):
                yield

    def script(self):
        yield


class Level1(Level):
    def script(self):
        for _ in range(3):
            self.spawn(Enemy, -1)
            self.spawn(LaserEnemy, 1)
            yield from self.wait_until_dead()


LEVELS = [Level1] * 5
