from random import choice, uniform
from random import choice, uniform
from typing import Tuple, Type, Union


from src.engine import *
from src.objects import *

__all__ = ["LEVELS"]


class Level:
    def __init__(self, state):
        self.state = state
        self.skip = False

    def spawn(
        self, enemy: Type[Enemy] = None, pos: Union[int, Tuple, None] = None, *args
    ):
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

        if enemy is None:
            enemy = self.random_enemy()

        return self.state.add(enemy(pos, *args))

    def all_enemy_types(self):
        return [
            Enemy,
            LaserEnemy,
            BomberEnemy,
            ChargeEnemy,
            lambda *args: CopyEnemy(*args, player=self.state.player),
        ]

    def random_enemy(self) -> Enemy:
        # noinspection PyTypeChecker
        return choice(self.all_enemy_types())

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
        yield  # Enemies may have not been added to the state yet.
        for _ in range(int(seconds * 60 - 1)):
            if self.any_alive() and not self.skip:
                yield

    def script(self):
        yield


class Level0(Level):
    """For demo purposes."""

    def script(self):
        for e in self.all_enemy_types():
            self.spawn(e, 0)
            yield from self.wait_until_dead()


class Level1(Level):
    """First level, "tutorial"."""

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
    """Introduces lasers"""

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
    """Introduces bomber."""

    def script(self):
        self.spawn(BomberEnemy)
        yield from self.wait(4)

        for i in range(10):

            if i % 2 == 0:
                self.spawn(Enemy)
            else:
                self.spawn(LaserEnemy)

            if i in (5, 9):
                self.spawn(BomberEnemy)

            yield from self.wait(3)
        yield from self.wait(11)

        self.spawn(Enemy, -1)
        self.spawn(Enemy, 1)
        self.spawn(LaserEnemy, -2)
        self.spawn(LaserEnemy, 2)
        self.spawn(BomberEnemy)
        self.spawn(BomberEnemy)


class Level4(Level):
    """Introducing chargers."""

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


class Level5(Level):
    """Introduces Copy"""

    def script(self):
        player = self.state.player
        self.spawn(CopyEnemy, 0, player)
        yield from self.wait_until_dead()

        self.spawn(CopyEnemy, -2, player)
        self.spawn(CopyEnemy, 2, player)
        yield from self.wait_until_dead()

        self.spawn(CopyEnemy, -2, player)
        self.spawn(Enemy, 0)
        self.spawn(Enemy, 2)

        yield from self.wait(10)

        for e in self.all_enemy_types():
            self.spawn(e)


class Level7(Level):
    """Hell breaks loose"""

    def script(self):
        player = self.state.player
        self.spawn(CopyEnemy, 0, player)
        yield from self.wait_until_dead()

        self.spawn(CopyEnemy, -2, player)
        self.spawn(CopyEnemy, 2, player)

        yield from self.wait(6)

        for i in range(10):
            self.spawn()
            self.spawn(Enemy)
            yield from self.wait(3)


class Level8(Level):
    """Hell breaks loose...r"""

    def script(self):
        player = self.state.player

        for _ in range(2):
            for e in self.all_enemy_types():
                self.spawn(e)
                self.spawn(CopyEnemy, None, player)
                yield from self.wait(4)


LEVELS = Level.__subclasses__()
# LEVELS = [Level5]
