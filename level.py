from random import uniform
from typing import Tuple, Type, Union

from constants import WORLD
from engine.utils import prop_in_rect
from objects.enemies import *

__all__ = ["LEVELS"]


class Level:
    def __init__(self, state):
        self.state = state
        self.skip = False

    def spawn(self, enemy: Type[Enemy], pos: Union[int, Tuple, None] = None, *args):
        positions = [
            (-0.1, 0.2),  # -2, left side
            (0.2, -0.2),  # -1, left up
            (0.5, -0.2),  # 0, up
            (0.8, -0.2),  # 1, right up
            (1.1, 0.2),  # 2, right side
        ]

        if pos is None:
            pos = self.random_at_top()
        elif isinstance(pos, int):
            pos = positions[pos + 2]
            pos = prop_in_rect(WORLD, *pos)

        return self.state.add(enemy(pos, *args))

    def any_alive(self):
        return any(e.alive for e in self.state.get_all(Enemy))

    def wait_until_dead(self, *enemies):
        if len(enemies) == 0:
            yield  # Enemies may have not been added to the state yet.
            while self.any_alive() and not self.skip:
                yield
        else:
            while any(e.alive for e in enemies) and not self.skip:
                yield

    def random_at_top(self):
        return uniform(0, WORLD.right), -40

    def wait(self, seconds):
        for _ in range(int(seconds * 60)):
            if not self.skip:
                yield

    def script(self):
        yield


class Level1(Level):
    def script(self):
        self.spawn(BomberEnemy)
        yield from self.wait_until_dead()
        self.spawn(Enemy, -1)
        self.spawn(Enemy, 1)
        yield from self.wait_until_dead()

        self.spawn(Enemy, -2)
        self.spawn(Enemy, 0)
        self.spawn(Enemy, 2)


class Level2(Level):
    def script(self):
        self.spawn(Enemy, -2)
        self.spawn(LaserEnemy, 0)
        self.spawn(Enemy, 2)

        yield from self.wait(5)

        self.spawn(Enemy, -1)
        self.spawn(Enemy, 1)

        yield from self.wait(3)

        self.spawn(LaserEnemy, -2)
        self.spawn(LaserEnemy, 2)


class Level3(Level):
    def script(self):
        for i in range(10):

            if i % 2 == 0:
                self.spawn(Enemy)
            else:
                self.spawn(LaserEnemy)

            yield from self.wait(5 - i / 2)
        yield from self.wait(8)

        self.spawn(Enemy, -1)
        self.spawn(Enemy, 1)
        self.spawn(LaserEnemy, -2)
        self.spawn(LaserEnemy, 2)


class Level4(Level):
    def script(self):

        self.spawn(ChargeEnemy, 1)
        yield from self.wait(4)
        for i in range(-2, 3):
            self.spawn(ChargeEnemy, i)

        yield from self.wait(10)

        for i in range(10):
            self.spawn(ChargeEnemy)
            self.spawn(LaserEnemy)
            yield from self.wait(5 - i / 2)


LEVELS = Level.__subclasses__()
# LEVELS = [Level4]
