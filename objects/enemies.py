from random import gauss, randrange, uniform

from pygame import Vector2

from .spaceship import SpaceShip
from constants import WORLD
from engine import App
from engine.assets import tilemap
from engine.utils import angle_towards, clamp_length
from .bullets import Bullet, Laser


__all__ = ["Enemy", "LaserEnemy", "ChargeEnemy"]


class Enemy(SpaceShip):
    SCALE = 2

    OFFSET = (-8, -9)
    SIZE = Vector2(17, 17) * SCALE

    def __init__(self, pos, kind=None):
        if kind is None:
            kind = randrange(0, 3)
        image = tilemap("spaceships", kind, 1, 32)
        super().__init__(pos, image, self.OFFSET, self.SIZE, rotation=180)
        # self.behavior = StationaryMultipleShooter(self)

    def logic(self, state):
        clamp_length(self.vel, self.MAX_SPEED)
        super().logic(state)

        angle_towards_player = -90 + (
            state.player.center - self.sprite_to_screen(self.GUN)
        ).angle_to((1, 0))
        self.rotation = angle_towards(self.rotation, angle_towards_player, 2)

    def script(self):
        while True:
            yield from self.go_to()

            state = App.current_state()
            for _ in range(3):
                self.fire(state, state.player.pos - self.pos)
                yield from range(8)

    def fire(self, state, direction):
        return state.add(Bullet(self.sprite_to_screen(self.GUN), direction, self))

    def hit(self, bullet):
        self.damage(bullet.damage)

        player = App.current_state().player
        if self.life <= 0 and bullet.owner is player:
            player.did_kill(self)

    def on_death(self, state):
        state.add(LaserEnemy((uniform(WORLD.left, WORLD.right), -30)))


class LaserEnemy(Enemy):
    GUN = (16.5, 7)
    SIZE = Vector2(22, 16) * Enemy.SCALE
    OFFSET = (-6, -11)

    def __init__(self, pos):
        super().__init__(pos, 2)

    def fire(self, state, target):
        return state.add(Laser(self, target))

    def script(self):
        state = App.current_state()

        while True:
            yield from self.go_to()
            yield from self.hover_around(gauss(5 * 60, 30))
            yield from self.slow_down_and_stop()

            bullet = self.fire(state, self.state.player)
            while bullet.alive:
                yield


class ChargeEnemy(Enemy):
    SIZE = Vector2(22, 18) * Enemy.SCALE
    OFFSET = (-6, -8)
    GUN = (16.5, 13)

    def script(self):
        yield from self.go_to()

        hover_duration = gauss(6 * 60, 60)
        yield from self.hover_around(hover_duration)
        yield from self.slow_down_and_stop()

        # Preparation
        prep_len = 60
        for t in range(prep_len):
            self.state.particles.add(self.get_charge_particle(t / prep_len))
            yield

        self.charge_to_player()

        self.alive = False
