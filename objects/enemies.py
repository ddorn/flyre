from random import gauss, randrange, uniform

from pygame import Vector2

from .spaceship import SpaceShip
from constants import WORLD
from engine import App
from engine.assets import tilemap
from engine.utils import (
    angle_towards,
    clamp_length,
    random_in_rect,
    random_in_rect_and_avoid,
)
from .bullets import Bomb, Bullet, Laser


__all__ = ["Enemy", "LaserEnemy", "ChargeEnemy", "CopyEnemy", "BomberEnemy"]


class Enemy(SpaceShip):
    SCALE = 2
    INVICIBILITY_DURATION = 5

    OFFSET = (-8, -9)
    SIZE = Vector2(17, 17) * SCALE

    def __init__(self, pos, kind=0):
        image = tilemap("spaceships", kind, 1, 32)
        super().__init__(pos, image, self.OFFSET, self.SIZE, rotation=180)
        # self.behavior = StationaryMultipleShooter(self)

    def logic(self, state):
        clamp_length(self.vel, self.max_speed)
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
        super().hit(bullet)

        player = App.current_state().player
        if self.life <= 0 and bullet.owner is player:
            player.did_kill(self)


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
            yield from self.go_straight_to()
            yield from self.hover_around(gauss(2 * 60, 20))
            yield from self.slow_down_and_stop()

            bullet = self.fire(state, self.state.player)
            bullet.wait_until_dead()


class ChargeEnemy(Enemy):
    SIZE = Vector2(22, 18) * Enemy.SCALE
    OFFSET = (-6, -8)
    GUN = (16.5, 13)
    CONTACT_DAMAGE = 400

    def __init__(self, pos):
        super().__init__(pos, 1)

    def script(self):
        yield from self.go_to()

        hover_duration = gauss(0 * 60, 30)
        yield from self.hover_around(hover_duration)
        yield from self.slow_down_and_stop()

        # Preparation
        prep_len = 60
        for t in range(prep_len):
            self.state.particles.add(self.get_charge_particle(t / prep_len))
            yield

        yield from self.charge_to_player()

        self.alive = False


class CopyEnemy(Enemy):
    SCALE = 2
    MAX_THRUST = 0.5

    SIZE = Vector2(17, 13) * SCALE
    OFFSET = Vector2(-7, -11)
    JET1 = Vector2(14, 22)
    JET2 = Vector2(15, 22)
    GUN = Vector2(15, 5)
    GUN_LEFT = Vector2(11, 11)
    GUN_RIGHT = Vector2(19, 11)
    GUN_FAR_LEFT = Vector2(8, 14)
    GUN_FAR_RIGHT = Vector2(22, 14)

    def __init__(self, pos, player):
        super().__init__(pos, 3)

        self.player = player

    # TODO: particle + same bullets as the player

    def script(self):
        yield from self.go_straight_to()
        while True:
            yield from self.hover_around(1000)


class BomberEnemy(Enemy):
    SIZE = Vector2(22, 22) * Enemy.SCALE
    OFFSET = (-5, -5)

    def __init__(self, pos):
        super().__init__(pos, 4)

    def fire(self, state, direction=None):
        state.add(Bomb(self.center, self, self.bullet_damage))

    def script(self):
        while True:

            pos = random_in_rect_and_avoid(
                WORLD.inflate(-60, -60),
                [o.center for o in self.state.get_all(SpaceShip, Bomb)],
                80,
            )
            yield from self.go_straight_to(pos)
            yield from self.slow_down_and_stop()
            self.fire(self.state)
